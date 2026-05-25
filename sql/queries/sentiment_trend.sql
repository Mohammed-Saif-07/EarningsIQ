-- Sentiment trend - rolling 4-quarter history per company
-- Built by Saif Mohammed - smohammed8@seattleu.edu
SELECT ticker, fiscal_year, quarter, sentiment_mean,
       LAG(sentiment_mean) OVER w AS prev_quarter_sentiment,
       sentiment_mean - LAG(sentiment_mean) OVER w AS sentiment_change,
       AVG(sentiment_mean) OVER (PARTITION BY ticker ORDER BY fiscal_year, quarter ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) AS rolling_4q_avg,
       price_delta_5d_pct
FROM v_filing_summary
WHERE ticker = COALESCE(NULLIF(current_setting('earningsiq.ticker', true), ''), 'AAPL')
WINDOW w AS (PARTITION BY ticker ORDER BY fiscal_year, quarter)
ORDER BY fiscal_year, quarter;
