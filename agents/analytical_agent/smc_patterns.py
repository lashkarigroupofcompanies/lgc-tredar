"""
Smart Money Concepts (SMC) & Institutional Price Action Engine
Fused from elite ICT / SMC quant trading repositories.
Detects Order Blocks (OB), Fair Value Gaps (FVG), Break of Structure (BOS), and Liquidity Sweeps.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional


class SmartMoneyConcepts:
    """
    Identifies institutional footprint: Order Blocks, Imbalances (FVG), and Liquidity Sweeps.
    """

    @staticmethod
    def detect_fair_value_gaps(df: pd.DataFrame, min_gap_pct: float = 0.001) -> List[Dict[str, Any]]:
        """
        Detects 3-candle Fair Value Gaps (FVGs).
        Bullish FVG: High of Candle 1 < Low of Candle 3 (Leaving an unfilled price gap).
        Bearish FVG: Low of Candle 1 > High of Candle 3.
        """
        fvgs = []
        if len(df) < 5:
            return fvgs

        for i in range(2, len(df)):
            c1_high = df["high"].iloc[i-2]
            c1_low = df["low"].iloc[i-2]
            c3_high = df["high"].iloc[i]
            c3_low = df["low"].iloc[i]
            c2_close = df["close"].iloc[i-1]

            # Bullish FVG
            if c3_low > c1_high:
                gap_size = c3_low - c1_high
                if gap_size / c2_close >= min_gap_pct:
                    fvgs.append({
                        "type": "BULLISH_FVG",
                        "index": i-1,
                        "time": str(df.index[i-1]),
                        "top": float(c3_low),
                        "bottom": float(c1_high),
                        "gap_size": round(float(gap_size), 2),
                        "status": "UNFILLED"
                    })

            # Bearish FVG
            elif c1_low > c3_high:
                gap_size = c1_low - c3_high
                if gap_size / c2_close >= min_gap_pct:
                    fvgs.append({
                        "type": "BEARISH_FVG",
                        "index": i-1,
                        "time": str(df.index[i-1]),
                        "top": float(c1_low),
                        "bottom": float(c3_high),
                        "gap_size": round(float(gap_size), 2),
                        "status": "UNFILLED"
                    })

        return fvgs[-5:]  # Return most recent 5 FVGs

    @staticmethod
    def detect_order_blocks(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detects Institutional Order Blocks:
        - Bullish OB: The lowest down-candle immediately preceding a strong expansion upwards that creates an imbalance.
        - Bearish OB: The highest up-candle immediately preceding a strong expansion downwards.
        """
        obs = []
        if len(df) < 10:
            return obs

        for i in range(4, len(df) - 1):
            # Check for strong displacement candle at i
            candle_body = abs(df["close"].iloc[i] - df["open"].iloc[i])
            avg_body = abs(df["close"].iloc[i-4:i] - df["open"].iloc[i-4:i]).mean()

            if candle_body > avg_body * 1.5:  # Significant expansion move
                # Bullish expansion: preceding red candle is Bullish Order Block
                if df["close"].iloc[i] > df["open"].iloc[i] and df["close"].iloc[i-1] < df["open"].iloc[i-1]:
                    obs.append({
                        "type": "BULLISH_ORDER_BLOCK",
                        "time": str(df.index[i-1]),
                        "zone_high": float(df["high"].iloc[i-1]),
                        "zone_low": float(df["low"].iloc[i-1]),
                        "strength": "HIGH" if candle_body > avg_body * 2 else "MEDIUM"
                    })
                # Bearish expansion: preceding green candle is Bearish Order Block
                elif df["close"].iloc[i] < df["open"].iloc[i] and df["close"].iloc[i-1] > df["open"].iloc[i-1]:
                    obs.append({
                        "type": "BEARISH_ORDER_BLOCK",
                        "time": str(df.index[i-1]),
                        "zone_high": float(df["high"].iloc[i-1]),
                        "zone_low": float(df["low"].iloc[i-1]),
                        "strength": "HIGH" if candle_body > avg_body * 2 else "MEDIUM"
                    })

        return obs[-4:]  # Return most recent 4 Order Blocks

    @staticmethod
    def detect_liquidity_sweep(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detects recent liquidity sweep (Stop-hunt / Turtle soup):
        Price pokes beyond a swing high/low with a long wick and closes back inside.
        """
        if len(df) < 20:
            return None

        recent = df.iloc[-1]
        prior_highs = df["high"].iloc[-20:-1].max()
        prior_lows = df["low"].iloc[-20:-1].min()

        # Bullish Liquidity Sweep (Swept lows and reversed)
        if recent["low"] < prior_lows and recent["close"] > prior_lows:
            return {
                "type": "BULLISH_LIQUIDITY_SWEEP",
                "swept_level": float(prior_lows),
                "wick_low": float(recent["low"]),
                "signal": "REVERSAL_BUY",
                "confidence": 0.85
            }

        # Bearish Liquidity Sweep (Swept highs and rejected)
        if recent["high"] > prior_highs and recent["close"] < prior_highs:
            return {
                "type": "BEARISH_LIQUIDITY_SWEEP",
                "swept_level": float(prior_highs),
                "wick_high": float(recent["high"]),
                "signal": "REVERSAL_SELL",
                "confidence": 0.85
            }

        return None

    @classmethod
    def analyze_smc_structure(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Unified SMC analysis package.
        """
        if df.empty or len(df) < 15:
            return {"bias": "NEUTRAL", "fvgs": [], "order_blocks": [], "sweep": None}

        fvgs = cls.detect_fair_value_gaps(df)
        obs = cls.detect_order_blocks(df)
        sweep = cls.detect_liquidity_sweep(df)

        bullish_ob_count = sum(1 for ob in obs if ob["type"] == "BULLISH_ORDER_BLOCK")
        bearish_ob_count = sum(1 for ob in obs if ob["type"] == "BEARISH_ORDER_BLOCK")

        smc_bias = "NEUTRAL"
        if sweep and sweep.get("signal") == "REVERSAL_BUY":
            smc_bias = "STRONG_BULLISH_REVERSAL"
        elif sweep and sweep.get("signal") == "REVERSAL_SELL":
            smc_bias = "STRONG_BEARISH_REVERSAL"
        elif bullish_ob_count > bearish_ob_count:
            smc_bias = "BULLISH_FLOW"
        elif bearish_ob_count > bullish_ob_count:
            smc_bias = "BEARISH_FLOW"

        return {
            "smc_bias": smc_bias,
            "recent_fvgs": fvgs,
            "order_blocks": obs,
            "liquidity_sweep": sweep
        }
