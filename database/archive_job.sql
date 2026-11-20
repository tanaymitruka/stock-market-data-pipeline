-- End-of-Day Rollup Job: Aggregates high-frequency ticks into daily OHLCV rows

INSERT INTO historical_market_data (
    ticker, 
    open_price, 
    high_price, 
    low_price, 
    close_price, 
    volume, 
    created_at
)
SELECT 
    ticker,
    (ARRAY_AGG(price ORDER BY created_at ASC))[1] AS open_price,
    MAX(price) AS high_price,
    MIN(price) AS low_price,
    (ARRAY_AGG(price ORDER BY created_at DESC))[1] AS close_price,
    SUM(volume) AS volume,
    created_at::DATE AS created_at
FROM market_ticks
GROUP BY ticker, created_at::DATE
ON CONFLICT (ticker, created_at) DO UPDATE 
SET 
    high_price = GREATEST(historical_market_data.high_price, EXCLUDED.high_price),
    low_price = LEAST(historical_market_data.low_price, EXCLUDED.low_price),
    close_price = EXCLUDED.close_price,
    volume = historical_market_data.volume + EXCLUDED.volume;

-- Delete only the archived ticks and metrics without acquiring ACCESS EXCLUSIVE locks
DELETE FROM market_ticks WHERE created_at::DATE <= CURRENT_DATE;
DELETE FROM calculated_metrics WHERE created_at::DATE <= CURRENT_DATE;
