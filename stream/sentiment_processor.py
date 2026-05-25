from ml.anomaly_detector import zscore_anomalies


POSITIVE = {"healthy", "improved", "accelerate", "strong", "growth", "profitable", "record", "recovery"}
NEGATIVE = {"pressured", "cautious", "longer", "costs", "risk", "decline", "uncertain", "weak"}


def lexical_finbert_fallback(sentence: str) -> dict:
    words = {word.strip(".,;:!?").lower() for word in sentence.split()}
    pos = len(words & POSITIVE)
    neg = len(words & NEGATIVE)
    raw = (pos - neg) / max(3, pos + neg + 1)
    label = "positive" if raw > 0.05 else "negative" if raw < -0.05 else "neutral"
    positive = max(0.05, min(0.9, 0.33 + max(raw, 0)))
    negative = max(0.05, min(0.9, 0.33 + max(-raw, 0)))
    neutral = max(0.05, 1.0 - positive - negative)
    total = positive + negative + neutral
    return {
        "label": label,
        "score": round(raw, 4),
        "positive_prob": round(positive / total, 4),
        "negative_prob": round(negative / total, 4),
        "neutral_prob": round(neutral / total, 4),
    }


class SentimentProcessor:
    def __init__(self) -> None:
        self._pipeline = None
        import os
        if os.getenv("USE_FINBERT", "false").lower() not in {"1", "true", "yes"}:
            return
        try:
            from transformers import pipeline
            self._pipeline = pipeline("text-classification", model="ProsusAI/finbert", tokenizer="ProsusAI/finbert", device=-1, top_k=None)
        except Exception:
            self._pipeline = None

    def score(self, sentences: list[str]) -> list[dict]:
        if self._pipeline is None:
            return [lexical_finbert_fallback(sentence) for sentence in sentences]
        results = self._pipeline(sentences, batch_size=32, truncation=True)
        scored: list[dict] = []
        for row in results:
            probs = {item["label"].lower(): float(item["score"]) for item in row}
            score = probs.get("positive", 0.0) - probs.get("negative", 0.0)
            label = max(probs, key=probs.get)
            scored.append({
                "label": label,
                "score": round(score, 4),
                "positive_prob": round(probs.get("positive", 0.0), 4),
                "negative_prob": round(probs.get("negative", 0.0), 4),
                "neutral_prob": round(probs.get("neutral", 0.0), 4),
            })
        return scored

    def analyze(self, sentences: list[str]) -> dict:
        scored = self.score(sentences)
        scores = [item["score"] for item in scored]
        return {"sentiments": scored, "anomalies": zscore_anomalies(sentences, scores)}
