import os
import logging  # To store detailed information about the system
from pathlib import Path
import psycopg2  # Connects Python and PostgreSQL
from psycopg2 import OperationalError  # To catch specific error when DB goes offline
from psycopg2.extras import execute_values  # To send large amounts data at once to the DB


def _load_env_file():
    """Lightweight .env loader (avoids requiring external python-dotenv)."""
    if "DB_PASSWORD" in os.environ and os.environ["DB_PASSWORD"]:
        return

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


class DatabaseConnection:
    def __init__(self, config: dict):
        # Initialize the connection
        _load_env_file()
        self.config = config
        self.conn = None  # Connection Object
        self.cursor = None  # Cursor Object

        self.connect()

    def connect(self):
        # Establish connection with PostgreSQL
        try:
            db_cfg = self.config["database"]
            db_password = os.getenv("DB_PASSWORD", db_cfg.get("password"))

            # Creating the connection
            self.conn = psycopg2.connect(
                host=db_cfg["host"],
                port=db_cfg["port"],
                database=db_cfg["database"],
                user=db_cfg["user"],
                password=db_password,
            )

            # Creating the cursor
            self.cursor = self.conn.cursor()
            logging.info("Connected Succesfully")

        except OperationalError as e:
            logging.error(f"ERROR: {e}")
            raise e

    def insert_historical_data(self, df, ticker_symbol):
        try:
            logging.info(f"Processing historical data for ticker: {ticker_symbol}")
            query = """
                INSERT INTO historical_market_data (
                    ticker, open_price, high_price, low_price, close_price, volume, created_at
                ) VALUES %s
                ON CONFLICT (ticker, created_at) DO UPDATE SET
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume
            """
            values = []
            for index, row in df.iterrows():
                open_price = float(row["Open"])
                close_price = float(row["Close"])
                high_price = float(row["High"])
                low_price = float(row["Low"])
                volume = int(row["Volume"])
                created_date = index.date() if hasattr(index, "date") else index
                values.append((
                    ticker_symbol,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume,
                    created_date,
                ))

            execute_values(self.cursor, query, values)
            self.conn.commit()

        except Exception as e:
            logging.error(f"DATABASE INSERTION ERROR for {ticker_symbol}: {e}")
            self.conn.rollback()

    def insert_tick_and_metrics(self, tick: dict, metrics: dict):
        # Insert ticks and metrics into DB
        try:
            tick_query = (
                "insert into market_ticks(ticker, price, volume) values (%s,"
                " %s, %s);"
            )
            tick_values = (tick["ticker"], tick["price"], tick["volume"])

            self.cursor.execute(tick_query, tick_values)

            metrics_query = (
                "insert into calculated_metrics(ticker, vwap, sma, upper_band,"
                " lower_band, price, alert) values (%s, %s, %s, %s, %s, %s,"
                " %s);"
            )
            metrics_values = (
                metrics["ticker"],
                metrics["vwap"],
                metrics["sma"],
                metrics["upper_band"],
                metrics["lower_band"],
                metrics["current_price"],
                metrics["alert"],
            )
            self.cursor.execute(metrics_query, metrics_values)
            self.conn.commit()

        except Exception as e:
            logging.error(
                f"Insert failed for ticker: {tick.get('ticker')}."
                f"Tick: {tick}, Metrics: {metrics}. ERROR: {e}"
            )
            self.conn.rollback()
            """Acknowledges the error, wipes the slate clean and undo any half-transactions from the attempt, 
            and resets the connection to healthy state for smooth insertion of next tick"""

    def eod_process(self, sql_path: str = "database/archive_job.sql") -> None:
        try:
            sql_script = Path(sql_path).read_text()
            self.cursor.execute(sql_script)
            self.conn.commit()
            logging.info(
                "End-of-day archive process executed successfully from"
                f" {sql_path}."
            )
        except FileNotFoundError:
            logging.error(f"SQL file not found at path: {sql_path}")
            self.conn.rollback()
        except Exception as e:
            logging.error(f"Failed to execute archive SQL script: {e}")
            self.conn.rollback()

    # Close network connections safely when shutting down
    def close(self):
        """To avoid Attribute Error, i.e, if the connection was never established due to some crash and we try to close the connection
        it will throw an error as it tries to do None.close()"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

        logging.info("Connection succesfully terminated")