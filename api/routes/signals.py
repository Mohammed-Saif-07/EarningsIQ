import os

import psycopg
from fastapi import APIRouter

from agents.orchestrator import run_pipeline

router = APIRouter(prefix="/signals", tags=["signals"])


def db_rows() -> list[dict]:
    try:
        with psycopg.connect(os.getenv("DATABASE_URL", "postgresql://earningsiq:earningsiq@localhost:5432/earningsiq")) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ticker, COALESCE(signal, 'WATCH'), COALESCE(confidence, 72),
                           COALESCE(price_delta_1d_pct, 0), COALESCE(price_delta_5d_pct, 0),
                           COALESCE(total_anomalies, 0)
                    FROM v_filing_summary
                    ORDER BY filed_at DESC
                    LIMIT 20
                    """
                )
                return [
                    {
                        "ticker": row[0],
                        "signal": row[1],
                        "confidence": int(row[2]),
                        "price_delta_1d": float(row[3]),
                        "price_delta_5d": float(row[4]),
                        "anomalies": int(row[5]),
                    }
                    for row in cur.fetchall()
                ]
    except Exception:
        return []


@router.get("")
def leaderboard() -> list[dict]:
    persisted = db_rows()
    if persisted:
        return persisted
    rows = []
    for ticker in ["AAPL", "MSFT", "NVDA"]:
        state = run_pipeline(ticker)
        rows.append({
            "ticker": ticker,
            "signal": state.get("signal", "WATCH"),
            "confidence": state.get("confidence", 72),
            "price_delta_1d": state.get("price_delta_1d", 0),
            "price_delta_5d": state.get("price_delta_5d", 0),
            "anomalies": len(state.get("anomalies", [])),
        })
    return rows


@router.get("/{ticker}")
def signal(ticker: str) -> dict:
    try:
        with psycopg.connect(os.getenv("DATABASE_URL", "postgresql://earningsiq:earningsiq@localhost:5432/earningsiq")) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT sr.ticker, sr.full_report_text, sr.signal, sr.confidence,
                           COALESCE(json_agg(json_build_object(
                               'sentence_text', ae.sentence_text,
                               'zscore', ae.zscore,
                               'severity', ae.severity,
                               'anomaly_type', ae.anomaly_type
                           )) FILTER (WHERE ae.id IS NOT NULL), '[]'::json)
                    FROM signal_reports sr
                    LEFT JOIN anomaly_events ae ON ae.filing_id = sr.filing_id
                    WHERE sr.ticker = %s
                    GROUP BY sr.ticker, sr.full_report_text, sr.signal, sr.confidence, sr.generated_at
                    ORDER BY sr.generated_at DESC
                    LIMIT 1
                    """,
                    (ticker.upper(),),
                )
                row = cur.fetchone()
                if row:
                    return {"ticker": row[0], "report": row[1], "signal": row[2], "confidence": int(row[3]), "anomalies": row[4]}
    except Exception:
        pass
    state = run_pipeline(ticker)
    return {"ticker": ticker.upper(), "report": state["signal_report"], "anomalies": state["anomalies"], "signal": state.get("signal", "WATCH"), "confidence": state.get("confidence", 72)}
