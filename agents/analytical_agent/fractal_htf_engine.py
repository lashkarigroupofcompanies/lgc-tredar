"""
Fractal Multi-Timeframe (HTF) Trend Lock & TTM Volatility Squeeze Engine
Inspired by John Carter's TTM Squeeze, Larry Williams Volatility Breakout,
and institutional multi-timeframe fractal alignment (15m -> 1H -> 4H).

Enforces:
1. HTF Trend Anchor: Never fight the 4H/1H institutional tide. Counter-trend trades are vetoed or throttled.
2. TTM Squeeze Coiled Spring: Detects Bollinger Band contraction inside Keltner Channels (Zero chop trades).
3. Squeeze Expansion Impulse: Detects when the spring uncoils for 3% to 5% conviction breakout entries.
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger("FractalHTFEngine")


class FractalHTFEngine:
    """
    Multi-Timeframe Fractal Confluence & Volatility Squeeze Engine.
    Ensures trade setups align with higher-timeframe order flow and volatility cycles.
    """

    @classmethod
    def calculate_ema(cls, series: List[float], period: int) -> List[float]:
        if not series:
            return []
        alpha = 2.0 / (period + 1.0)
        ema = [series[0]]
        for val in series[1:]:
            ema.append((val * alpha) + (ema[-1] * (1.0 - alpha)))
        return ema

    @classmethod
    def analyze_htf_structure(
        cls,
        df_htf: pd.DataFrame,
        timeframe_label: str = "4h"
    ) -> Dict[str, Any]:
        """
        Analyzes 4H / 1H Higher Timeframe Market Structure.
        Computes 50 EMA, 200 EMA, and structural swings.
        """
        if df_htf.empty or len(df_htf) < 25:
            return {
                "timeframe": timeframe_label,
                "trend": "UNKNOWN",
                "bias": "NEUTRAL",
                "ema_200": 0.0,
                "ema_50": 0.0,
                "structure_clear": False,
                "details": "Insufficient HTF candles."
            }

        closes: List[float] = [float(x) for x in df_htf["close"]]
        highs: List[float] = [float(x) for x in df_htf["high"]]
        lows: List[float] = [float(x) for x in df_htf["low"]]
        current_close = closes[-1]

        # EMAs
        ema_50_series = cls.calculate_ema(closes, min(50, len(closes)))
        ema_200_series = cls.calculate_ema(closes, min(200, len(closes)))

        ema_50 = ema_50_series[-1]
        ema_200 = ema_200_series[-1]

        # Recent 20-period swing structure
        recent_highs = highs[-20:]
        recent_lows = lows[-20:]
        htf_swing_high = max(recent_highs)
        htf_swing_low = min(recent_lows)

        # Trend classification
        if current_close > ema_50 and ema_50 >= ema_200:
            trend = "STRONG_BULLISH"
            bias = "BULLISH"
        elif current_close > ema_200:
            trend = "MODERATE_BULLISH"
            bias = "BULLISH"
        elif current_close < ema_50 and ema_50 <= ema_200:
            trend = "STRONG_BEARISH"
            bias = "BEARISH"
        elif current_close < ema_200:
            trend = "MODERATE_BEARISH"
            bias = "BEARISH"
        else:
            trend = "RANGING_NEUTRAL"
            bias = "NEUTRAL"

        return {
            "timeframe": timeframe_label,
            "trend": trend,
            "bias": bias,
            "current_close": round(current_close, 2),
            "ema_50": round(ema_50, 2),
            "ema_200": round(ema_200, 2),
            "htf_swing_high": round(htf_swing_high, 2),
            "htf_swing_low": round(htf_swing_low, 2),
            "structure_clear": True,
            "details": f"HTF ({timeframe_label}) is {trend} | Price: {current_close} vs 200 EMA: {ema_200:.2f}"
        }

    @classmethod
    def detect_ttm_volatility_squeeze(
        cls,
        df: pd.DataFrame,
        length: int = 20,
        bb_std: float = 2.0,
        kc_mult: float = 1.5
    ) -> Dict[str, Any]:
        """
        TTM Volatility Squeeze Engine:
        Bollinger Bands vs Keltner Channels contraction and expansion.
        - SQUEEZE_ON: Bollinger Bands contract INSIDE Keltner Channels (Coiled Spring / Chop).
        - SQUEEZE_FIRED: Bands breakout outside Channels with momentum thrust (Prime Entry).
        - NO_SQUEEZE: Normal uncompressed market.
        """
        if df.empty or len(df) < length + 5:
            return {
                "squeeze_status": "NORMAL",
                "coiled_spring": False,
                "fired_expansion": False,
                "momentum": 0.0,
                "details": "Insufficient data for squeeze calculation."
            }

        closes: List[float] = [float(x) for x in df["close"]]
        highs: List[float] = [float(x) for x in df["high"]]
        lows: List[float] = [float(x) for x in df["low"]]
        n = len(df)

        # 1. 20-period SMA & Bollinger Bands
        sma_20 = sum(closes[-length:]) / length
        variance = sum((x - sma_20) ** 2 for x in closes[-length:]) / length
        std_dev = max(1e-6, np.sqrt(variance))

        bb_upper = sma_20 + (bb_std * std_dev)
        bb_lower = sma_20 - (bb_std * std_dev)

        # 2. 20-period ATR & Keltner Channels
        tr_list = []
        for i in range(max(1, n - length), n):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1])
            )
            tr_list.append(tr)
        atr = sum(tr_list) / max(1, len(tr_list)) if tr_list else 1.0

        kc_upper = sma_20 + (kc_mult * atr)
        kc_lower = sma_20 - (kc_mult * atr)

        # 3. Check Current & Previous Squeeze States
        is_squeeze_current = (bb_upper <= kc_upper) and (bb_lower >= kc_lower)

        # Previous bar squeeze state
        prev_closes = closes[-length-1:-1]
        prev_sma = sum(prev_closes) / length
        prev_var = sum((x - prev_sma) ** 2 for x in prev_closes) / length
        prev_std = max(1e-6, np.sqrt(prev_var))
        prev_bb_upper = prev_sma + (bb_std * prev_std)
        prev_bb_lower = prev_sma - (bb_std * prev_std)
        prev_kc_upper = prev_sma + (kc_mult * atr)
        prev_kc_lower = prev_sma - (kc_mult * atr)
        is_squeeze_prev = (prev_bb_upper <= prev_kc_upper) and (prev_bb_lower >= prev_kc_lower)

        # 4. Squeeze Momentum Calculation (Linear regression proxy)
        highest_20 = max(highs[-length:])
        lowest_20 = min(lows[-length:])
        mid_val = ((highest_20 + lowest_20) / 2.0 + sma_20) / 2.0
        momentum = closes[-1] - mid_val

        # Classify Squeeze
        if is_squeeze_current:
            status = "SQUEEZE_ON_COILED_SPRING"
            coiled = True
            fired = False
            details = "Bollinger Bands compressed tightly inside Keltner Channel. Market coiling like a spring."
        elif is_squeeze_prev and not is_squeeze_current:
            status = "SQUEEZE_FIRED_MOMENTUM_EXPLOSION"
            coiled = False
            fired = True
            details = f"Squeeze unleashed! Bands expanding rapidly. Momentum: {momentum:+.2f}."
        else:
            status = "NO_SQUEEZE_NORMAL_EXPANSION"
            coiled = False
            fired = False
            details = "Normal volatility conditions."

        return {
            "squeeze_status": status,
            "coiled_spring": coiled,
            "fired_expansion": fired,
            "momentum": round(momentum, 2),
            "momentum_direction": "BULLISH" if momentum > 0 else "BEARISH",
            "bb_bandwidth": round((bb_upper - bb_lower) / max(1e-6, sma_20) * 100.0, 2),
            "details": details
        }

    @classmethod
    def evaluate_fractal_alignment(
        cls,
        df_primary: pd.DataFrame,
        df_htf: Optional[pd.DataFrame],
        proposed_direction: str
    ) -> Dict[str, Any]:
        """
        Master Fractal Alignment Function:
        Validates whether the proposed intraday trade aligns with 4H/1H structure
        and assesses the Volatility Squeeze status.
        """
        htf_analysis = cls.analyze_htf_structure(df_htf if df_htf is not None else pd.DataFrame())
        squeeze_analysis = cls.detect_ttm_volatility_squeeze(df_primary)

        clean_dir = proposed_direction.upper()
        htf_bias = htf_analysis.get("bias", "NEUTRAL")

        # 1. Check HTF Trend Collision
        htf_collision = False
        veto_reason = ""

        if htf_analysis.get("structure_clear"):
            if clean_dir == "LONG" and htf_analysis.get("trend") == "STRONG_BEARISH":
                htf_collision = True
                veto_reason = f"HTF_TREND_COLLISION: Proposing LONG into an institutional 4H STRONG_BEARISH trend (Below 200 EMA at ${htf_analysis['ema_200']:,.2f})."
            elif clean_dir == "SHORT" and htf_analysis.get("trend") == "STRONG_BULLISH":
                htf_collision = True
                veto_reason = f"HTF_TREND_COLLISION: Proposing SHORT into an institutional 4H STRONG_BULLISH trend (Above 200 EMA at ${htf_analysis['ema_200']:,.2f})."

        # 2. Check Volatility Squeeze State
        # If market is dead-coiled in a squeeze, advise caution/patience
        # If squeeze just fired in the direction of the trade, grant HIGH CONVICTION BOOST!
        conviction_boost = False
        if squeeze_analysis.get("fired_expansion"):
            if clean_dir == "LONG" and squeeze_analysis.get("momentum_direction") == "BULLISH":
                conviction_boost = True
            elif clean_dir == "SHORT" and squeeze_analysis.get("momentum_direction") == "BEARISH":
                conviction_boost = True

        return {
            "htf_aligned": not htf_collision,
            "htf_collision": htf_collision,
            "veto_reason": veto_reason,
            "conviction_boost": conviction_boost,
            "htf_structure": htf_analysis,
            "volatility_squeeze": squeeze_analysis,
            "recommended_action": "VETO_TRADE" if htf_collision else ("BOOST_CONVICTION_SIZING" if conviction_boost else "STANDARD_EXECUTION")
        }
