-- ============================================================
-- EarningsIQ - Materialized Views
-- Built by Saif Mohammed - smohammed8@seattleu.edu
-- ============================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_weekly_signals AS
SELECT f.ticker, c.name AS company_name, c.sector, f.quarter, f.fiscal_year, f.filed_at, sr.signal, sr.confidence,
       sc.signal_score, sc.price_delta_1d_pct, sc.price_delta_5d_pct, sc.anomaly_count, sc.high_severity_count,
       COUNT(ae.id) AS total_anomalies
FROM filings f
JOIN companies c ON c.id = f.company_id
LEFT JOIN signal_reports sr ON sr.filing_id = f.id
LEFT JOIN signal_correlations sc ON sc.filing_id = f.id
LEFT JOIN anomaly_events ae ON ae.filing_id = f.id
WHERE f.filed_at >= NOW() - INTERVAL '7 days'
GROUP BY f.ticker, c.name, c.sector, f.quarter, f.fiscal_year, f.filed_at, sr.signal, sr.confidence,
         sc.signal_score, sc.price_delta_1d_pct, sc.price_delta_5d_pct, sc.anomaly_count, sc.high_severity_count
ORDER BY sc.signal_score DESC NULLS LAST;
CREATE UNIQUE INDEX IF NOT EXISTS mv_weekly_signals_uq ON mv_weekly_signals (ticker, quarter, fiscal_year);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_sector_sentiment AS
SELECT c.sector, DATE_TRUNC('week', f.filed_at) AS week_start, COUNT(DISTINCT f.ticker) AS company_count,
       ROUND(AVG(sc.sentiment_mean)::NUMERIC, 4) AS avg_sentiment,
       ROUND(AVG(sc.price_delta_5d_pct)::NUMERIC, 2) AS avg_5d_return,
       SUM(sc.anomaly_count) AS total_anomalies
FROM filings f
JOIN companies c ON c.id = f.company_id
JOIN signal_correlations sc ON sc.filing_id = f.id
GROUP BY c.sector, DATE_TRUNC('week', f.filed_at)
ORDER BY week_start DESC, avg_sentiment;
CREATE INDEX IF NOT EXISTS mv_sector_sentiment_idx ON mv_sector_sentiment (sector, week_start);

CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_weekly_signals;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_sector_sentiment;
    RAISE NOTICE 'Materialized views refreshed at %', NOW();
END;
$$ LANGUAGE plpgsql;
