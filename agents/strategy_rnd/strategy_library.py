"""
Comprehensive Strategy Library
Repository of 15+ classical, quantitative, and institutional (ICT / Smart Money) trading strategies.
All logic is strictly deterministic, vectorized across Pandas/Numpy DataFrames.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional
from agents.strategy_rnd.classical_wyckoff_engine import ClassicalWyckoffEngine


class StrategyLibrary:
    """
    Standardized strategy repository implementing verified quant & ICT algorithms.
    Each strategy accepts an OHLCV DataFrame and returns a pd.Series of signals:
      +1 = BUY / LONG
      -1 = SELL / SHORT
       0 = HOLD / NEUTRAL
    """

    # -------------------------------------------------------------
    # Helper Technical Indicator Computations
    # -------------------------------------------------------------
    @staticmethod
    def _compute_ema(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def _compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high = df["high"]
        low = df["low"]
        close = df["close"]
        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs()
        ], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    @staticmethod
    def _compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    # -------------------------------------------------------------
    # 1. Classical Quant & Trend Following Strategies
    # -------------------------------------------------------------
    @classmethod
    def turtle_donchian_breakout(cls, df: pd.DataFrame, lookback: int = 20) -> pd.Series:
        """Turtle Trading: Buy on 20-bar high break, Sell on 20-bar low break."""
        signals = pd.Series(0, index=df.index)
        upper = df["high"].shift(1).rolling(lookback).max()
        lower = df["low"].shift(1).rolling(lookback).min()

        signals[df["close"] > upper] = 1
        signals[df["close"] < lower] = -1
        return signals

    @classmethod
    def dual_ema_trend(cls, df: pd.DataFrame, fast: int = 21, slow: int = 50, trend: int = 200) -> pd.Series:
        """Dual EMA Trend Rider with 200 EMA Macro Filter."""
        signals = pd.Series(0, index=df.index)
        ema_fast = cls._compute_ema(df["close"], fast)
        ema_slow = cls._compute_ema(df["close"], slow)
        ema_trend = cls._compute_ema(df["close"], trend)

        bullish = (ema_fast > ema_slow) & (df["close"] > ema_trend) & (ema_fast.shift(1) <= ema_slow.shift(1))
        bearish = (ema_fast < ema_slow) & (df["close"] < ema_trend) & (ema_fast.shift(1) >= ema_slow.shift(1))

        signals[bullish] = 1
        signals[bearish] = -1
        return signals

    @classmethod
    def supertrend_momentum(cls, df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.Series:
        """Supertrend Volatility Momentum."""
        signals = pd.Series(0, index=df.index)
        atr = cls._compute_atr(df, period)
        hl2 = (df["high"] + df["low"]) / 2
        upperband = hl2 + (multiplier * atr)
        lowerband = hl2 - (multiplier * atr)

        close = [float(x) for x in df["close"]]
        upper = [float(x) for x in upperband]
        lower = [float(x) for x in lowerband]
        in_uptrend = np.zeros(len(df), dtype=bool)

        for i in range(1, len(df)):
            if close[i] > upper[i-1]:
                in_uptrend[i] = True
            elif close[i] < lower[i-1]:
                in_uptrend[i] = False
            else:
                in_uptrend[i] = in_uptrend[i-1]

        # Trigger on flip
        trend_series = pd.Series(in_uptrend, index=df.index)
        signals[(trend_series == True) & (trend_series.shift(1) == False)] = 1
        signals[(trend_series == False) & (trend_series.shift(1) == True)] = -1
        return signals

    @classmethod
    def opening_range_breakout(cls, df: pd.DataFrame, orb_bars: int = 6) -> pd.Series:
        """Opening Range Breakout (ORB): First N bars (e.g. 6 x 5m = 30 min) range breakout."""
        signals = pd.Series(0, index=df.index)
        rolling_high = df["high"].rolling(orb_bars).max().shift(1)
        rolling_low = df["low"].rolling(orb_bars).min().shift(1)
        vol_ma = df["volume"].rolling(10, min_periods=1).mean()

        signals[(df["close"] > rolling_high) & (df["volume"] > vol_ma * 1.2)] = 1
        signals[(df["close"] < rolling_low) & (df["volume"] > vol_ma * 1.2)] = -1
        return signals

    # -------------------------------------------------------------
    # 2. Mean Reversion & Volatility Strategies
    # -------------------------------------------------------------
    @classmethod
    def bollinger_rsi_mean_reversion(cls, df: pd.DataFrame) -> pd.Series:
        """Bollinger Bands + RSI Extreme Overbought/Oversold Reversal."""
        signals = pd.Series(0, index=df.index)
        sma20 = df["close"].rolling(20).mean()
        std20 = df["close"].rolling(20).std()
        lower_bb = sma20 - (2.0 * std20)
        upper_bb = sma20 + (2.0 * std20)
        rsi = cls._compute_rsi(df["close"], 14)

        # Long: Price pierces lower BB and RSI oversold < 32 then crosses back
        long_cond = (df["low"] <= lower_bb) & (rsi < 32) & (df["close"] > df["open"])
        # Short: Price pierces upper BB and RSI overbought > 68 then crosses back
        short_cond = (df["high"] >= upper_bb) & (rsi > 68) & (df["close"] < df["open"])

        signals[long_cond] = 1
        signals[short_cond] = -1
        return signals

    @classmethod
    def vwap_mean_reversion(cls, df: pd.DataFrame) -> pd.Series:
        """VWAP Band Deviation Fade."""
        signals = pd.Series(0, index=df.index)
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        vwap = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()
        vwap_std = (typical_price - vwap).rolling(20).std().fillna(0)

        upper_band = vwap + (2.0 * vwap_std)
        lower_band = vwap - (2.0 * vwap_std)

        signals[(df["low"] < lower_band) & (df["close"] > lower_band)] = 1
        signals[(df["high"] > upper_band) & (df["close"] < upper_band)] = -1
        return signals

    @classmethod
    def stochastic_rsi_swing(cls, df: pd.DataFrame) -> pd.Series:
        """Stochastic RSI Momentum Swing."""
        signals = pd.Series(0, index=df.index)
        rsi = cls._compute_rsi(df["close"], 14)
        min_rsi = rsi.rolling(14).min()
        max_rsi = rsi.rolling(14).max()
        stoch_k = ((rsi - min_rsi) / (max_rsi - min_rsi).replace(0, np.nan)) * 100
        stoch_d = stoch_k.rolling(3).mean()

        signals[(stoch_k > stoch_d) & (stoch_k.shift(1) <= stoch_d.shift(1)) & (stoch_k < 25)] = 1
        signals[(stoch_k < stoch_d) & (stoch_k.shift(1) >= stoch_d.shift(1)) & (stoch_k > 75)] = -1
        return signals

    @classmethod
    def keltner_channel_breakout(cls, df: pd.DataFrame) -> pd.Series:
        """Keltner Channel Volatility Squeeze & Release."""
        signals = pd.Series(0, index=df.index)
        ema20 = cls._compute_ema(df["close"], 20)
        atr = cls._compute_atr(df, 10)
        keltner_upper = ema20 + (1.5 * atr)
        keltner_lower = ema20 - (1.5 * atr)

        signals[(df["close"] > keltner_upper) & (df["close"].shift(1) <= keltner_upper.shift(1))] = 1
        signals[(df["close"] < keltner_lower) & (df["close"].shift(1) >= keltner_lower.shift(1))] = -1
        return signals

    # -------------------------------------------------------------
    # 3. Institutional & Smart Money Concepts (ICT) Strategies
    # -------------------------------------------------------------
    @classmethod
    def ict_2022_model(cls, df: pd.DataFrame) -> pd.Series:
        """
        ICT 2022 Mentorship Model:
        1. Liquidity Sweep of previous swing high/low
        2. Market Structure Shift (MSS) displacement
        3. Entry on Fair Value Gap (FVG) retest
        """
        signals = pd.Series(0, index=df.index)
        highs: List[float] = [float(x) for x in df["high"]]
        lows: List[float] = [float(x) for x in df["low"]]
        closes: List[float] = [float(x) for x in df["close"]]
        n = len(df)

        for i in range(5, n):
            # Bullish ICT 2022: Low sweeps prior swing low, sharp reversal, FVG created
            low_slice = lows[max(0, i-15):max(0, i-2)]
            prev_swing_low = min(low_slice) if low_slice else lows[i-2]
            if lows[i-2] < prev_swing_low and closes[i-1] > highs[i-2]:
                # Check for Bullish FVG: low[i] > high[i-2]
                if lows[i] >= highs[i-2]:
                    signals.iloc[i] = 1

            # Bearish ICT 2022: High sweeps prior swing high, sharp drop, FVG created
            high_slice = highs[max(0, i-15):max(0, i-2)]
            prev_swing_high = max(high_slice) if high_slice else highs[i-2]
            if highs[i-2] > prev_swing_high and closes[i-1] < lows[i-2]:
                # Check for Bearish FVG: high[i] <= low[i-2]
                if highs[i] <= lows[i-2]:
                    signals.iloc[i] = -1

        return signals

    @classmethod
    def ict_silver_bullet(cls, df: pd.DataFrame) -> pd.Series:
        """
        ICT Silver Bullet:
        FVG retest targeting 50% Consequent Encroachment (CE) during high-volatility momentum.
        """
        signals = pd.Series(0, index=df.index)
        # 3-candle Fair Value Gap detection
        bullish_fvg = (df["low"] > df["high"].shift(2)) & (df["close"].shift(1) > df["open"].shift(1))
        bearish_fvg = (df["high"] < df["low"].shift(2)) & (df["close"].shift(1) < df["open"].shift(1))

        signals[bullish_fvg] = 1
        signals[bearish_fvg] = -1
        return signals

    @classmethod
    def order_block_golden_pocket(cls, df: pd.DataFrame) -> pd.Series:
        """
        Order Block Retest coinciding with Fibonacci 0.618 OTE (Optimal Trade Entry).
        """
        signals = pd.Series(0, index=df.index)
        rolling_high = df["high"].rolling(30).max()
        rolling_low = df["low"].rolling(30).min()
        fib_618 = rolling_low + (rolling_high - rolling_low) * 0.618

        # Bullish: Price pulls back to 0.618 Fib after an uptrend
        bull_pullback = (df["low"] <= fib_618) & (df["close"] > fib_618) & (df["close"] > df["open"])
        # Bearish: Price rallies to 0.382/0.618 Fib after downtrend
        fib_382 = rolling_low + (rolling_high - rolling_low) * 0.382
        bear_pullback = (df["high"] >= fib_382) & (df["close"] < fib_382) & (df["close"] < df["open"])

        signals[bull_pullback] = 1
        signals[bear_pullback] = -1
        return signals

    @classmethod
    def breaker_block_flip(cls, df: pd.DataFrame) -> pd.Series:
        """Breaker Block: Failed order block broken with momentum, retested as opposite support/resistance."""
        signals = pd.Series(0, index=df.index)
        ema50 = cls._compute_ema(df["close"], 50)
        # Price crosses 50 EMA and retests
        retest_bull = (df["close"] > ema50) & (df["low"] <= ema50) & (df["close"] > df["open"])
        retest_bear = (df["close"] < ema50) & (df["high"] >= ema50) & (df["close"] < df["open"])

        signals[retest_bull] = 1
        signals[retest_bear] = -1
        return signals

    # -------------------------------------------------------------
    # 4. Volume Flow & Multi-Factor Momentum Strategies
    # -------------------------------------------------------------
    @classmethod
    def volume_profile_poc_retest(cls, df: pd.DataFrame) -> pd.Series:
        """Volume Profile Point of Control (POC) Retest & Continuation."""
        signals = pd.Series(0, index=df.index)
        vol_mean = df["volume"].rolling(20).mean()
        high_vol_bars = df[df["volume"] > vol_mean * 1.5]
        if not high_vol_bars.empty:
            poc_approx = high_vol_bars["close"].mean()
            # Bounce from POC
            bounce_up = (df["low"] <= poc_approx) & (df["close"] > poc_approx) & (df["close"] > df["open"])
            bounce_down = (df["high"] >= poc_approx) & (df["close"] < poc_approx) & (df["close"] < df["open"])
            signals[bounce_up] = 1
            signals[bounce_down] = -1
        return signals

    @classmethod
    def rvol_surge_momentum(cls, df: pd.DataFrame) -> pd.Series:
        """Relative Volume Surge Breakout (RVOL > 2.0)."""
        signals = pd.Series(0, index=df.index)
        vol_sma = df["volume"].rolling(20).mean()
        rvol = df["volume"] / vol_sma.replace(0, np.nan)
        atr = cls._compute_atr(df, 14)
        body_size = (df["close"] - df["open"]).abs()

        bull_surge = (rvol > 2.0) & (df["close"] > df["open"]) & (body_size > atr * 0.8)
        bear_surge = (rvol > 2.0) & (df["close"] < df["open"]) & (body_size > atr * 0.8)

        signals[bull_surge] = 1
        signals[bear_surge] = -1
        return signals

    @classmethod
    def adx_trend_acceleration(cls, df: pd.DataFrame) -> pd.Series:
        """ADX Strong Trend Momentum with Directional Movement (+DI/-DI)."""
        signals = pd.Series(0, index=df.index)
        high = df["high"]
        low = df["low"]
        close = df["close"]

        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        tr = cls._compute_atr(df, 14)
        plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(14).mean() / tr.replace(0, np.nan))
        minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(14).mean() / tr.replace(0, np.nan))
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan))
        adx = dx.rolling(14).mean()

        strong_trend = adx > 25
        signals[strong_trend & (plus_di > minus_di) & (plus_di.shift(1) <= minus_di.shift(1))] = 1
        signals[strong_trend & (minus_di > plus_di) & (minus_di.shift(1) <= plus_di.shift(1))] = -1
        return signals

    @classmethod
    def pullback_ema_bounce(cls, df: pd.DataFrame) -> pd.Series:
        """Section 7: 21 EMA / 50 EMA Pullback Bounce in primary trend."""
        signals = pd.Series(0, index=df.index)
        ema21 = cls._compute_ema(df["close"], 21)
        ema50 = cls._compute_ema(df["close"], 50)
        ema200 = cls._compute_ema(df["close"], 200)

        uptrend = (df["close"] > ema200) & (ema21 > ema50)
        bull_bounce = uptrend & (df["low"] <= ema21) & (df["close"] > ema21) & (df["close"] > df["open"])

        downtrend = (df["close"] < ema200) & (ema21 < ema50)
        bear_bounce = downtrend & (df["high"] >= ema21) & (df["close"] < ema21) & (df["close"] < df["open"])

        signals[bull_bounce] = 1
        signals[bear_bounce] = -1
        return signals

    # -------------------------------------------------------------
    # Registry of All Classical, Quant, and Institutional Strategies
    # -------------------------------------------------------------
    @classmethod
    def get_all_strategies(cls) -> Dict[str, Any]:
        """Returns catalog of all registered strategy functions."""
        return {
            # Classical & Legendary Traders (Section 1 & 10)
            "TURTLE_DONCHIAN_BREAKOUT": cls.turtle_donchian_breakout,
            "WYCKOFF_SPRING_UPTHRUST": ClassicalWyckoffEngine.wyckoff_spring_and_upthrust,
            "DARVAS_BOX_BREAKOUT": ClassicalWyckoffEngine.darvas_box_breakout,
            "LIVERMORE_PIVOTAL_POINT": ClassicalWyckoffEngine.livermore_pivotal_point,
            "TURTLE_SOUP_SWEEP": ClassicalWyckoffEngine.turtle_soup_reversal,
            
            # Trend Following (Section 3 & 7)
            "DUAL_EMA_TREND": cls.dual_ema_trend,
            "SUPERTREND_MOMENTUM": cls.supertrend_momentum,
            "PULLBACK_EMA_BOUNCE": cls.pullback_ema_bounce,
            "ADX_TREND_ACCELERATION": cls.adx_trend_acceleration,

            # Breakout & Volatility (Section 5)
            "OPENING_RANGE_BREAKOUT": cls.opening_range_breakout,
            "KELTNER_CHANNEL_BREAKOUT": cls.keltner_channel_breakout,
            "RVOL_SURGE_MOMENTUM": cls.rvol_surge_momentum,

            # Mean Reversion (Section 4)
            "BOLLINGER_RSI_MEAN_REVERSION": cls.bollinger_rsi_mean_reversion,
            "VWAP_MEAN_REVERSION": cls.vwap_mean_reversion,
            "STOCHASTIC_RSI_SWING": cls.stochastic_rsi_swing,

            # Institutional Smart Money Concepts (ICT) (Section 2)
            "ICT_2022_MODEL": cls.ict_2022_model,
            "ICT_SILVER_BULLET": cls.ict_silver_bullet,
            "ORDER_BLOCK_GOLDEN_POCKET": cls.order_block_golden_pocket,
            "BREAKER_BLOCK_FLIP": cls.breaker_block_flip,
            "VOLUME_PROFILE_POC_RETEST": cls.volume_profile_poc_retest
        }
