from datetime import datetime, timezone
import os

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

from ingestion.kafka_producer import EarningsProducer
from ingestion.transcript_parser import chunk_sentences

app = FastAPI(title="EarningsIQ Ingest Agent")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "agent": "ingest", "time": datetime.now(timezone.utc).isoformat()}


def ingest_node(state: dict) -> dict:
    state["step"] = "ingest"
    chunks = chunk_sentences(state.get("transcript_text", ""))
    state["chunks"] = chunks
    if not state.get("emit_kafka"):
        return state
    if os.getenv("USE_KAFKA", "false").lower() not in {"1", "true", "yes"}:
        return state
    producer = EarningsProducer()
    for index, sentence in enumerate(chunks):
        producer.send(state.get("filing_id", "local"), {
            "filing_id": state.get("filing_id", "local"),
            "ticker": state.get("ticker", "AAPL"),
            "sentence_index": index,
            "sentence_text": sentence,
        })
    producer.flush()
    return state


@app.post("/run")
def run(state: dict) -> dict:
    return ingest_node(state)
