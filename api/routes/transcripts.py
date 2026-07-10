import os

import psycopg
from fastapi import APIRouter

from agents.orchestrator import run_pipeline
from ingestion.transcript_parser import chunk_sentences

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.get("")
def list_transcripts() -> list[dict]:
    state = run_pipeline("AAPL")
    return [{"ticker": state["ticker"], "filing_id": state["filing_id"], "quarter": state["quarter"], "year": state["year"], "word_count": len(state["transcript_text"].split())}]


@router.get("/{ticker}")
def get_transcript(ticker: str) -> dict:
    try:
        with psycopg.connect(os.getenv("DATABASE_URL", "postgresql://earningsiq:earningsiq@localhost:5432/earningsiq")) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT accession_number, transcript_text
                    FROM filings
                    WHERE ticker = %s
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT 1
                    """,
                    (ticker.upper(),),
                )
                row = cur.fetchone()
                if row:
                    return {"ticker": ticker.upper(), "filing_id": row[0], "text": row[1], "chunks": chunk_sentences(row[1])}
    except Exception:
        pass
    state = run_pipeline(ticker)
    return {"ticker": state["ticker"], "filing_id": state["filing_id"], "text": state["transcript_text"], "chunks": chunk_sentences(state["transcript_text"])}


@router.post("/ingest/{ticker}")
def ingest_ticker(ticker: str) -> dict:
    return run_pipeline(ticker, emit_kafka=True)
