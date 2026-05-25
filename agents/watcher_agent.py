import os
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

from ingestion.edgar_client import EdgarClient

app = FastAPI(title="EarningsIQ Watcher Agent")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "agent": "watcher", "time": datetime.now(timezone.utc).isoformat()}


def watcher_node(state: dict) -> dict:
    state["step"] = "watcher"
    ticker = state.get("ticker", "AAPL").upper()
    filing = EdgarClient().latest_8k(ticker)
    state.update({
        "filing_id": filing["accession_number"],
        "ticker": ticker,
        "quarter": f"Q{filing['quarter']}",
        "year": filing["fiscal_year"],
        "transcript_text": filing["text"],
    })
    try:
        import redis
        client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        client.lpush("pending_filings", filing["accession_number"])
    except Exception:
        state["redis_queue"] = "offline"
    return state


@app.post("/run/{ticker}")
def run(ticker: str) -> dict:
    return watcher_node({"ticker": ticker, "error": None})
