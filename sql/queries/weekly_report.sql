-- Weekly report rollup for dashboard and newsletter
-- Built by Saif Mohammed - smohammed8@seattleu.edu
SELECT ticker, company_name, sector, signal, confidence, signal_score,
       anomaly_count, high_severity_count, price_delta_1d_pct, price_delta_5d_pct
FROM mv_weekly_signals
ORDER BY signal_score DESC NULLS LAST, confidence DESC NULLS LAST;
