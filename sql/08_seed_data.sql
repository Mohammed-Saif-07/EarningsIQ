-- ============================================================
-- EarningsIQ - Seed Data
-- Built by Saif Mohammed - smohammed8@seattleu.edu
-- ============================================================
INSERT INTO companies (ticker, name, sector, exchange, cik) VALUES
('AAPL','Apple Inc.','Technology','NASDAQ','0000320193'),
('MSFT','Microsoft Corporation','Technology','NASDAQ','0000789019'),
('AMZN','Amazon.com Inc.','Consumer Cyclical','NASDAQ','0001018724'),
('GOOGL','Alphabet Inc.','Communication','NASDAQ','0001652044'),
('META','Meta Platforms Inc.','Communication','NASDAQ','0001326801'),
('NVDA','NVIDIA Corporation','Technology','NASDAQ','0001045810'),
('TSLA','Tesla Inc.','Consumer Cyclical','NASDAQ','0001318605'),
('JPM','JPMorgan Chase & Co.','Financial','NYSE','0000019617'),
('GS','Goldman Sachs Group Inc.','Financial','NYSE','0000886982'),
('JNJ','Johnson & Johnson','Healthcare','NYSE','0000200406')
ON CONFLICT (ticker) DO NOTHING;
