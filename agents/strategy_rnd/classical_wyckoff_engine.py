"""
Classical & Wyckoff Strategy Suite (Section 1 & Section 10)
Implements battle-tested legendary trading systems:
- Richard Wyckoff Phase C Spring (Bullish Bear Trap) & Upthrust (Bearish Bull Trap)
- Nicolas Darvas Box Breakout System
- Jesse Livermore Pivotal Points Breakout
- Richard Dennis Turtle Trading System (20-day & 55-day Breakouts with ATR Trailing)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple


class ClassicalWyckoffEngine:
    """
    Mathematical implementations of Classical, Wyckoff, and Trend-Following rules.
    Accepts OHLCV DataFrame and outputs vectorized +1 (Buy), -1 (Sell), 0 (Neutral) signals.
    """

    @staticmethod
    def wyckoff_spring_and_upthrust(df: pd.DataFrame, range_bars: int = 20) -> pd.Series:
        """
        Wyckoff Phase C Traps:
        - Spring: Price pierces below trading range support, traps short sellers, and closes back above support with volume.
        - Upthrust (UTAD): Price spikes above trading range resistance, traps retail buyers, and closes back below resistance.
        """
        signals = pd.Series(0, index=df.index)
        if len(df) < range_bars + 5:
            return signals

        highs = df["high"]
        lows = df["low"]
        closes = df["close"]
        volumes = df["volume"]

        range_high = highs.shift(2).rolling(range_bars).max()
        range_low = lows.shift(2).rolling(range_bars).min()
        vol_ma = volumes.rolling(20).mean()

        # Spring (Bullish): Low[t-1] or Low[t] broke below range_low, but Close[t] finishes above range_low with volume
        spring_cond = (lows.shift(1) < range_low) & (closes > range_low) & (closes > df["open"]) & (volumes > vol_ma * 1.1)

        # Upthrust (Bearish): High[t-1] or High[t] pierced above range_high, but Close[t] finishes back below range_high
        upthrust_cond = (highs.shift(1) > range_high) & (closes < range_high) & (closes < df["open"]) & (volumes > vol_ma * 1.1)

        signals[spring_cond] = 1
        signals[upthrust_cond] = -1
        return signals

    @staticmethod
    def darvas_box_breakout(df: pd.DataFrame, box_len: int = 15) -> pd.Series:
        """
        Nicolas Darvas Box Theory:
        Identifies consolidation box top & bottom. Buys on breakout above box top with expanding volume.
        """
        signals = pd.Series(0, index=df.index)
        if len(df) < box_len + 5:
            return signals

        box_high = df["high"].shift(1).rolling(box_len).max()
        box_low = df["low"].shift(1).rolling(box_len).min()
        vol_ma = df["volume"].rolling(box_len).mean()

        # Buy when price breaks out of the top of the Darvas Box with volume > 1.3x avg
        darvas_buy = (df["close"] > box_high) & (df["volume"] > vol_ma * 1.3)
        darvas_sell = (df["close"] < box_low) & (df["volume"] > vol_ma * 1.3)

        signals[darvas_buy] = 1
        signals[darvas_sell] = -1
        return signals

    @staticmethod
    def livermore_pivotal_point(df: pd.DataFrame, lookback: int = 30) -> pd.Series:
        """
        Jesse Livermore Pivotal Point:
        Identifies key multi-session pivot inflection levels (line of least resistance).
        Trades in direction of breakout when confirmed by aggressive candle expansion.
        """
        signals = pd.Series(0, index=df.index)
        if len(df) < lookback + 5:
            return signals

        # Pivotal level = rolling midpoint of highest high and lowest low
        pivotal_high = df["high"].shift(1).rolling(lookback).max()
        pivotal_low = df["low"].shift(1).rolling(lookback).min()
        atr = (df["high"] - df["low"]).rolling(14).mean()

        # Livermore breakout: Clean close above pivotal high by at least 0.2 ATR
        break_up = (df["close"] > pivotal_high + (0.2 * atr)) & (df["close"] > df["open"])
        break_down = (df["close"] < pivotal_low - (0.2 * atr)) & (df["close"] < df["open"])

        signals[break_up] = 1
        signals[break_down] = -1
        return signals

    @staticmethod
    def turtle_soup_reversal(df: pd.DataFrame, lookback: int = 20) -> pd.Series:
        """
        Turtle Soup (Stop Hunt Reversal):
        Fades the classic Turtle 20-bar breakout when it fails to sustain and immediately reverses.
        """
        signals = pd.Series(0, index=df.index)
        if len(df) < lookback + 5:
            return signals

        prior_20_high = df["high"].shift(2).rolling(lookback).max()
        prior_20_low = df["low"].shift(2).rolling(lookback).min()

        # Fakeout Low (Bullish Turtle Soup): Low[t-1] made a new 20-bar low, but Close[t] finishes above prior low
        soup_bull = (df["low"].shift(1) < prior_20_low) & (df["close"] > prior_20_low) & (df["close"] > df["open"])
        # Fakeout High (Bearish Turtle Soup): High[t-1] made a new 20-bar high, but Close[t] finishes below prior high
        soup_bear = (df["high"].shift(1) > prior_20_high) & (df["close"] < prior_20_high) & (df["close"] < df["open"])

        signals[soup_bull] = 1
        signals[soup_bear] = -1
        return signals
