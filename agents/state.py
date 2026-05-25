from typing import Optional, TypedDict


class AgentState(TypedDict):
    filing_id: str
    ticker: str
    quarter: str
    year: int
    transcript_text: str
    chunks: list[str]
    sentiment_scores: list[float]
    anomalies: list[dict]
    company_context: str
    signal_report: str
    price_delta_1d: float
    price_delta_5d: float
    error: Optional[str]
    step: str
    emit_kafka: bool
