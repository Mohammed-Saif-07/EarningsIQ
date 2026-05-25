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

app = FastAPI(title="EarningsIQ Research Agent")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "agent": "research", "time": datetime.now(timezone.utc).isoformat()}


def research_node(state: dict) -> dict:
    state["step"] = "research"
    ticker = state.get("ticker", "AAPL")
    anomaly_count = len(state.get("anomalies", []))
    state["company_context"] = (
        f"{ticker} has {anomaly_count} flagged earnings-call language shifts. "
        "Recent context should be compared against company guidance, sector demand, and margin commentary. "
        "EarningsIQ keeps this research layer separate from the statistical anomaly score."
    )
    return state


@app.post("/run")
def run(state: dict) -> dict:
    return research_node(state)
