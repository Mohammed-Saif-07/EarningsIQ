-- ============================================================
-- EarningsIQ - Indexes
-- Built by Saif Mohammed - smohammed8@seattleu.edu
-- ============================================================
CREATE INDEX idx_companies_ticker ON companies (ticker);
CREATE INDEX idx_companies_sector ON companies (sector);
CREATE INDEX idx_filings_ticker ON filings (ticker);
CREATE INDEX idx_filings_status ON filings (processing_status);
CREATE INDEX idx_filings_filed_at ON filings (filed_at DESC);
CREATE INDEX idx_filings_ticker_year ON filings (ticker, fiscal_year);
CREATE INDEX idx_filings_company ON filings (company_id);
CREATE INDEX idx_filings_fts ON filings USING GIN (to_tsvector('english', COALESCE(transcript_text, '')));
CREATE INDEX idx_sentiments_filing ON sentence_sentiments (filing_id);
CREATE INDEX idx_sentiments_speaker ON sentence_sentiments (speaker);
CREATE INDEX idx_sentiments_score ON sentence_sentiments (sentiment_score);
CREATE INDEX idx_sentiments_filing_idx ON sentence_sentiments (filing_id, sentence_index);
CREATE INDEX idx_sentiments_text_trgm ON sentence_sentiments USING GIN (sentence_text gin_trgm_ops);
CREATE INDEX idx_anomalies_filing ON anomaly_events (filing_id);
CREATE INDEX idx_anomalies_severity ON anomaly_events (severity);
CREATE INDEX idx_anomalies_type ON anomaly_events (anomaly_type);
CREATE INDEX idx_anomalies_zscore ON anomaly_events (zscore DESC);
CREATE INDEX idx_anomalies_flagged_at ON anomaly_events (flagged_at DESC);
CREATE INDEX idx_signals_ticker ON signal_correlations (ticker);
CREATE INDEX idx_signals_score ON signal_correlations (signal_score DESC);
CREATE INDEX idx_signals_delta_1d ON signal_correlations (price_delta_1d_pct);
CREATE INDEX idx_reports_signal ON signal_reports (signal);
CREATE INDEX idx_reports_confidence ON signal_reports (confidence DESC);
CREATE INDEX idx_agent_log_agent ON agent_run_log (agent_name);
CREATE INDEX idx_agent_log_status ON agent_run_log (status);
CREATE INDEX idx_agent_log_started ON agent_run_log (started_at DESC);
