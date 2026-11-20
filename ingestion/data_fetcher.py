import logging
from pathlib import Path
import random
import signal
import time
import yaml
import yfinance as yf

from database.connection import DatabaseConnection
from ingestion.validator import TickValidator
from processing.indicators import RealTimeIndicators

logger = logging.getLogger(__name__)


class MarketDataFetcher:
    def __init__(self, config_path: str = "config/settings.yaml"):
        # Resolve config relative to project root if relative path provided
        cfg_file = Path(config_path)
        if not cfg_file.is_absolute():
            base_dir = Path(__file__).resolve().parent.parent
            resolved_cfg = base_dir / config_path
            if resolved_cfg.exists():
                cfg_file = resolved_cfg

        with open(cfg_file, "r") as file:
            self.config = yaml.safe_load(file)

        # Extracting values
        self.tickers = self.config["market_data"]["tickers"]
        self.interval = self.config["market_data"]["update_interval_seconds"]

        # Starting prices
        self.price_tracks = {}
        for ticker in self.tickers:
            self.price_tracks[ticker] = random.uniform(150.0, 450.0)

        # Establish connection with the Database
        self.db = DatabaseConnection(self.config)

        # Establish connection to calculate indicators
        self.indicator = RealTimeIndicators()

        # Initialize algorithmic validator
        val_config = self.config.get("validation", {})
        self.validator = TickValidator(
            max_price_variance_percent=val_config.get("max_price_variance_percent", 10.0),
            allow_missing_volume=val_config.get("allow_missing_volume", False),
        )
        # Seed validator with initial baseline prices
        for ticker, price in self.price_tracks.items():
            self.validator.last_prices[ticker] = price

    def historical_data(self, ticker_symbol: str):
        try:
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(period="30d")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {ticker_symbol}: {e}")
            import pandas as pd
            return pd.DataFrame()

    def run_historical(self):
        logging.info(f"Tracking tickers found in config: {self.tickers}")
        for ticker in self.tickers:
            df = self.historical_data(ticker)
            logging.info(f"{ticker} Downloaded Rows Count: {len(df)}")

            if not df.empty:
                self.db.insert_historical_data(df, ticker)
            else:
                logging.warning(f"No data returned from Yahoo Finance for {ticker}!")

    def generate_simulated_tick(self) -> dict:
        # Choose a ticker
        ticker = random.choice(self.tickers)

        # Fluctuation percentage (-0.3% to +0.3%)
        change_percentage = random.uniform(-0.003, 0.003)

        # Update the tracked price
        self.price_tracks[ticker] = self.price_tracks[ticker] * (1 + change_percentage)

        # Generate a volume
        volume = random.randint(500, 15000)

        return {
            "ticker": ticker,
            "price": round(self.price_tracks[ticker], 2),
            "volume": volume,
        }

    # Backward compatibility alias
    generate_stimulated_tick = generate_simulated_tick

    def run_live_feed(self):
        logging.info(f"Starting live market feed simulation (Interval: {self.interval}s)")

        running = True

        def shutdown(signum, frame):
            nonlocal running
            logging.info("[SIGNAL RECEIVED] Shutting down after finishing the current tick process")
            running = False

        # Handle Ctrl+C interrupt gracefully
        signal.signal(signal.SIGINT, shutdown)

        try:
            while running:
                # 1. Fetch/Generate the tick data
                tick_data = self.generate_simulated_tick()
                logging.debug(f"New Market Data: {tick_data}")

                # 2. Algorithmic Data Firewall / Validation
                if not self.validator.validate(tick_data):
                    logging.warning(f"Discarding invalid tick: {tick_data}")
                    time.sleep(self.interval)
                    continue

                # 3. Calculate real-time indicators
                metrics = self.indicator.calculate_metrics(tick_data)
                logging.info(f"Ticker: {tick_data['ticker']} | Price: {tick_data['price']} | Metrics: {metrics}")

                # 4. Ingest tick and metrics into DB
                self.db.insert_tick_and_metrics(tick_data, metrics)

                # Pause the tick flow every interval to mimic real-world simulation
                time.sleep(self.interval)

        except Exception as e:
            logging.error(f"Error in live feed loop: {e}", exc_info=True)
        finally:
            logging.info("Closing Database connection...")
            self.db.close()
            logging.info("Shutdown Successful!")
