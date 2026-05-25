-- Executive speaker sentiment analysis
-- Built by Saif Mohammed - smohammed8@seattleu.edu
SELECT ticker, fiscal_year, quarter, COALESCE(speaker_role, 'Unknown') AS speaker_role,
       SUM(sentence_count) AS sentences,
       ROUND(AVG(avg_sentiment)::NUMERIC, 4) AS avg_sentiment,
       SUM(negative_count) AS negative_sentences
FROM v_speaker_sentiment
GROUP BY ticker, fiscal_year, quarter, COALESCE(speaker_role, 'Unknown')
ORDER BY ticker, fiscal_year DESC, quarter DESC, avg_sentiment ASC;
