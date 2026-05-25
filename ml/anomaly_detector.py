import statistics


def zscore_anomalies(sentences: list[str], scores: list[float], threshold: float = 1.2) -> list[dict]:
    if not scores:
        return []
    mean = statistics.fmean(scores)
    stdev = statistics.pstdev(scores) or 1.0
    anomalies: list[dict] = []
    for index, score in enumerate(scores):
        zscore = (score - mean) / stdev
        evasive = any(term in sentences[index].lower() for term in ["cautious", "pressure", "longer", "uncertain", "risk"])
        if abs(zscore) >= threshold or (score < -0.25 and evasive):
            severity = "high" if score < -0.45 or abs(zscore) > 2 else "medium"
            anomalies.append({
                "sentence_index": index,
                "sentence_text": sentences[index],
                "zscore": round(zscore, 4),
                "anomaly_type": "sudden_negative_shift" if score < 0 else "sentiment_reversal",
                "severity": severity,
            })
    return anomalies
