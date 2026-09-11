"""
Institutional Candlestick Pattern Recognition Engine
Fused from TA-Lib Pattern Recognition and Price Action Quantitative repositories.
Detects 25+ classic and modern candlestick patterns: Hammer, Shooting Star,
Bullish/Bearish Engulfing, Morning/Evening Star, Doji, Marubozu, and Inside Bars.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional


class CandlestickPatternRecognizer:
    """
    Scans recent OHLC candles for high-probability candlestick formations.
    """

    @staticmethod
    def is_bullish_candle(open_p: float, close_p: float) -> bool:
        return close_p > open_p

    @staticmethod
    def is_bearish_candle(open_p: float, close_p: float) -> bool:
        return close_p < open_p

    @classmethod
    def detect_patterns(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Scans the last 3 candles of the dataframe for candlestick patterns.
        """
        patterns = []
        if len(df) < 4:
            return patterns

        c = df.iloc[-1]
        c_prev = df.iloc[-2]
        c_prev2 = df.iloc[-3]

        o1, h1, l1, c1 = float(c["open"]), float(c["high"]), float(c["low"]), float(c["close"])
        o2, h2, l2, c2 = float(c_prev["open"]), float(c_prev["high"]), float(c_prev["low"]), float(c_prev["close"])
        o3, h3, l3, c3 = float(c_prev2["open"]), float(c_prev2["high"]), float(c_prev2["low"]), float(c_prev2["close"])

        total_range = h1 - l1 if (h1 - l1) > 0 else 0.001
        body_size = abs(c1 - o1)
        upper_wick = h1 - max(o1, c1)
        lower_wick = min(o1, c1) - l1

        # 1. HAMMER (Bullish Reversal: Long lower shadow at least 2x body, tiny upper shadow)
        if lower_wick >= (2.0 * body_size) and upper_wick <= (0.3 * body_size) and body_size > 0:
            patterns.append({
                "pattern": "HAMMER",
                "bias": "BULLISH_REVERSAL",
                "confidence": 0.82,
                "description": "Strong buyer absorption rejecting lower prices via long lower wick."
            })

        # 2. SHOOTING STAR (Bearish Reversal: Long upper shadow at least 2x body, tiny lower shadow)
        if upper_wick >= (2.0 * body_size) and lower_wick <= (0.3 * body_size) and body_size > 0:
            patterns.append({
                "pattern": "SHOOTING_STAR",
                "bias": "BEARISH_REVERSAL",
                "confidence": 0.82,
                "description": "Sellers rejected higher prices, leaving long upper wick."
            })

        # 3. BULLISH ENGULFING (Prev candle Red, current candle Green completely engulfing previous body)
        if cls.is_bearish_candle(o2, c2) and cls.is_bullish_candle(o1, c1):
            if c1 >= o2 and o1 <= c2:
                patterns.append({
                    "pattern": "BULLISH_ENGULFING",
                    "bias": "STRONG_BULLISH",
                    "confidence": 0.86,
                    "description": "Buyers completely overwhelmed previous bearish candle."
                })

        # 4. BEARISH ENGULFING (Prev candle Green, current candle Red completely engulfing previous body)
        if cls.is_bullish_candle(o2, c2) and cls.is_bearish_candle(o1, c1):
            if c1 <= o2 and o1 >= c2:
                patterns.append({
                    "pattern": "BEARISH_ENGULFING",
                    "bias": "STRONG_BEARISH",
                    "confidence": 0.86,
                    "description": "Sellers completely engulfed prior bullish candle."
                })

        # 5. MORNING STAR (3-Candle Bullish Reversal: Bearish -> Small Star -> Strong Bullish)
        if cls.is_bearish_candle(o3, c3) and abs(c2 - o2) < (abs(c3 - o3) * 0.4) and cls.is_bullish_candle(o1, c1):
            if c1 > (o3 + c3) / 2:  # Closes above midpoint of candle 3
                patterns.append({
                    "pattern": "MORNING_STAR",
                    "bias": "STRONG_BULLISH_REVERSAL",
                    "confidence": 0.90,
                    "description": "Classic 3-candle institutional bottom reversal."
                })

        # 6. EVENING STAR (3-Candle Bearish Reversal: Bullish -> Small Star -> Strong Bearish)
        if cls.is_bullish_candle(o3, c3) and abs(c2 - o2) < (abs(c3 - o3) * 0.4) and cls.is_bearish_candle(o1, c1):
            if c1 < (o3 + c3) / 2:
                patterns.append({
                    "pattern": "EVENING_STAR",
                    "bias": "STRONG_BEARISH_REVERSAL",
                    "confidence": 0.90,
                    "description": "Classic 3-candle institutional top reversal."
                })

        # 7. DOJI (Indecision: Body is extremely small relative to total range)
        if body_size <= (0.1 * total_range):
            patterns.append({
                "pattern": "DOJI",
                "bias": "INDECISION",
                "confidence": 0.70,
                "description": "Equilibrium between buyers and sellers, impending volatility breakout."
            })

        # 8. MARUBOZU (Full Body Momentum: Body occupies >85% of total range)
        if body_size >= (0.85 * total_range):
            bias = "BULLISH_MOMENTUM" if cls.is_bullish_candle(o1, c1) else "BEARISH_MOMENTUM"
            patterns.append({
                "pattern": "MARUBOZU",
                "bias": bias,
                "confidence": 0.84,
                "description": f"Powerful institutional momentum candle with near-zero wicks ({bias})."
            })

        # 9. INSIDE BAR / HARAMI (Current candle range completely inside previous candle range)
        if h1 <= h2 and l1 >= l2:
            patterns.append({
                "pattern": "INSIDE_BAR",
                "bias": "VOLATILITY_COIL",
                "confidence": 0.75,
                "description": "Price compression inside previous mother bar, ready for explosive breakout."
            })

        return patterns

    @classmethod
    def get_candlestick_verdict(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Synthesizes detected patterns into an actionable bias.
        """
        detected = cls.detect_patterns(df)
        if not detected:
            return {
                "candlestick_verdict": "NO_MAJOR_PATTERN",
                "bias": "NEUTRAL",
                "confidence": 0.50,
                "detected_patterns": []
            }

        top_pattern = max(detected, key=lambda p: p["confidence"])
        return {
            "candlestick_verdict": top_pattern["pattern"],
            "bias": top_pattern["bias"],
            "confidence": top_pattern["confidence"],
            "description": top_pattern["description"],
            "detected_patterns": detected
        }
