"""
Technical Indicators & Quant Signal Calculation Engine
Fused from TradingView-TA, pandas-ta, and Wall Street Quantitative indicator libraries.
Calculates EMA (9, 21, 50, 200), RSI, MACD, Bollinger Bands, Supertrend, ATR, and Dynamic Pivot Zones.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple


class TechnicalIndicators:
    """
    Calculates institutional indicators with high-speed vectorized Pandas/Numpy operations.
    """

    @staticmethod
    def calculate_ema(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        sma = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high = df["high"]
        low = df["low"]
        close = df["close"]
        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return true_range.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    @staticmethod
    def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> Tuple[pd.Series, pd.Series]:
        """
        TradingView standard Supertrend implementation.
        """
        hl2 = (df["high"] + df["low"]) / 2
        atr = TechnicalIndicators.calculate_atr(df, period)
        
        upper_basic = hl2 + (multiplier * atr)
        lower_basic = hl2 - (multiplier * atr)
        
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)
        
        upper_band = upper_basic.copy()
        lower_band = lower_basic.copy()
        
        close = df["close"].values
        u_band = upper_band.values
        l_band = lower_band.values
        st = np.zeros(len(df))
        dir_arr = np.zeros(len(df))
        
        for i in range(1, len(df)):
            if close[i-1] > l_band[i-1]:
                l_band[i] = max(lower_basic.iloc[i], l_band[i-1])
            else:
                l_band[i] = lower_basic.iloc[i]
                
            if close[i-1] < u_band[i-1]:
                u_band[i] = min(upper_basic.iloc[i], u_band[i-1])
            else:
                u_band[i] = upper_basic.iloc[i]
                
            if close[i] > u_band[i-1]:
                dir_arr[i] = 1
            elif close[i] < l_band[i-1]:
                dir_arr[i] = -1
            else:
                dir_arr[i] = dir_arr[i-1]
                if dir_arr[i] == 1 and l_band[i] < l_band[i-1]:
                    l_band[i] = l_band[i-1]
                if dir_arr[i] == -1 and u_band[i] > u_band[i-1]:
                    u_band[i] = u_band[i-1]
                    
            st[i] = l_band[i] if dir_arr[i] == 1 else u_band[i]
            
        return pd.Series(st, index=df.index), pd.Series(dir_arr, index=df.index)

    @classmethod
    def enrich_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes the complete suite of technical indicators onto the DataFrame.
        """
        if df.empty or len(df) < 30:
            return df

        df = df.copy()
        close = df["close"]

        # EMAs
        df["ema_9"] = cls.calculate_ema(close, 9)
        df["ema_21"] = cls.calculate_ema(close, 21)
        df["ema_50"] = cls.calculate_ema(close, 50)
        df["ema_200"] = cls.calculate_ema(close, 200)

        # RSI
        df["rsi"] = cls.calculate_rsi(close, 14)

        # MACD
        macd, signal, hist = cls.calculate_macd(close)
        df["macd"] = macd
        df["macd_signal"] = signal
        df["macd_hist"] = hist

        # Bollinger Bands
        upper, mid, lower = cls.calculate_bollinger_bands(close)
        df["bb_upper"] = upper
        df["bb_mid"] = mid
        df["bb_lower"] = lower

        # ATR
        df["atr"] = cls.calculate_atr(df, 14)

        # Supertrend
        st, st_dir = cls.calculate_supertrend(df)
        df["supertrend"] = st
        df["supertrend_dir"] = st_dir  # 1 = Bullish, -1 = Bearish

        # Dynamic Support & Resistance (Pivots)
        df["swing_high"] = df["high"].rolling(window=10, center=True).max()
        df["swing_low"] = df["low"].rolling(window=10, center=True).min()

        return df

    @classmethod
    def get_latest_indicators(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extracts clean indicator snapshot from the latest candle.
        """
        if df.empty:
            return {}

        enriched = cls.enrich_dataframe(df)
        latest = enriched.iloc[-1]
        prev = enriched.iloc[-2] if len(enriched) > 1 else latest

        current_price = float(latest["close"])
        ema_9 = float(latest.get("ema_9", current_price))
        ema_21 = float(latest.get("ema_21", current_price))
        ema_200 = float(latest.get("ema_200", current_price))
        rsi = float(latest.get("rsi", 50.0))
        st_dir = int(latest.get("supertrend_dir", 1))
        macd_hist = float(latest.get("macd_hist", 0.0))
        atr = float(latest.get("atr", current_price * 0.01))

        # Check Crossovers
        ema_cross_bullish = (prev["ema_9"] <= prev["ema_21"]) and (ema_9 > ema_21)
        ema_cross_bearish = (prev["ema_9"] >= prev["ema_21"]) and (ema_9 < ema_21)

        # Overall Indicator Verdict
        bullish_votes = 0
        bearish_votes = 0

        if ema_9 > ema_21: bullish_votes += 1
        else: bearish_votes += 1

        if current_price > ema_200: bullish_votes += 1
        else: bearish_votes += 1

        if st_dir == 1: bullish_votes += 1
        else: bearish_votes += 1

        if macd_hist > 0: bullish_votes += 1
        else: bearish_votes += 1

        if 45 <= rsi <= 68: bullish_votes += 1
        elif rsi < 40: bearish_votes += 1

        return {
            "price": current_price,
            "ema_9": round(ema_9, 2),
            "ema_21": round(ema_21, 2),
            "ema_200": round(ema_200, 2),
            "rsi": round(rsi, 2),
            "supertrend": "BULLISH" if st_dir == 1 else "BEARISH",
            "macd_hist": round(macd_hist, 4),
            "atr": round(atr, 2),
            "ema_cross_signal": "BULLISH_CROSS" if ema_cross_bullish else ("BEARISH_CROSS" if ema_cross_bearish else "NONE"),
            "indicator_bias": "STRONG_BUY" if bullish_votes >= 4 else ("STRONG_SELL" if bearish_votes >= 4 else "NEUTRAL"),
            "bullish_strength": f"{bullish_votes}/5",
            "bearish_strength": f"{bearish_votes}/5"
        }
