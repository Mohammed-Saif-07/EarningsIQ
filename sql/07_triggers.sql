-- ============================================================
-- EarningsIQ - Triggers
-- Built by Saif Mohammed - smohammed8@seattleu.edu
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_companies_updated_at BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_filings_updated_at BEFORE UPDATE ON filings FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE FUNCTION auto_compute_signal_score()
RETURNS TRIGGER AS $$
BEGIN
    NEW.signal_score := compute_signal_score(NEW.anomaly_count, NEW.high_severity_count, NEW.sentiment_mean, NEW.price_delta_1d_pct);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auto_signal_score BEFORE INSERT OR UPDATE ON signal_correlations FOR EACH ROW EXECUTE FUNCTION auto_compute_signal_score();

CREATE OR REPLACE FUNCTION sync_filing_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'success' THEN
        UPDATE filings SET processing_status = CASE
            WHEN NEW.agent_name LIKE '%ingest%' THEN 'ingested'
            WHEN NEW.agent_name LIKE '%nlp%' THEN 'scored'
            WHEN NEW.agent_name LIKE '%research%' THEN 'researched'
            WHEN NEW.agent_name LIKE '%report%' THEN 'reported'
            ELSE processing_status END,
            updated_at = NOW()
        WHERE id = NEW.filing_id;
    ELSIF NEW.status = 'failed' THEN
        UPDATE filings SET processing_status = 'error', error_message = NEW.error_message, updated_at = NOW()
        WHERE id = NEW.filing_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_filing_status_sync AFTER INSERT ON agent_run_log FOR EACH ROW EXECUTE FUNCTION sync_filing_status();
