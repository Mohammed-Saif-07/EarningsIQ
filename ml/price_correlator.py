import math


def synthetic_price_impact(ticker: str, sentiment_mean: float, anomaly_count: int) -> dict:
    base = (sum(ord(c) for c in ticker.upper()) % 17) / 10.0
    direction = -1 if sentiment_mean < 0 else 1
    delta_1d = direction * (base + anomaly_count * 0.25)
    delta_5d = delta_1d * (1.0 + math.log1p(anomaly_count + 1) / 3.0)
    return {"price_delta_1d": round(delta_1d, 2), "price_delta_5d": round(delta_5d, 2)}
