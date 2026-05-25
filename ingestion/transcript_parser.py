import re


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def chunk_sentences(text: str) -> list[str]:
    cleaned = clean_text(text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", cleaned)
    return [part.strip() for part in parts if len(part.strip()) > 20]


def infer_speaker(sentence: str) -> tuple[str, str]:
    lowered = sentence.lower()
    if "chief financial officer" in lowered or "cfo" in lowered:
        return "CFO", "Finance"
    if "chief executive officer" in lowered or "ceo" in lowered:
        return "CEO", "Executive"
    return "Unknown", "Unknown"
