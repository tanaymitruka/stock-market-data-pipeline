import logging
from pathlib import Path
import yaml
from database.connection import DatabaseConnection

# Anchor base directory to project root so cron jobs execute cleanly from any directory
BASE_DIR = Path(__file__).resolve().parent
log_dir = BASE_DIR / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "archive_job.log"),
        logging.StreamHandler(),
    ],
)


def load_config(config_path: Path = None) -> dict:
    target_path = config_path or (BASE_DIR / "config" / "settings.yaml")
    if not target_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {target_path}")

    with open(target_path, "r") as f:
        return yaml.safe_load(f)


def main():
    logging.info("--- Starting End-of-Day Archiving Job ---")

    db = None
    try:
        config = load_config()
        db = DatabaseConnection(config)
        sql_file = BASE_DIR / "database" / "archive_job.sql"
        db.eod_process(str(sql_file))

    except Exception as e:
        logging.critical(f"Unhandled exception during EOD process: {e}", exc_info=True)
    finally:
        if db:
            db.close()
        logging.info("--- End-of-Day Archiving Job Completed ---")


if __name__ == "__main__":
    main()
