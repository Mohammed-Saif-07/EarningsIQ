-- ============================================================
-- EarningsIQ - Views
-- Built by Saif Mohammed - smohammed8@seattleu.edu
-- ============================================================
CREATE OR REPLACE VIEW v_filing_summary AS
SELECT f.id AS filing_id, f.ticker, c.name AS company_name, c.sector, f.quarter, f.fiscal_year, f.filed_at,
       f.processing_status, f.word_count, COUNT(DISTINCT ss.id) AS sentence_count,
       ROUND(AVG(ss.sentiment_score)::NUMERIC, 4) AS sentiment_mean,
       ROUND(STDDEV(ss.sentiment_score)::NUMERIC, 4) AS sentiment_std,
       ROUND(MIN(ss.sentiment_score)::NUMERIC, 4) AS sentiment_min,
       ROUND(MAX(ss.sentiment_score)::NUMERIC, 4) AS sentiment_max,
       COUNT(DISTINCT ae.id) AS total_anomalies,
       COUNT(DISTINCT ae.id) FILTER (WHERE ae.severity='high') AS high_severity_anomalies,
       sr.signal, sr.confidence, sc.price_delta_1d_pct, sc.price_delta_5d_pct, sc.signal_score
FROM filings f
LEFT JOIN companies c ON c.id = f.company_id
LEFT JOIN sentence_sentiments ss ON ss.filing_id = f.id
LEFT JOIN anomaly_events ae ON ae.filing_id = f.id
LEFT JOIN signal_reports sr ON sr.filing_id = f.id
LEFT JOIN signal_correlations sc ON sc.filing_id = f.id
GROUP BY f.id, f.ticker, c.name, c.sector, f.quarter, f.fiscal_year, f.filed_at, f.processing_status,
         f.word_count, sr.signal, sr.confidence, sc.price_delta_1d_pct, sc.price_delta_5d_pct, sc.signal_score;

CREATE OR REPLACE VIEW v_top_anomalies AS
SELECT ae.id, f.ticker, c.name AS company_name, f.quarter, f.fiscal_year, ae.speaker, ae.sentence_text,
       ae.zscore, ae.anomaly_type, ae.severity, ae.flagged_at, sr.signal, sc.price_delta_1d_pct
FROM anomaly_events ae
JOIN filings f ON f.id = ae.filing_id
JOIN companies c ON c.id = f.company_id
LEFT JOIN signal_reports sr ON sr.filing_id = f.id
LEFT JOIN signal_correlations sc ON sc.filing_id = f.id
WHERE ae.flagged_at >= NOW() - INTERVAL '30 days'
ORDER BY ABS(ae.zscore) DESC
LIMIT 50;

CREATE OR REPLACE VIEW v_speaker_sentiment AS
SELECT f.ticker, f.fiscal_year, f.quarter, ss.speaker_role, COUNT(*) AS sentence_count,
       ROUND(AVG(ss.sentiment_score)::NUMERIC, 4) AS avg_sentiment,
       ROUND(AVG(ss.positive_prob)::NUMERIC, 4) AS avg_positive_prob,
       ROUND(AVG(ss.negative_prob)::NUMERIC, 4) AS avg_negative_prob,
       COUNT(*) FILTER (WHERE ss.sentiment_label='negative') AS negative_count
FROM sentence_sentiments ss
JOIN filings f ON f.id = ss.filing_id
GROUP BY f.ticker, f.fiscal_year, f.quarter, ss.speaker_role
ORDER BY f.ticker, f.fiscal_year, f.quarter, avg_sentiment;

CREATE OR REPLACE VIEW v_signal_accuracy AS
SELECT sr.signal, COUNT(*) AS total_calls,
       COUNT(*) FILTER (WHERE (sr.signal='BUY' AND sc.price_delta_5d_pct > 0)
          OR (sr.signal='SELL' AND sc.price_delta_5d_pct < 0)
          OR (sr.signal='NEUTRAL' AND ABS(sc.price_delta_5d_pct) < 2)) AS correct_calls,
       ROUND(100.0 * COUNT(*) FILTER (WHERE (sr.signal='BUY' AND sc.price_delta_5d_pct > 0)
          OR (sr.signal='SELL' AND sc.price_delta_5d_pct < 0)
          OR (sr.signal='NEUTRAL' AND ABS(sc.price_delta_5d_pct) < 2)) / NULLIF(COUNT(*), 0), 2) AS accuracy_pct,
       ROUND(AVG(sc.price_delta_5d_pct)::NUMERIC, 2) AS avg_5d_return
FROM signal_reports sr
JOIN signal_correlations sc ON sc.filing_id = sr.filing_id
WHERE sc.price_delta_5d_pct IS NOT NULL
GROUP BY sr.signal;
