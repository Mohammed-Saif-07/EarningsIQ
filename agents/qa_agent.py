from datetime import datetime, timezone

try:
    from fastapi import FastAPI
except Exception:
    class FastAPI:
        def __init__(self, *args, **kwargs):
            self.title = kwargs.get("title", "app")
        def get(self, *args, **kwargs):
            return lambda fn: fn
        def post(self, *args, **kwargs):
            return lambda fn: fn

from llm.qa_engine import answer_question

app = FastAPI(title="EarningsIQ QA Agent")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "agent": "qa", "time": datetime.now(timezone.utc).isoformat()}


def qa_node(question: str, state: dict) -> dict:
    return {
        "question": question,
        "answer": answer_question(question, state.get("chunks", []), state.get("company_context", "")),
        "ticker": state.get("ticker", ""),
    }


@app.post("/ask")
def ask(payload: dict) -> dict:
    return qa_node(payload.get("question", "What changed?"), payload.get("state", {}))
