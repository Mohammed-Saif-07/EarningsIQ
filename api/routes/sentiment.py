import os

import psycopg
from fastapi import APIRouter

from agents.orchestrator import run_pipeline

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/{ticker}")
def sentiment(ticker: str) -> dict:
    try:
        with psycopg.connect(os.getenv("DATABASE_URL", "postgresql://earningsiq:earningsiq@localhost:5432/earningsiq")) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ss.sentence_index, ss.sentiment_score
                    FROM sentence_sentiments ss
                    JOIN filings f ON f.id = ss.filing_id
                    WHERE f.ticker = %s
                    ORDER BY f.filed_at DESC, ss.sentence_index
                    LIMIT 200
                    """,
                    (ticker.upper(),),
                )
                rows = cur.fetchall()
                if rows:
                    timeline = [{"index": int(row[0]), "score": float(row[1])} for row in rows]
                    return {"ticker": ticker.upper(), "scores": [row["score"] for row in timeline], "timeline": timeline}
    except Exception:
        pass
    state = run_pipeline(ticker)
    return {
        "ticker": state["ticker"],
        "scores": state["sentiment_scores"],
        "timeline": [{"index": i, "score": score} for i, score in enumerate(state["sentiment_scores"])],
    }
