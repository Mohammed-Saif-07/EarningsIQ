-- Price correlation versus sentiment and anomalies
-- Built by Saif Mohammed - smohammed8@seattleu.edu
SELECT ticker, fiscal_year, quarter, sentiment_mean, anomaly_count, high_severity_count,
       price_delta_1d_pct, price_delta_5d_pct, signal_score,
       corr(sentiment_mean, price_delta_5d_pct) OVER () AS sample_sentiment_return_corr
FROM signal_correlations
WHERE computed_at >= NOW() - INTERVAL '365 days'
ORDER BY signal_score DESC NULLS LAST, computed_at DESC;
