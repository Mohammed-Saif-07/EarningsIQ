-- Top 10 anomalous companies this week
-- Built by Saif Mohammed - smohammed8@seattleu.edu
SELECT f.ticker, c.name, f.quarter, f.fiscal_year, COUNT(ae.id) AS anomaly_count,
       ROUND(MAX(ABS(ae.zscore))::NUMERIC, 2) AS max_zscore,
       ROUND(AVG(ss.sentiment_score)::NUMERIC, 4) AS avg_sentiment,
       sc.price_delta_1d_pct, sr.signal
FROM anomaly_events ae
JOIN filings f ON f.id = ae.filing_id
JOIN companies c ON c.id = f.company_id
JOIN sentence_sentiments ss ON ss.id = ae.sentence_id
LEFT JOIN signal_correlations sc ON sc.filing_id = f.id
LEFT JOIN signal_reports sr ON sr.filing_id = f.id
WHERE ae.flagged_at >= NOW() - INTERVAL '7 days' AND ae.severity IN ('high','medium')
GROUP BY f.ticker, c.name, f.quarter, f.fiscal_year, sc.price_delta_1d_pct, sr.signal
ORDER BY anomaly_count DESC, max_zscore DESC
LIMIT 10;
