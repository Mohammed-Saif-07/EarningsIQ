import argparse
import json

from agents.ingest_agent import ingest_node
from agents.nlp_agent import nlp_node
from agents.report_agent import report_node
from agents.research_agent import research_node
from agents.state import AgentState
from agents.watcher_agent import watcher_node


def error_handler(state: AgentState) -> AgentState:
    state["step"] = "error_handler"
    state["error"] = state.get("error") or "Unhandled agent error"
    return state


def should_research(state: AgentState) -> str:
    if state.get("error"):
        return "error_handler"
    return "research" if state.get("anomalies") else "report"


def build_graph():
    try:
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.graph import END, StateGraph
        workflow = StateGraph(AgentState)
        workflow.add_node("watcher", watcher_node)
        workflow.add_node("ingest", ingest_node)
        workflow.add_node("nlp", nlp_node)
        workflow.add_node("research", research_node)
        workflow.add_node("report", report_node)
        workflow.add_node("error_handler", error_handler)
        workflow.set_entry_point("watcher")
        workflow.add_edge("watcher", "ingest")
        workflow.add_edge("ingest", "nlp")
        workflow.add_conditional_edges("nlp", should_research, {"research": "research", "report": "report", "error_handler": "error_handler"})
        workflow.add_edge("research", "report")
        workflow.add_edge("report", END)
        workflow.add_edge("error_handler", END)
        return workflow.compile(checkpointer=MemorySaver())
    except Exception:
        return None


app = build_graph()


def run_pipeline(ticker: str = "AAPL", emit_kafka: bool = False) -> AgentState:
    state: AgentState = {
        "filing_id": "",
        "ticker": ticker.upper(),
        "quarter": "",
        "year": 2026,
        "transcript_text": "",
        "chunks": [],
        "sentiment_scores": [],
        "anomalies": [],
        "company_context": "",
        "signal_report": "",
        "signal": "",
        "confidence": 0,
        "price_delta_1d": 0.0,
        "price_delta_5d": 0.0,
        "error": None,
        "step": "start",
    }
    state["emit_kafka"] = emit_kafka
    graph = app
    if graph is not None:
        try:
            return graph.invoke(state, config={"configurable": {"thread_id": f"earningsiq-{ticker}"}})
        except Exception as exc:
            state["error"] = str(exc)
    for node in (watcher_node, ingest_node, nlp_node):
        state = node(state)
        if state.get("error"):
            return error_handler(state)
    state = research_node(state) if state.get("anomalies") else state
    return report_node(state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="AAPL")
    parser.add_argument("--emit-kafka", action="store_true", help="Publish transcript chunks to Kafka when USE_KAFKA=true.")
    args = parser.parse_args()
    print(json.dumps(run_pipeline(args.ticker, emit_kafka=args.emit_kafka), indent=2))
