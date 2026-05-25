-- ============================================================
-- EarningsIQ - Stored Functions
-- Built by Saif Mohammed - smohammed8@seattleu.edu
-- ============================================================
CREATE OR REPLACE FUNCTION get_filing_dashboard(p_filing_id UUID)
RETURNS JSON AS $$
DECLARE result JSON;
BEGIN
    SELECT json_build_object(
        'filing', row_to_json(f.*),
        'company', row_to_json(c.*),
        'sentiment', (SELECT COALESCE(json_agg(row_to_json(ss.*) ORDER BY ss.sentence_index), '[]'::json) FROM sentence_sentiments ss WHERE ss.filing_id = p_filing_id),
        'anomalies', (SELECT COALESCE(json_agg(row_to_json(ae.*) ORDER BY ae.zscore DESC), '[]'::json) FROM anomaly_events ae WHERE ae.filing_id = p_filing_id),
        'report', row_to_json(sr.*),
        'correlation', row_to_json(sc.*)
    ) INTO result
    FROM filings f
    JOIN companies c ON c.id = f.company_id
    LEFT JOIN signal_reports sr ON sr.filing_id = f.id
    LEFT JOIN signal_correlations sc ON sc.filing_id = f.id
    WHERE f.id = p_filing_id
    LIMIT 1;
    RETURN result;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION compute_signal_score(p_anomaly_count INTEGER, p_high_severity INTEGER, p_sentiment_mean NUMERIC, p_price_delta_1d NUMERIC)
RETURNS NUMERIC AS $$
BEGIN
    RETURN LEAST(100, GREATEST(0, (p_anomaly_count * 10.0) + (p_high_severity * 20.0) + (ABS(COALESCE(p_sentiment_mean, 0)) * 30.0) + (ABS(COALESCE(p_price_delta_1d, 0)) * 5.0)));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION search_transcripts(p_query TEXT)
RETURNS TABLE (ticker VARCHAR, filed_at TIMESTAMPTZ, rank REAL, headline TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT f.ticker, f.filed_at,
           ts_rank(to_tsvector('english', COALESCE(f.transcript_text, '')), plainto_tsquery('english', p_query)) AS rank,
           ts_headline('english', COALESCE(f.transcript_text, ''), plainto_tsquery('english', p_query), 'MaxWords=30, MinWords=15, StartSel=<mark>, StopSel=</mark>') AS headline
    FROM filings f
    WHERE to_tsvector('english', COALESCE(f.transcript_text, '')) @@ plainto_tsquery('english', p_query)
    ORDER BY rank DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql;
