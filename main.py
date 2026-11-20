import logging
from pathlib import Path
from ingestion.data_fetcher import MarketDataFetcher

# Ensure logs directory exists relative to project root
BASE_DIR = Path(__file__).resolve().parent
log_dir = BASE_DIR / "logs"
log_dir.mkdir(exist_ok=True)

# Configure logging path to sit inside the logs directory
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "data_ingestion.log"),
        logging.StreamHandler(),
    ],
)


def main():
    logging.info("Starting the stock data pipeline...")

    try:
        fetcher = MarketDataFetcher()

        logging.info("Initializing historical data ingestion (Yahoo Finance)...")
        fetcher.run_historical()
        logging.info("Historical data successfully initialized.")

        logging.info("Starting real-time market data feed...")
        fetcher.run_live_feed()

    except Exception as e:
        logging.critical(f"Fatal error in pipeline execution: {e}", exc_info=True)


if __name__ == "__main__":
    main()
