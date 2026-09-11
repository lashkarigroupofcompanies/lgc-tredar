"""
Institutional Key Levels, Supply & Demand Zones, and Fibonacci OTE Engine
Covers:
- Section 3: Support & Resistance (Horizontal, Virgin S&R, PDH/PDL, PWH/PWL)
- Section 4: Supply & Demand Zones (RBD, DBR, DBD, RBR, Proximal/Distal lines)
- Section 7: Fibonacci Retracement (0.382, 0.5, 0.618 Golden Ratio, 0.786 OTE), Extensions (1.272, 1.618)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple


class KeyLevelsAndFibEngine:
    """
    Computes institutional key price levels, nested supply/demand zones, and Fibonacci OTE zones.
    """

    @staticmethod
    def calculate_fibonacci_levels(swing_low: float, swing_high: float, is_uptrend: bool = True) -> Dict[str, float]:
        """
        Calculates institutional Fibonacci retracement and extension levels.
        OTE (Optimal Trade Entry) Zone: 0.618 - 0.786
        """
        diff = swing_high - swing_low
        if diff <= 0:
            return {}

        if is_uptrend:
            # Retracement down from high
            levels = {
                "fib_0": round(swing_high, 2),
                "fib_0236": round(swing_high - 0.236 * diff, 2),
                "fib_0382": round(swing_high - 0.382 * diff, 2),
                "fib_0500": round(swing_high - 0.500 * diff, 2),  # Equilibrium
                "fib_0618": round(swing_high - 0.618 * diff, 2),  # Golden Ratio
                "fib_0786": round(swing_high - 0.786 * diff, 2),  # OTE Base
                "fib_1": round(swing_low, 2),
                "ote_zone_high": round(swing_high - 0.618 * diff, 2),
                "ote_zone_low": round(swing_high - 0.786 * diff, 2),
                "ext_1272": round(swing_high + 0.272 * diff, 2),  # Target 1
                "ext_1618": round(swing_high + 0.618 * diff, 2),  # Target 2 (Golden Extension)
            }
        else:
            # Retracement up from low
            levels = {
                "fib_0": round(swing_low, 2),
                "fib_0236": round(swing_low + 0.236 * diff, 2),
                "fib_0382": round(swing_low + 0.382 * diff, 2),
                "fib_0500": round(swing_low + 0.500 * diff, 2),
                "fib_0618": round(swing_low + 0.618 * diff, 2),
                "fib_0786": round(swing_low + 0.786 * diff, 2),
                "fib_1": round(swing_high, 2),
                "ote_zone_low": round(swing_low + 0.618 * diff, 2),
                "ote_zone_high": round(swing_low + 0.786 * diff, 2),
                "ext_1272": round(swing_low - 0.272 * diff, 2),
                "ext_1618": round(swing_low - 0.618 * diff, 2),
            }

        return levels

    @staticmethod
    def identify_supply_demand_zones(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detects institutional Supply & Demand formations:
        - DBR (Drop-Base-Rally): Demand Zone
        - RBD (Rally-Base-Drop): Supply Zone
        - RBR (Rally-Base-Rally): Continuation Demand
        - DBD (Drop-Base-Drop): Continuation Supply
        """
        zones = []
        if len(df) < 10:
            return zones

        for i in range(2, len(df) - 2):
            c_prev = df.iloc[i-1]
            c_base = df.iloc[i]
            c_next = df.iloc[i+1]

            prev_body = c_prev["close"] - c_prev["open"]
            base_body = abs(c_base["close"] - c_base["open"])
            next_body = c_next["close"] - c_next["open"]
            avg_body = abs(df["close"].iloc[max(0, i-5):i] - df["open"].iloc[max(0, i-5):i]).mean()

            # Base candle must be small consolidation candle
            is_base = base_body < (avg_body * 0.75)

            if is_base and abs(next_body) > (avg_body * 1.5):
                # DBR: Drop -> Base -> Strong Rally (DEMAND)
                if prev_body < 0 and next_body > 0:
                    zones.append({
                        "type": "DEMAND_ZONE",
                        "formation": "DBR (Drop-Base-Rally)",
                        "proximal_line": float(max(c_base["open"], c_base["close"])),  # Entry line
                        "distal_line": float(c_base["low"]),                           # Stop Loss line
                        "time": str(df.index[i]),
                        "status": "FRESH"
                    })
                # RBD: Rally -> Base -> Strong Drop (SUPPLY)
                elif prev_body > 0 and next_body < 0:
                    zones.append({
                        "type": "SUPPLY_ZONE",
                        "formation": "RBD (Rally-Base-Drop)",
                        "proximal_line": float(min(c_base["open"], c_base["close"])),  # Entry line
                        "distal_line": float(c_base["high"]),                          # Stop Loss line
                        "time": str(df.index[i]),
                        "status": "FRESH"
                    })

        return zones[-6:]  # Keep freshest 6 zones

    @staticmethod
    def get_timeframe_key_levels(df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculates PDH/PDL (Previous Day High/Low), PWH/PWL (Previous Week), and Psychological Round Numbers.
        """
        if df.empty:
            return {}

        current_price = float(df["close"].iloc[-1])

        # PDH / PDL (Approx last 24 1-hour or 96 15m candles)
        lookback_day = min(len(df), 24)
        pdh = float(df["high"].iloc[-lookback_day:].max())
        pdl = float(df["low"].iloc[-lookback_day:].min())

        # PWH / PWL (Approx last 7 days)
        lookback_week = min(len(df), lookback_day * 7)
        pwh = float(df["high"].iloc[-lookback_week:].max())
        pwl = float(df["low"].iloc[-lookback_week:].min())

        # Round Numbers / Psychological Levels (e.g. 70000, 75000, 80000 for BTC)
        order_mag = 10 ** (int(np.log10(current_price)) - 1) if current_price > 10 else 1.0
        round_above = np.ceil(current_price / order_mag) * order_mag
        round_below = np.floor(current_price / order_mag) * order_mag

        return {
            "current_price": round(current_price, 2),
            "pdh": round(pdh, 2),
            "pdl": round(pdl, 2),
            "pwh": round(pwh, 2),
            "pwl": round(pwl, 2),
            "psychological_round_above": round(float(round_above), 2),
            "psychological_round_below": round(float(round_below), 2)
        }


if __name__ == "__main__":
    from agents.analytical_agent.market_feed import MarketFeedEngine
    feed = MarketFeedEngine()
    df = feed.fetch_crypto_candles("BTC", interval="15m", limit=80)
    levels = KeyLevelsAndFibEngine.get_timeframe_key_levels(df)
    print("Timeframe Key Levels:", levels)
    fibs = KeyLevelsAndFibEngine.calculate_fibonacci_levels(levels["pdl"], levels["pdh"], is_uptrend=True)
    print("Fibonacci OTE (0.618 - 0.786):", fibs.get("ote_zone_high"), "-", fibs.get("ote_zone_low"))
    zones = KeyLevelsAndFibEngine.identify_supply_demand_zones(df)
    print(f"Identified {len(zones)} Supply & Demand zones.")
    for z in zones[:2]:
        print(f"[{z['type']}] {z['formation']} Proximal: {z['proximal_line']} | Distal: {z['distal_line']}")
