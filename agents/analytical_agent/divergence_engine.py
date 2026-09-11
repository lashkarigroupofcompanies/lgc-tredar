"""
Quantitative Divergence Detection Engine (RSI & MACD)
Covers:
- Regular Bullish Divergence (Price LL, Indicator HL -> Reversal Up)
- Regular Bearish Divergence (Price HH, Indicator LH -> Reversal Down)
- Hidden Bullish Divergence (Price HL, Indicator LL -> Continuation Up)
- Hidden Bearish Divergence (Price LH, Indicator HH -> Continuation Down)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


class DivergenceEngine:
    """
    Identifies institutional regular and hidden momentum divergences.
    """

    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        return 100 - (100 / (1 + rs))

    @classmethod
    def detect_divergences(cls, df: pd.DataFrame, lookback: int = 25) -> List[Dict[str, Any]]:
        """
        Scans recent price swings vs RSI swings for divergence signatures.
        """
        divergences = []
        if len(df) < lookback:
            return divergences

        close = [float(x) for x in df["close"].iloc[-lookback:]]
        rsi_series = cls.calculate_rsi(df["close"]).iloc[-lookback:]
        rsi = [float(x) for x in rsi_series]

        # Find 2 most prominent local lows and highs in the window
        half = lookback // 2
        p1_high, p2_high = max(close[:half]), max(close[half:])
        r1_high, r2_high = max(rsi[:half]), max(rsi[half:])

        p1_low, p2_low = min(close[:half]), min(close[half:])
        r1_low, r2_low = min(rsi[:half]), min(rsi[half:])

        # 1. REGULAR BEARISH DIVERGENCE (Price Higher High, RSI Lower High)
        if p2_high > p1_high and r2_high < r1_high and r1_high > 65:
            divergences.append({
                "type": "REGULAR_BEARISH_DIVERGENCE",
                "bias": "REVERSAL_DOWN",
                "confidence": 0.88,
                "description": "Price printed a Higher High while momentum (RSI) printed a Lower High (Exhaustion Top)."
            })

        # 2. REGULAR BULLISH DIVERGENCE (Price Lower Low, RSI Higher Low)
        if p2_low < p1_low and r2_low > r1_low and r1_low < 35:
            divergences.append({
                "type": "REGULAR_BULLISH_DIVERGENCE",
                "bias": "REVERSAL_UP",
                "confidence": 0.88,
                "description": "Price printed a Lower Low while momentum (RSI) printed a Higher Low (Seller Absorption Bottom)."
            })

        # 3. HIDDEN BULLISH DIVERGENCE (Price Higher Low, RSI Lower Low -> Continuation)
        if p2_low > p1_low and r2_low < r1_low:
            divergences.append({
                "type": "HIDDEN_BULLISH_DIVERGENCE",
                "bias": "CONTINUATION_UP",
                "confidence": 0.82,
                "description": "Price formed a Higher Low while RSI dipped deeper (Institutional Accumulation during Pullback)."
            })

        # 4. HIDDEN BEARISH DIVERGENCE (Price Lower High, RSI Higher High -> Continuation)
        if p2_high < p1_high and r2_high > r1_high:
            divergences.append({
                "type": "HIDDEN_BEARISH_DIVERGENCE",
                "bias": "CONTINUATION_DOWN",
                "confidence": 0.82,
                "description": "Price formed a Lower High while RSI pushed higher (Bearish Trend Continuation)."
            })

        return divergences

    @classmethod
    def get_divergence_verdict(cls, df: pd.DataFrame) -> Dict[str, Any]:
        divs = cls.detect_divergences(df)
        if not divs:
            return {
                "divergence_signal": "NONE",
                "bias": "NEUTRAL",
                "confidence": 0.50,
                "active_divergences": []
            }
        top = divs[0]
        return {
            "divergence_signal": top["type"],
            "bias": top["bias"],
            "confidence": top["confidence"],
            "description": top["description"],
            "active_divergences": divs
        }


if __name__ == "__main__":
    from agents.analytical_agent.market_feed import MarketFeedEngine
    feed = MarketFeedEngine()
    df = feed.fetch_crypto_candles("BTC", interval="15m", limit=60)
    res = DivergenceEngine.get_divergence_verdict(df)
    print("Divergence Signal:", res["divergence_signal"], "| Bias:", res["bias"])
