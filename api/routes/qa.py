from fastapi import APIRouter
from pydantic import BaseModel

from agents.orchestrator import run_pipeline
from llm.qa_engine import answer_question

router = APIRouter(prefix="/qa", tags=["qa"])


class Question(BaseModel):
    ticker: str = "AAPL"
    question: str


@router.post("")
def ask(payload: Question) -> dict:
    state = run_pipeline(payload.ticker)
    answer = answer_question(payload.question, state.get("chunks", []), state.get("company_context", ""))
    return {"ticker": payload.ticker.upper(), "question": payload.question, "answer": answer, "anomalies": state.get("anomalies", [])}
