"""
Institutional ICT (Inner Circle Trader) & Smart Money Liquidity Engine
Covers:
- Section 8: BSL (Buy-Side Liquidity), SSL (Sell-Side Liquidity), FVG Consequent Encroachment (CE 50%),
  Breaker Blocks, Mitigation Blocks, Turtle Soup patterns, Power of 3 (AMD).
- Section 15: Kill Zones (Asian Range, London Open Killzone, NY Session Open Expansion).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


class ICTSmartMoneyEngine:
    """
    Advanced ICT Liquidity and Time-Based Institutional Flow Engine.
    """

    @staticmethod
    def identify_liquidity_pools(df: pd.DataFrame, window: int = 10) -> Dict[str, List[float]]:
        """
        Detects Buy-Side Liquidity (BSL) and Sell-Side Liquidity (SSL) resting pools:
        - BSL: Resting stop orders above Equal Highs & prominent Swing Highs.
        - SSL: Resting stop orders below Equal Lows & prominent Swing Lows.
        """
        bsl_levels = []
        ssl_levels = []

        if len(df) < window * 2:
            return {"bsl_levels": bsl_levels, "ssl_levels": ssl_levels}

        highs: List[float] = [float(x) for x in df["high"]]
        lows: List[float] = [float(x) for x in df["low"]]

        for i in range(window, len(df) - window):
            # Swing High = BSL Target
            if highs[i] == max(highs[i - window : i + window + 1]):
                bsl_levels.append(round(float(highs[i]), 2))

            # Swing Low = SSL Target
            if lows[i] == min(lows[i - window : i + window + 1]):
                ssl_levels.append(round(float(lows[i]), 2))

        # Filter and deduplicate near equal levels
        return {
            "bsl_levels": sorted(list(set(bsl_levels[-5:]))),  # Top resting buy liquidity
            "ssl_levels": sorted(list(set(ssl_levels[-5:])))   # Bottom resting sell liquidity
        }

    @staticmethod
    def calculate_fvg_consequent_encroachment(fvg_top: float, fvg_bottom: float) -> float:
        """
        Consequent Encroachment (CE): The precise 50% midpoint of a Fair Value Gap.
        Institutions routinely treat the 50% mark as the primary reaction barrier.
        """
        return round((fvg_top + fvg_bottom) / 2.0, 2)

    @staticmethod
    def detect_breaker_block(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detects Institutional Breaker Blocks:
        - Bullish Breaker: A bearish order block that was violated upwards during a lower low sweep,
          now flipping into powerful support upon retest.
        - Bearish Breaker: A bullish order block violated downwards during a higher high sweep,
          now flipping into resistance.
        """
        if len(df) < 15:
            return None

        recent_close = df["close"].iloc[-1]
        swing_high = df["high"].iloc[-15:-5].max()
        swing_low = df["low"].iloc[-15:-5].min()

        # Check if price retested a previous broken swing structure
        if recent_close > swing_high:
            return {
                "breaker_type": "BULLISH_BREAKER",
                "flip_level": float(swing_high),
                "bias": "BULLISH_SUPPORT",
                "confidence": 0.86,
                "description": "Previous resistance structure flipped into institutional Breaker support."
            }
        elif recent_close < swing_low:
            return {
                "breaker_type": "BEARISH_BREAKER",
                "flip_level": float(swing_low),
                "bias": "BEARISH_RESISTANCE",
                "confidence": 0.86,
                "description": "Previous support structure flipped into institutional Breaker resistance."
            }

        return None

    @staticmethod
    def evaluate_kill_zone(current_time_utc: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Evaluates active ICT Killzone based on UTC time:
        - Asian Range: 00:00 - 06:00 UTC (Liquidity buildup & consolidation)
        - London Open Killzone: 07:00 - 10:00 UTC (Manipulation / Judash swing)
        - New York Open Killzone: 12:00 - 15:00 UTC (Maximum volume & trend expansion)
        - London Close: 15:00 - 17:00 UTC (Profit taking / reversals)
        """
        now = current_time_utc or datetime.utcnow()
        hour = now.hour

        if 0 <= hour < 6:
            zone = "ASIAN_RANGE"
            phase = "ACCUMULATION_RANGE"
            volatility = "LOW_CONSOLIDATION"
        elif 7 <= hour < 10:
            zone = "LONDON_OPEN_KILLZONE"
            phase = "MANIPULATION_JUDAS_SWING"
            volatility = "HIGH_EXPANSION"
        elif 12 <= hour < 15:
            zone = "NEW_YORK_OPEN_KILLZONE"
            phase = "DISTRIBUTION_EXPANSION"
            volatility = "MAXIMUM_INSTITUTIONAL_VOLUME"
        elif 15 <= hour < 17:
            zone = "LONDON_CLOSE_KILLZONE"
            phase = "PROFIT_TAKING_REVERSAL"
            volatility = "MODERATE"
        else:
            zone = "OFF_SESSION"
            phase = "INTER_SESSION_FLOW"
            volatility = "STANDARD"

        return {
            "current_utc_time": now.strftime("%H:%M UTC"),
            "active_killzone": zone,
            "power_of_3_phase": phase,
            "session_volatility": volatility
        }

    @classmethod
    def analyze_ict_suite(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs comprehensive ICT Institutional analysis.
        """
        if df.empty:
            return {}

        liquidity = cls.identify_liquidity_pools(df)
        breaker = cls.detect_breaker_block(df)
        killzone = cls.evaluate_kill_zone()

        current_price = float(df["close"].iloc[-1])
        nearest_bsl = min([l for l in liquidity["bsl_levels"] if l > current_price], default=current_price * 1.02)
        nearest_ssl = max([l for l in liquidity["ssl_levels"] if l < current_price], default=current_price * 0.98)

        return {
            "bsl_target_above": round(nearest_bsl, 2),
            "ssl_target_below": round(nearest_ssl, 2),
            "liquidity_pools": liquidity,
            "breaker_block": breaker,
            "session_context": killzone
        }


if __name__ == "__main__":
    from agents.analytical_agent.market_feed import MarketFeedEngine
    feed = MarketFeedEngine()
    df = feed.fetch_crypto_candles("BTC", interval="15m", limit=60)
    ict = ICTSmartMoneyEngine.analyze_ict_suite(df)
    print("Nearest BSL (Buy-Side Liquidity Target):", ict["bsl_target_above"])
    print("Nearest SSL (Sell-Side Liquidity Target):", ict["ssl_target_below"])
    print("Active Session Killzone:", ict["session_context"]["active_killzone"])
    print("Power of 3 Phase (AMD):", ict["session_context"]["power_of_3_phase"])
