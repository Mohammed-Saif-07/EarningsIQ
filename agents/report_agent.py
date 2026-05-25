import os
import re
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

from llm.groq_client import groq_chat
from llm.ollama_client import ollama_chat
from ml.price_correlator import synthetic_price_impact
from ml.signal_ranker import classify_signal, rank_signal
from ingestion.transcript_parser import infer_speaker

app = FastAPI(title="EarningsIQ Report Agent")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "agent": "report", "time": datetime.now(timezone.utc).isoformat()}


def report_node(state: dict) -> dict:
    state["step"] = "report"
    scores = state.get("sentiment_scores", [])
    mean = sum(scores) / max(1, len(scores))
    high = sum(1 for item in state.get("anomalies", []) if item.get("severity") == "high")
    price = synthetic_price_impact(state.get("ticker", "AAPL"), mean, len(state.get("anomalies", [])))
    state["price_delta_1d"] = price["price_delta_1d"]
    state["price_delta_5d"] = price["price_delta_5d"]
    score = rank_signal(len(state.get("anomalies", [])), high, mean, price["price_delta_1d"])
    signal = classify_signal(score, mean)
    quotes = [item.get("sentence_text", "") for item in state.get("anomalies", [])[:3]]
    while len(quotes) < 3:
        quotes.append((state.get("chunks") or ["No transcript chunk available."])[0])
    prompt = (
        f"Generate a 200-word EarningsIQ report for {state.get('ticker')} with SIGNAL, CONFIDENCE, KEY QUOTES, REASONING. "
        f"Suggested signal {signal}, score {score}, anomalies {state.get('anomalies')}, context {state.get('company_context', '')}."
    )
    text = groq_chat(prompt) if os.getenv("LLM_PROVIDER", "ollama").lower() == "groq" else ollama_chat(prompt)
    if "SIGNAL:" not in text:
        text = f"SIGNAL: {signal}\nCONFIDENCE: {int(max(50, min(95, score + 35)))}\nKEY QUOTES: {' | '.join(quotes)}\nREASONING: Anomaly density and sentiment movement suggest the call deserves analyst review. Price impact is simulated for local validation."
    state["signal_report"] = text
    state["signal"] = signal
    state["confidence"] = int(re.search(r"CONFIDENCE:\s*(\d+)", text).group(1)) if re.search(r"CONFIDENCE:\s*(\d+)", text) else int(max(50, min(95, score + 35)))
    persist_report_state(state, mean, score, high)
    return state


def persist_report_state(state: dict, sentiment_mean: float, signal_score: float, high_count: int) -> None:
    if os.getenv("PERSIST_TO_DB", "true").lower() not in {"1", "true", "yes"}:
        return
    try:
        import psycopg
        dsn = os.getenv("DATABASE_URL", "postgresql://earningsiq:earningsiq@localhost:5432/earningsiq")
        ticker = state.get("ticker", "AAPL").upper()
        filing_year = int(state.get("year") or datetime.now(timezone.utc).year)
        quarter_text = str(state.get("quarter") or "Q1")
        quarter = int(re.sub(r"\D", "", quarter_text) or "1")
        chunks = state.get("chunks", [])
        details = state.get("sentiment_details") or [
            {"label": "neutral", "score": score, "positive_prob": 0.0, "negative_prob": 0.0, "neutral_prob": 1.0}
            for score in state.get("sentiment_scores", [])
        ]
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM companies WHERE ticker=%s", (ticker,))
                row = cur.fetchone()
                if row is None:
                    cur.execute("INSERT INTO companies (ticker, name, sector, exchange) VALUES (%s,%s,%s,%s) RETURNING id", (ticker, f"{ticker} Inc.", "Unknown", "Unknown"))
                    company_id = cur.fetchone()[0]
                else:
                    company_id = row[0]
                accession = state.get("filing_id") or f"LOCAL-{ticker}-{filing_year}"
                cur.execute(
                    """
                    INSERT INTO filings (company_id, ticker, accession_number, quarter, fiscal_year, filed_at, transcript_text, word_count, processing_status)
                    VALUES (%s,%s,%s,%s,%s,NOW(),%s,%s,'reported')
                    ON CONFLICT (accession_number, fiscal_year) DO UPDATE
                    SET transcript_text=EXCLUDED.transcript_text, word_count=EXCLUDED.word_count, processing_status='reported', updated_at=NOW()
                    RETURNING id
                    """,
                    (company_id, ticker, accession, quarter, filing_year, state.get("transcript_text", ""), len(state.get("transcript_text", "").split())),
                )
                filing_id = cur.fetchone()[0]
                cur.execute("DELETE FROM anomaly_events WHERE filing_id=%s", (filing_id,))
                cur.execute("DELETE FROM sentence_sentiments WHERE filing_id=%s", (filing_id,))
                sentence_ids: dict[int, tuple[str, str]] = {}
                rolling: list[float] = []
                for index, sentence in enumerate(chunks):
                    detail = details[index] if index < len(details) else {"label": "neutral", "score": 0.0}
                    speaker, role = infer_speaker(sentence)
                    score = float(detail.get("score", 0.0))
                    rolling.append(score)
                    label = str(detail.get("label", "neutral")).lower()
                    if label not in {"positive", "negative", "neutral"}:
                        label = "positive" if score > 0 else "negative" if score < 0 else "neutral"
                    cur.execute(
                        """
                        INSERT INTO sentence_sentiments
                        (filing_id, filing_year, sentence_index, speaker, speaker_role, sentence_text, sentiment_label, sentiment_score, positive_prob, negative_prob, neutral_prob, rolling_avg_10)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        RETURNING id, sentiment_label
                        """,
                        (
                            filing_id, filing_year, index, speaker, role, sentence, label, score,
                            float(detail.get("positive_prob", 0.0)), float(detail.get("negative_prob", 0.0)),
                            float(detail.get("neutral_prob", 0.0)), sum(rolling[-10:]) / len(rolling[-10:]),
                        ),
                    )
                    sid, slabel = cur.fetchone()
                    sentence_ids[index] = (sid, slabel)
                for anomaly in state.get("anomalies", []):
                    index = int(anomaly.get("sentence_index", 0))
                    if index not in sentence_ids:
                        continue
                    sid, slabel = sentence_ids[index]
                    cur.execute(
                        """
                        INSERT INTO anomaly_events
                        (filing_id, filing_year, sentence_id, sentence_label, sentence_index, speaker, sentence_text, zscore, anomaly_type, severity)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (filing_id, filing_year, sid, slabel, index, "Unknown", anomaly.get("sentence_text", ""), anomaly.get("zscore", 0), anomaly.get("anomaly_type", "sentiment_reversal"), anomaly.get("severity", "medium")),
                    )
                cur.execute("DELETE FROM signal_reports WHERE filing_id=%s", (filing_id,))
                cur.execute(
                    """
                    INSERT INTO signal_reports
                    (filing_id, filing_year, ticker, signal, confidence, key_quote_1, key_quote_2, key_quote_3, reasoning, full_report_text, company_context)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (filing_id, filing_year, ticker, state.get("signal", "WATCH"), state.get("confidence", 72), *(state.get("chunks", ["", "", ""]) + ["", "", ""])[:3], "Generated by EarningsIQ live pipeline.", state.get("signal_report", ""), state.get("company_context", "")),
                )
                cur.execute("DELETE FROM signal_correlations WHERE filing_id=%s", (filing_id,))
                cur.execute(
                    """
                    INSERT INTO signal_correlations
                    (filing_id, filing_year, ticker, quarter, fiscal_year, price_delta_1d_pct, price_delta_5d_pct, sentiment_mean, sentiment_std, anomaly_count, high_severity_count)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (filing_id, filing_year, ticker, quarter, filing_year, state.get("price_delta_1d", 0.0), state.get("price_delta_5d", 0.0), sentiment_mean, 0.0, len(state.get("anomalies", [])), high_count),
                )
            conn.commit()
    except Exception as exc:
        state["persistence_error"] = str(exc)


@app.post("/run")
def run(state: dict) -> dict:
    return report_node(state)
