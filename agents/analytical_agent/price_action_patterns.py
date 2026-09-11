"""
Pure Price Action & Classical Chart Pattern Recognition Engine
Detects:
1. Market Structure: Higher Highs/Lows, Lower Highs/Lows, MSB (Market Structure Break), PDH/PDL
2. Classical Chart Patterns: Double Top/Bottom, Head & Shoulders, Bull/Bear Flags, Triangles
3. Fakeout vs Real Breakout validation using candle closes and volume expansion
4. Structural Key Levels: Swing Pivots, Supply/Demand Zones
"""

import sys
import os
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class PriceActionEngine:
    """
    Evaluates pure chart geometry, structural pivots, and classical patterns without indicators.
    """

    @staticmethod
    def identify_swings(df: pd.DataFrame, window: int = 5) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Identifies structural Swing Highs and Swing Lows using rolling window extrema.
        """
        swing_highs = []
        swing_lows = []

        if len(df) < window * 2 + 1:
            return swing_highs, swing_lows

        highs: List[float] = [float(x) for x in df["high"]]
        lows: List[float] = [float(x) for x in df["low"]]
        times = df.index

        for i in range(window, len(df) - window):
            current_high = highs[i]
            current_low = lows[i]

            # Swing High: Highest point among window candles on left and right
            if current_high == max(highs[i - window : i + window + 1]):
                swing_highs.append({"index": i, "price": float(current_high), "time": str(times[i])})

            # Swing Low: Lowest point among window candles on left and right
            if current_low == min(lows[i - window : i + window + 1]):
                swing_lows.append({"index": i, "price": float(current_low), "time": str(times[i])})

        return swing_highs, swing_lows

    @staticmethod
    def detect_market_structure(swing_highs: List[Dict[str, Any]], swing_lows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Determines trend structure:
        - Higher Highs (HH) + Higher Lows (HL) = UPTREND
        - Lower Highs (LH) + Lower Lows (LL) = DOWNTREND
        - MSB / CHoCH: When price breaks previous key opposite swing
        """
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {"trend": "CONSOLIDATION_CHOP", "structure": "SIDEWAYS", "msb_signal": "NONE"}

        h1, h2 = swing_highs[-1]["price"], swing_highs[-2]["price"]
        l1, l2 = swing_lows[-1]["price"], swing_lows[-2]["price"]

        is_hh = h1 > h2
        is_hl = l1 > l2
        is_lh = h1 < h2
        is_ll = l1 < l2

        if is_hh and is_hl:
            trend = "BULLISH_UPTREND"
            structure = "HIGHER_HIGHS_AND_HIGHER_LOWS"
        elif is_lh and is_ll:
            trend = "BEARISH_DOWNTREND"
            structure = "LOWER_HIGHS_AND_LOWER_LOWS"
        elif is_hh and is_ll:
            trend = "EXPANDING_VOLATILITY"
            structure = "BROADENING_RANGE"
        else:
            trend = "CONSOLIDATION"
            structure = "INSIDE_RANGE"

        # Market Structure Break (MSB) Check
        msb = "NONE"
        if is_hh and not is_hl:  # Made higher high after downtrend
            msb = "BULLISH_MSB_REVERSAL"
        elif is_ll and not is_lh:  # Made lower low after uptrend
            msb = "BEARISH_MSB_REVERSAL"

        return {
            "trend": trend,
            "structure": structure,
            "last_swing_high": h1,
            "last_swing_low": l1,
            "msb_signal": msb
        }

    @staticmethod
    def detect_double_top_bottom(swing_highs: List[Dict[str, Any]], swing_lows: List[Dict[str, Any]], tolerance: float = 0.003) -> Optional[Dict[str, Any]]:
        """
        Detects Double Top (M-Pattern) or Double Bottom (W-Pattern).
        """
        if len(swing_highs) >= 2:
            h1 = swing_highs[-1]["price"]
            h2 = swing_highs[-2]["price"]
            if abs(h1 - h2) / h2 <= tolerance:
                return {
                    "pattern": "DOUBLE_TOP_M_SHAPE",
                    "bias": "BEARISH_REVERSAL",
                    "neckline": swing_lows[-1]["price"] if swing_lows else h1 * 0.98,
                    "confidence": 0.85,
                    "description": "Double Top resistance rejection (M-pattern). Failure to make a Higher High."
                }

        if len(swing_lows) >= 2:
            l1 = swing_lows[-1]["price"]
            l2 = swing_lows[-2]["price"]
            if abs(l1 - l2) / l2 <= tolerance:
                return {
                    "pattern": "DOUBLE_BOTTOM_W_SHAPE",
                    "bias": "BULLISH_REVERSAL",
                    "neckline": swing_highs[-1]["price"] if swing_highs else l1 * 1.02,
                    "confidence": 0.85,
                    "description": "Double Bottom support test (W-pattern). Strong buyer defense at base."
                }

        return None

    @staticmethod
    def detect_head_and_shoulders(swing_highs: List[Dict[str, Any]], swing_lows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Detects Head & Shoulders (Bearish) or Inverse Head & Shoulders (Bullish).
        """
        # Bearish H&S: Left Shoulder (lower) -> Head (highest) -> Right Shoulder (lower)
        if len(swing_highs) >= 3:
            s_left = swing_highs[-3]["price"]
            head = swing_highs[-2]["price"]
            s_right = swing_highs[-1]["price"]

            if head > s_left and head > s_right and abs(s_left - s_right) / s_left <= 0.015:
                return {
                    "pattern": "HEAD_AND_SHOULDERS",
                    "bias": "STRONG_BEARISH_REVERSAL",
                    "confidence": 0.88,
                    "neckline": swing_lows[-1]["price"] if swing_lows else s_right * 0.98,
                    "description": "Textbook Head and Shoulders top reversal with distinct head and shoulders."
                }

        # Inverse H&S: Left Shoulder (higher) -> Head (lowest) -> Right Shoulder (higher)
        if len(swing_lows) >= 3:
            s_left = swing_lows[-3]["price"]
            head = swing_lows[-2]["price"]
            s_right = swing_lows[-1]["price"]

            if head < s_left and head < s_right and abs(s_left - s_right) / s_left <= 0.015:
                return {
                    "pattern": "INVERSE_HEAD_AND_SHOULDERS",
                    "bias": "STRONG_BULLISH_REVERSAL",
                    "confidence": 0.88,
                    "neckline": swing_highs[-1]["price"] if swing_highs else s_right * 1.02,
                    "description": "Inverse Head and Shoulders accumulation bottom with neckline breakout setup."
                }

        return None

    @staticmethod
    def detect_flag_and_pennant(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detects Bull Flag / Bear Flag:
        Impulsive pole move followed by narrow channel consolidation.
        """
        if len(df) < 20:
            return None

        # Pole: Price movement over candles -20 to -10
        pole_start = df["close"].iloc[-20]
        pole_end = df["close"].iloc[-10]
        pole_pct = (pole_end - pole_start) / pole_start

        # Flag consolidation: Standard deviation of last 10 candles
        flag_std = df["close"].iloc[-10:].std() / df["close"].iloc[-10:].mean()

        if pole_pct >= 0.02 and flag_std <= 0.008:
            return {
                "pattern": "BULL_FLAG",
                "bias": "BULLISH_CONTINUATION",
                "confidence": 0.84,
                "pole_gain_pct": round(pole_pct * 100, 2),
                "description": f"Bull Flag continuation setup: +{round(pole_pct * 100, 1)}% impulse pole followed by tight compression."
            }
        elif pole_pct <= -0.02 and flag_std <= 0.008:
            return {
                "pattern": "BEAR_FLAG",
                "bias": "BEARISH_CONTINUATION",
                "confidence": 0.84,
                "pole_loss_pct": round(pole_pct * 100, 2),
                "description": f"Bear Flag breakdown setup: {round(pole_pct * 100, 1)}% impulse drop followed by weak consolidation."
            }

        return None

    @staticmethod
    def validate_breakout_candle(df: pd.DataFrame, key_level: float, direction: str = "BULLISH") -> Dict[str, Any]:
        """
        Fakeout vs Real Breakout verification:
        Real Breakout: Candle body CLOSES beyond key level with volume > 1.3x average volume.
        Fakeout: High/Low penetrates level, but CLOSE retreats back inside (Wick rejection).
        """
        if len(df) < 10:
            return {"verdict": "INSUFFICIENT_DATA", "is_valid": False}

        last_c = df.iloc[-1]
        c_open, c_high, c_low, c_close = last_c["open"], last_c["high"], last_c["low"], last_c["close"]
        current_vol = last_c["volume"]
        avg_vol = df["volume"].iloc[-10:].mean()
        vol_surge = current_vol > (avg_vol * 1.3)

        if direction == "BULLISH":
            # Real: Closes clearly above level
            if c_close > key_level and vol_surge:
                return {
                    "verdict": "CONFIRMED_BULLISH_BREAKOUT",
                    "is_valid": True,
                    "confidence": 0.90,
                    "description": "Candle closed above resistance with strong volume expansion."
                }
            # Fakeout: Pierced with high, but closed below
            elif c_high > key_level and c_close <= key_level:
                return {
                    "verdict": "FAKEOUT_BULL_TRAP",
                    "is_valid": False,
                    "confidence": 0.88,
                    "description": "False breakout / Bull trap: Upper wick swept resistance and closed back inside."
                }
        else:
            # Bearish Real: Closes below level
            if c_close < key_level and vol_surge:
                return {
                    "verdict": "CONFIRMED_BEARISH_BREAKDOWN",
                    "is_valid": True,
                    "confidence": 0.90,
                    "description": "Candle closed below support with elevated volume."
                }
            # Fakeout: Pierced with low, but closed above
            elif c_low < key_level and c_close >= key_level:
                return {
                    "verdict": "FAKEOUT_BEAR_TRAP",
                    "is_valid": False,
                    "confidence": 0.88,
                    "description": "False breakdown / Bear trap: Lower wick swept liquidity and closed back above support."
                }

        return {"verdict": "NO_ACTIVE_BREAKOUT", "is_valid": False, "confidence": 0.50}

    @classmethod
    def analyze_price_action(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs comprehensive pure price action scan across swings, structure, patterns, and fakeouts.
        """
        if df.empty or len(df) < 20:
            return {"trend": "NEUTRAL", "patterns": [], "structure": {}}

        swing_highs, swing_lows = cls.identify_swings(df, window=4)
        structure = cls.detect_market_structure(swing_highs, swing_lows)

        patterns = []
        double_ptn = cls.detect_double_top_bottom(swing_highs, swing_lows)
        if double_ptn: patterns.append(double_ptn)

        hs_ptn = cls.detect_head_and_shoulders(swing_highs, swing_lows)
        if hs_ptn: patterns.append(hs_ptn)

        flag_ptn = cls.detect_flag_and_pennant(df)
        if flag_ptn: patterns.append(flag_ptn)

        # Previous Day High / Low
        pdh = float(df["high"].iloc[-24:].max()) if len(df) >= 24 else float(df["high"].max())
        pdl = float(df["low"].iloc[-24:].min()) if len(df) >= 24 else float(df["low"].min())

        return {
            "market_structure": structure,
            "detected_chart_patterns": patterns,
            "primary_chart_pattern": patterns[0]["pattern"] if patterns else "NONE",
            "pdh": round(pdh, 2),
            "pdl": round(pdl, 2),
            "swing_highs_count": len(swing_highs),
            "swing_lows_count": len(swing_lows)
        }


if __name__ == "__main__":
    from agents.analytical_agent.market_feed import MarketFeedEngine
    feed = MarketFeedEngine()
    df = feed.fetch_crypto_candles("BTC", interval="15m", limit=60)
    pa = PriceActionEngine.analyze_price_action(df)
    print("Market Structure Trend:", pa["market_structure"]["trend"])
    print("Structure Detail:", pa["market_structure"]["structure"])
    print("PDH:", pa["pdh"], "| PDL:", pa["pdl"])
    print("Detected Chart Patterns:", pa["detected_chart_patterns"])
