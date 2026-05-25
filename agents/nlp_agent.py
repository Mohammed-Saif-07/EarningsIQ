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

from stream.sentiment_processor import SentimentProcessor

app = FastAPI(title="EarningsIQ NLP Agent")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "agent": "nlp", "time": datetime.now(timezone.utc).isoformat()}


def nlp_node(state: dict) -> dict:
    state["step"] = "nlp"
    chunks = state.get("chunks", [])
    analysis = SentimentProcessor().analyze(chunks)
    state["sentiment_scores"] = [item["score"] for item in analysis["sentiments"]]
    state["sentiment_details"] = analysis["sentiments"]
    state["anomalies"] = analysis["anomalies"]
    return state


@app.post("/run")
def run(state: dict) -> dict:
    return nlp_node(state)
