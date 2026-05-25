-- ============================================================
-- EarningsIQ - Database Schema
-- Built by Saif Mohammed - smohammed8@seattleu.edu
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    cik VARCHAR(20) UNIQUE,
    sector VARCHAR(100),
    industry VARCHAR(100),
    exchange VARCHAR(20),
    market_cap BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE filings (
    id UUID DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    ticker VARCHAR(10) NOT NULL,
    accession_number VARCHAR(25) NOT NULL,
    form_type VARCHAR(10) NOT NULL DEFAULT '8-K',
    quarter SMALLINT CHECK (quarter BETWEEN 1 AND 4),
    fiscal_year SMALLINT NOT NULL,
    filed_at TIMESTAMPTZ NOT NULL,
    earnings_date DATE,
    transcript_text TEXT,
    word_count INTEGER,
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending','ingested','scored','anomaly_detected','researched','reported','error','watcher_done','ingest_done','nlp_done','research_done','report_done')),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, fiscal_year),
    UNIQUE (accession_number, fiscal_year)
) PARTITION BY RANGE (fiscal_year);

CREATE TABLE filings_2022 PARTITION OF filings FOR VALUES FROM (2022) TO (2023);
CREATE TABLE filings_2023 PARTITION OF filings FOR VALUES FROM (2023) TO (2024);
CREATE TABLE filings_2024 PARTITION OF filings FOR VALUES FROM (2024) TO (2025);
CREATE TABLE filings_2025 PARTITION OF filings FOR VALUES FROM (2025) TO (2026);
CREATE TABLE filings_2026 PARTITION OF filings FOR VALUES FROM (2026) TO (2027);

CREATE TABLE sentence_sentiments (
    id UUID DEFAULT uuid_generate_v4(),
    filing_id UUID NOT NULL,
    filing_year SMALLINT NOT NULL,
    sentence_index INTEGER NOT NULL,
    speaker VARCHAR(100),
    speaker_role VARCHAR(50),
    sentence_text TEXT NOT NULL,
    sentiment_label VARCHAR(10) NOT NULL CHECK (sentiment_label IN ('positive','negative','neutral')),
    sentiment_score NUMERIC(5,4) CHECK (sentiment_score BETWEEN -1.0 AND 1.0),
    positive_prob NUMERIC(5,4),
    negative_prob NUMERIC(5,4),
    neutral_prob NUMERIC(5,4),
    rolling_avg_10 NUMERIC(5,4),
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, sentiment_label),
    UNIQUE (filing_id, sentence_index, sentiment_label),
    FOREIGN KEY (filing_id, filing_year) REFERENCES filings(id, fiscal_year) ON DELETE CASCADE
) PARTITION BY LIST (sentiment_label);

CREATE TABLE sentence_sentiments_positive PARTITION OF sentence_sentiments FOR VALUES IN ('positive');
CREATE TABLE sentence_sentiments_negative PARTITION OF sentence_sentiments FOR VALUES IN ('negative');
CREATE TABLE sentence_sentiments_neutral PARTITION OF sentence_sentiments FOR VALUES IN ('neutral');

CREATE TABLE anomaly_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id UUID NOT NULL,
    filing_year SMALLINT NOT NULL,
    sentence_id UUID NOT NULL,
    sentence_label VARCHAR(10) NOT NULL,
    sentence_index INTEGER NOT NULL,
    speaker VARCHAR(100),
    sentence_text TEXT NOT NULL,
    zscore NUMERIC(8,4) NOT NULL,
    isolation_score NUMERIC(8,6),
    anomaly_type VARCHAR(30) CHECK (anomaly_type IN ('sudden_negative_shift','evasive_language','sentiment_reversal','outlier_isolation_forest')),
    severity VARCHAR(10) CHECK (severity IN ('low','medium','high')),
    flagged_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (filing_id, filing_year) REFERENCES filings(id, fiscal_year) ON DELETE CASCADE,
    FOREIGN KEY (sentence_id, sentence_label) REFERENCES sentence_sentiments(id, sentiment_label)
);

CREATE TABLE price_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id),
    ticker VARCHAR(10) NOT NULL,
    snapshot_date DATE NOT NULL,
    open_price NUMERIC(12,4),
    close_price NUMERIC(12,4),
    volume BIGINT,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (ticker, snapshot_date)
);

CREATE TABLE signal_correlations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id UUID NOT NULL,
    filing_year SMALLINT NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    quarter SMALLINT,
    fiscal_year SMALLINT,
    price_pre_5d_avg NUMERIC(12,4),
    price_post_1d NUMERIC(12,4),
    price_post_5d NUMERIC(12,4),
    price_delta_1d_pct NUMERIC(8,4),
    price_delta_5d_pct NUMERIC(8,4),
    sentiment_mean NUMERIC(5,4),
    sentiment_std NUMERIC(5,4),
    anomaly_count INTEGER DEFAULT 0,
    high_severity_count INTEGER DEFAULT 0,
    signal_score NUMERIC(5,2),
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (filing_id, filing_year) REFERENCES filings(id, fiscal_year) ON DELETE CASCADE
);

CREATE TABLE signal_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id UUID NOT NULL,
    filing_year SMALLINT NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    signal VARCHAR(10) CHECK (signal IN ('BUY','SELL','NEUTRAL','WATCH')),
    confidence SMALLINT CHECK (confidence BETWEEN 0 AND 100),
    key_quote_1 TEXT,
    key_quote_2 TEXT,
    key_quote_3 TEXT,
    reasoning TEXT,
    full_report_text TEXT,
    company_context TEXT,
    generated_by VARCHAR(50) DEFAULT 'report-agent-llama3',
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (filing_id, filing_year) REFERENCES filings(id, fiscal_year) ON DELETE CASCADE
);

CREATE TABLE signal_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id UUID NOT NULL,
    filing_year SMALLINT NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    news_summary TEXT,
    sources JSONB,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (filing_id, filing_year) REFERENCES filings(id, fiscal_year) ON DELETE CASCADE
);

CREATE TABLE agent_run_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id UUID,
    filing_year SMALLINT,
    agent_name VARCHAR(50) NOT NULL,
    pod_name VARCHAR(100),
    status VARCHAR(20) CHECK (status IN ('started','success','failed','skipped')),
    duration_ms INTEGER,
    records_processed INTEGER,
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE kafka_offsets (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(100) NOT NULL,
    partition_num INTEGER NOT NULL,
    consumer_group VARCHAR(100) NOT NULL,
    committed_offset BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (topic, partition_num, consumer_group)
);
