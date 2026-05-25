-- ============================================================
-- EarningsIQ - Partitioning Strategy
-- Built by Saif Mohammed - smohammed8@seattleu.edu
-- ============================================================
CREATE OR REPLACE FUNCTION create_year_partition(p_year INTEGER)
RETURNS void AS $$
DECLARE
    partition_name TEXT := 'filings_' || p_year;
BEGIN
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF filings FOR VALUES FROM (%s) TO (%s)', partition_name, p_year, p_year + 1);
    RAISE NOTICE 'Partition % created', partition_name;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE VIEW partition_sizes AS
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(format('%I.%I', schemaname, tablename))) AS total_size,
       pg_total_relation_size(format('%I.%I', schemaname, tablename)) AS raw_bytes
FROM pg_tables
WHERE tablename LIKE 'filings_%' OR tablename LIKE 'sentence_sentiments_%'
ORDER BY raw_bytes DESC;
