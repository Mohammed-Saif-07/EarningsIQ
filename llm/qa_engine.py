import os

from llm.groq_client import groq_chat
from llm.ollama_client import ollama_chat


def answer_question(question: str, chunks: list[str], context: str = "") -> str:
    relevant = sorted(chunks, key=lambda chunk: sum(word.lower() in chunk.lower() for word in question.split()), reverse=True)[:5]
    prompt = "Answer using the EarningsIQ transcript context.\nQuestion: {q}\nContext: {c}\nChunks:\n{chunks}".format(
        q=question,
        c=context,
        chunks="\n".join(relevant),
    )
    if os.getenv("LLM_PROVIDER", "ollama").lower() == "groq":
        return groq_chat(prompt)
    return ollama_chat(prompt)
