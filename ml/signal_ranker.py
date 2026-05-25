def rank_signal(anomaly_count: int, high_count: int, sentiment_mean: float, price_delta_1d: float = 0.0) -> float:
    score = anomaly_count * 10.0 + high_count * 20.0 + abs(sentiment_mean) * 30.0 + abs(price_delta_1d) * 5.0
    return round(max(0.0, min(100.0, score)), 2)


def compute_signal_score(anomaly_count: int, high_severity: int, sentiment_mean: float, price_delta_1d: float = 0.0) -> float:
    """Compatibility wrapper for SQL-style signal score naming."""
    return rank_signal(anomaly_count, high_severity, sentiment_mean, price_delta_1d)


def classify_signal(score: float, sentiment_mean: float) -> str:
    if score >= 65 and sentiment_mean < -0.1:
        return "SELL"
    if score >= 65 and sentiment_mean > 0.1:
        return "BUY"
    if score >= 35:
        return "WATCH"
    return "NEUTRAL"
