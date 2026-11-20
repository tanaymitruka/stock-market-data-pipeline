from collections import deque
from datetime import date
import statistics
from typing import Optional


class RealTimeIndicators:
    """
    Real-time streaming technical indicators:
    - Volume Weighted Average Price (VWAP) with intraday session resets
    - Bollinger Bands (20-period SMA +/- 2 StdDev) with cold-start protection
    """

    def __init__(self, window_size: int = 20, max_ticks: Optional[int] = None):
        self.window_size = window_size
        self.max_ticks = max_ticks  # Optional manual tick threshold reset

        # Tracks {'cum_pv': float, 'total_vol': int, 'tick_count': int, 'session_date': date}
        self.data = {}

        # Sliding window for prices per ticker
        self.price_window = {}

    def calculate_metrics(self, tick: dict) -> dict:
        ticker = tick["ticker"]
        price = float(tick["price"])
        volume = int(tick["volume"])
        today = date.today()

        if ticker not in self.data:
            self.data[ticker] = {
                "cum_pv": 0.0,
                "total_vol": 0,
                "tick_count": 0,
                "session_date": today,
            }
            self.price_window[ticker] = deque(maxlen=self.window_size)

        # Automatic intraday reset when calendar date rolls over
        if self.data[ticker].get("session_date") != today:
            self.reset_vwap(ticker)
            self.data[ticker]["session_date"] = today

        # Optional tick-count reset if configured
        if self.max_ticks and self.data[ticker]["tick_count"] >= self.max_ticks:
            self.reset_vwap(ticker)

        # Accumulate volume and price-volume for VWAP
        self.data[ticker]["cum_pv"] += price * volume
        self.data[ticker]["total_vol"] += volume
        self.data[ticker]["tick_count"] += 1

        total_vol = self.data[ticker]["total_vol"]
        vwap = self.data[ticker]["cum_pv"] / total_vol if total_vol > 0 else price

        # Bollinger Bands calculation
        self.price_window[ticker].append(price)
        history = self.price_window[ticker]

        # Require a fully warmed-up window to avoid erratic alerts on 2-3 tick samples
        if len(history) >= self.window_size:
            sma = statistics.mean(history)
            std_dev = statistics.stdev(history)

            upper_band = sma + (2 * std_dev)
            lower_band = sma - (2 * std_dev)

            if price > upper_band:
                alert = "SELL"  # Overbought
            elif price < lower_band:
                alert = "BUY"   # Oversold
            else:
                alert = "HOLD"
        else:
            # Cold-start period: baseline metrics until the 20-tick window fills up
            sma = statistics.mean(history) if history else price
            upper_band = sma
            lower_band = sma
            alert = "HOLD"

        return {
            "ticker": ticker,
            "current_price": round(price, 2),
            "vwap": round(vwap, 2),
            "sma": round(sma, 2),
            "upper_band": round(upper_band, 2),
            "lower_band": round(lower_band, 2),
            "alert": alert,
        }

    def reset_vwap(self, ticker: str):
        """Resets VWAP accumulators for intra-day or session recalculation."""
        if ticker in self.data:
            self.data[ticker]["cum_pv"] = 0.0
            self.data[ticker]["total_vol"] = 0
            self.data[ticker]["tick_count"] = 0

    def reset_all(self):
        """Resets indicators across all tracked assets."""
        for ticker in list(self.data.keys()):
            self.reset_vwap(ticker)
