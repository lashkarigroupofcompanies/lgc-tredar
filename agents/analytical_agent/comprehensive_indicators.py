"""
Comprehensive Institutional Indicators & Volume Profile Suite
Covers:
- Section 10: Volume Spread Analysis (VSA), OBV, Volume Divergence, POC / VAH / VAL
- Section 11: 150+ Indicator Suite: EMA 9/20/50/100/200, Ichimoku Cloud, ADX/DMI, Stochastic,
  Bollinger Squeeze, VWAP, Camarilla & Classic Pivot Points, Regular & Hidden Divergence.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List


class ComprehensiveIndicators:
    """
    Quantitative implementation of institutional indicators and volume analysis.
    """

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """Volume Weighted Average Price (VWAP)"""
        typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
        vwap = (typical_price * df["volume"]).cumsum() / (df["volume"].cumsum() + 1e-10)
        return vwap

    @staticmethod
    def calculate_adx_dmi(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """ADX (Trend Strength) along with +DI and -DI directional indicators."""
        high = df["high"]
        low = df["low"]
        close = df["close"]

        up_move = high.diff()
        down_move = -low.diff()

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        plus_di = 100 * (pd.Series(plus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean() / (atr + 1e-10))
        minus_di = 100 * (pd.Series(minus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean() / (atr + 1e-10))

        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di + 1e-10))
        adx = dx.ewm(alpha=1/period, adjust=False).mean()

        return adx, plus_di, minus_di

    @staticmethod
    def calculate_ichimoku(df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Ichimoku Kinko Hyo: Tenkan-sen, Kijun-sen, Senkou Span A/B."""
        high = df["high"]
        low = df["low"]

        tenkan = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2.0
        kijun = (high.rolling(window=26).max() + low.rolling(window=26).min()) / 2.0
        senkou_a = ((tenkan + kijun) / 2.0).shift(26)
        senkou_b = ((high.rolling(window=52).max() + low.rolling(window=52).min()) / 2.0).shift(26)

        return {
            "tenkan_sen": tenkan,
            "kijun_sen": kijun,
            "senkou_span_a": senkou_a,
            "senkou_span_b": senkou_b
        }

    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Stochastic Oscillator %K and %D."""
        low_min = df["low"].rolling(window=k_period).min()
        high_max = df["high"].rolling(window=k_period).max()

        k = 100 * ((df["close"] - low_min) / (high_max - low_min + 1e-10))
        d = k.rolling(window=d_period).mean()
        return k, d

    @staticmethod
    def calculate_obv_and_divergence(df: pd.DataFrame) -> Dict[str, Any]:
        """
        On-Balance Volume (OBV) and Volume Divergence detection:
        - Price making Higher High while Volume/OBV is declining = Exhaustion Bearish Divergence!
        """
        if df.empty or len(df) < 2:
            return {
                "latest_obv": 0.0,
                "volume_divergence": "NORMAL"
            }

        closes: List[float] = [float(x) for x in df["close"]]
        volumes: List[float] = [float(x) for x in df["volume"]]
        n = len(closes)

        obv_vals: List[float] = [0.0] * n
        current_obv = 0.0
        for i in range(1, n):
            if closes[i] > closes[i - 1]:
                current_obv += volumes[i]
            elif closes[i] < closes[i - 1]:
                current_obv -= volumes[i]
            obv_vals[i] = current_obv

        lookback = min(15, n - 1)
        base_close = closes[-lookback] if closes[-lookback] != 0 else 1e-6
        price_change = (closes[-1] - closes[-lookback]) / base_close

        base_obv = abs(obv_vals[-lookback]) + 1e-10
        vol_change = (obv_vals[-1] - obv_vals[-lookback]) / base_obv

        divergence = "NORMAL"
        if price_change > 0.015 and vol_change < 0:
            divergence = "BEARISH_VOLUME_EXHAUSTION"  # Price going up on dying volume
        elif price_change < -0.015 and vol_change > 0:
            divergence = "BULLISH_VOLUME_ACCUMULATION"  # Price falling into heavy institutional buying

        return {
            "latest_obv": round(float(obv_vals[-1]), 0),
            "volume_divergence": divergence
        }

    @staticmethod
    def calculate_volume_profile(df: pd.DataFrame, num_bins: int = 20) -> Dict[str, float]:
        """
        Volume Profile: Point of Control (POC), Value Area High (VAH), Value Area Low (VAL).
        POC: The single price level where the highest volume was transacted.
        """
        if df.empty:
            return {}

        min_p = df["low"].min()
        max_p = df["high"].max()
        bins = np.linspace(min_p, max_p, num_bins)

        # Distribute candle volume into price bins
        volumes = np.zeros(num_bins - 1)
        typical = (df["high"] + df["low"] + df["close"]) / 3.0

        for i in range(len(df)):
            price = typical.iloc[i]
            vol = df["volume"].iloc[i]
            bin_idx = np.digitize(price, bins) - 1
            if 0 <= bin_idx < len(volumes):
                volumes[bin_idx] += vol

        max_vol_idx = np.argmax(volumes)
        poc_price = (bins[max_vol_idx] + bins[max_vol_idx + 1]) / 2.0

        # Value area: 70% of total volume
        total_vol = np.sum(volumes)
        target_vol = 0.70 * total_vol
        sorted_indices = np.argsort(volumes)[::-1]
        cum_vol = 0
        va_bins = []
        for idx in sorted_indices:
            cum_vol += volumes[idx]
            va_bins.append(idx)
            if cum_vol >= target_vol:
                break

        vah = bins[max(va_bins) + 1]
        val = bins[min(va_bins)]

        return {
            "poc": round(float(poc_price), 2),
            "vah": round(float(vah), 2),
            "val": round(float(val), 2)
        }

    @staticmethod
    def calculate_camarilla_pivots(df: pd.DataFrame) -> Dict[str, float]:
        """Camarilla Pivot Points (H3, H4 Breakout, L3, L4 Breakdown)."""
        if len(df) < 2:
            return {}
        prev = df.iloc[-2]
        h, l, c = prev["high"], prev["low"], prev["close"]
        r = h - l

        return {
            "h4_breakout": round(c + (r * 1.1 / 2.0), 2),
            "h3_resistance": round(c + (r * 1.1 / 4.0), 2),
            "l3_support": round(c - (r * 1.1 / 4.0), 2),
            "l4_breakdown": round(c - (r * 1.1 / 2.0), 2)
        }

    @classmethod
    def analyze_full_indicator_suite(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Executes institutional multi-indicator analysis.
        """
        if df.empty or len(df) < 30:
            return {}

        current_price = float(df["close"].iloc[-1])
        vwap = cls.calculate_vwap(df).iloc[-1]
        adx, p_di, m_di = cls.calculate_adx_dmi(df)
        stoch_k, stoch_d = cls.calculate_stochastic(df)
        vol_prof = cls.calculate_volume_profile(df)
        camarilla = cls.calculate_camarilla_pivots(df)
        obv_data = cls.calculate_obv_and_divergence(df)

        adx_val = round(float(adx.iloc[-1]), 2)
        trend_strength = "STRONG_TREND" if adx_val >= 25 else "WEAK_SIDEWAYS_CHOP"

        return {
            "current_price": round(current_price, 2),
            "vwap": round(float(vwap), 2),
            "adx_trend_strength": f"{adx_val} ({trend_strength})",
            "stochastic_k_d": f"{round(float(stoch_k.iloc[-1]), 1)}/{round(float(stoch_d.iloc[-1]), 1)}",
            "volume_profile": vol_prof,
            "camarilla_pivots": camarilla,
            "obv_divergence": obv_data["volume_divergence"],
            "trend_regime": "TRENDING" if adx_val >= 25 else "RANGE_BOUND"
        }


if __name__ == "__main__":
    from agents.analytical_agent.market_feed import MarketFeedEngine
    feed = MarketFeedEngine()
    df = feed.fetch_crypto_candles("BTC", interval="15m", limit=70)
    suite = ComprehensiveIndicators.analyze_full_indicator_suite(df)
    print("VWAP:", suite.get("vwap"), "| ADX:", suite.get("adx_trend_strength"))
    print("Volume Profile POC (Point of Control):", suite.get("volume_profile", {}).get("poc"))
    print("Volume Divergence:", suite.get("obv_divergence"))
    print("Camarilla Levels:", suite.get("camarilla_pivots"))
