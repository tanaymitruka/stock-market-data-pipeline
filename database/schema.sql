-- Wipe pre-existing tables to start fresh
DROP TABLE IF EXISTS market_ticks CASCADE;
DROP TABLE IF EXISTS calculated_metrics CASCADE;
DROP TABLE IF EXISTS historical_market_data CASCADE;

-- Define market_ticks (High-frequency data keeps full timestamps)
CREATE TABLE market_ticks (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    volume BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Define calculated_metrics
CREATE TABLE calculated_metrics (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    vwap FLOAT,
    sma NUMERIC(10, 2),
    upper_band NUMERIC(10, 2),
    lower_band NUMERIC(10, 2),
    price NUMERIC(10, 2),
    alert VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Define historical_market_data (EOD Rollups use DATE)
CREATE TABLE historical_market_data (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    open_price NUMERIC(10, 2) NOT NULL,
    high_price NUMERIC(10, 2) NOT NULL,
    low_price NUMERIC(10, 2) NOT NULL,
    close_price NUMERIC(10, 2) NOT NULL,
    volume BIGINT NOT NULL,
    created_at DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Composite unique constraint on ticker + DATE
    CONSTRAINT uq_ticker_created UNIQUE (ticker, created_at)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_hist_ticker_created 
ON historical_market_data (ticker, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ticks_ticker_created 
ON market_ticks (ticker, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_metrics_ticker_created 
ON calculated_metrics (ticker, created_at DESC);