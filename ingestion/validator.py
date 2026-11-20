import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TickValidator:
    """
    Data firewall that verifies incoming ticks for integrity, missing fields,
    and abnormal price variance against recent prices.
    """

    def __init__(self, max_price_variance_percent: float = 10.0, allow_missing_volume: bool = False):
        self.max_price_variance_percent = max_price_variance_percent
        self.allow_missing_volume = allow_missing_volume
        self.last_prices = {}

    def validate(self, tick: dict) -> bool:
        if not isinstance(tick, dict):
            logger.warning(f"Validation Error: Tick must be a dictionary, got {type(tick)}")
            return False

        # Mandatory fields check
        required_keys = ["ticker", "price"]
        if not self.allow_missing_volume:
            required_keys.append("volume")

        for key in required_keys:
            if key not in tick or tick[key] is None:
                logger.warning(f"Validation Error: Missing or null required key '{key}' in tick: {tick}")
                return False

        ticker = tick["ticker"]
        price = tick["price"]

        # Logical value checks
        try:
            price = float(price)
            if price <= 0:
                logger.warning(f"Validation Error: Non-positive price ({price}) for ticker {ticker}")
                return False
        except (ValueError, TypeError):
            logger.warning(f"Validation Error: Price could not be converted to float for ticker {ticker}")
            return False

        if "volume" in tick and tick["volume"] is not None:
            try:
                volume = int(tick["volume"])
                if volume < 0:
                    logger.warning(f"Validation Error: Negative volume ({volume}) for ticker {ticker}")
                    return False
            except (ValueError, TypeError):
                logger.warning(f"Validation Error: Volume could not be converted to int for ticker {ticker}")
                return False

        # Price variance check against last known price
        if ticker in self.last_prices and self.max_price_variance_percent > 0:
            last_price = self.last_prices[ticker]
            variance_pct = abs(price - last_price) / last_price * 100.0
            if variance_pct > self.max_price_variance_percent:
                logger.warning(
                    f"Validation Error: Price variance {variance_pct:.2f}% exceeds threshold "
                    f"{self.max_price_variance_percent}% for {ticker} (Last: {last_price}, New: {price})"
                )
                return False

        # Update last known valid price
        self.last_prices[ticker] = price
        return True


# Backward-compatible convenience function
_default_validator = TickValidator()

def validate_tick(tick: dict, validator: Optional[TickValidator] = None) -> bool:
    target_validator = validator or _default_validator
    return target_validator.validate(tick)
