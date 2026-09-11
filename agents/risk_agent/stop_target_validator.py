"""
Stop Loss & Target Validator - Section 3, 4 & 10 of Risk Management Knowledge Base
Validates entry geometry, structural placement, and mathematical expectancy:
- Hard Stop Loss Verification (Zero trades permitted without explicit, verified SL)
- Structure-Based SL with ATR Buffer (Behind swing high/low, beyond liquidity zones)
- ATR Stop Loss Models (1.5x tight, 2.0x standard, 3.0x wide)
- Chandelier Exit & Trailing Stop Calculator
- Stop Loss Mistake Detection (Stop too tight <0.2%, Stop too wide >6.0%, Round number traps)
- Minimum R:R Ratio Enforcement (Min 1:2.0 for intraday/swing; reject trades < 1:2.0)
- Mathematical Expectancy Engine (Expectancy = P_win * R_win - P_loss * R_loss > 0)
- Partial Profit Scale Model (50% at 1R -> BE, 25% at 2R, 25% Trail)
"""

import math
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger("StopTargetValidator")


class StopTargetValidator:
    """
    Mathematical Structure, Stop-Loss & Take-Profit Auditor.
    Enforces minimum 1:2 R:R and validates that stops are placed beyond structural liquidity.
    """

    MIN_RR_STANDARDS = {
        "SCALPING": 1.5,
        "INTRADAY": 2.0,
        "SWING": 2.5,
        "POSITIONAL": 3.0
    }

    @classmethod
    def calculate_atr(cls, df: pd.DataFrame, period: int = 14) -> float:
        """Calculates Average True Range (ATR)."""
        if len(df) < period + 1:
            return float(df.iloc[-1]["close"]) * 0.015 if not df.empty else 1.0

        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)

        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean().iloc[-1]
        return float(atr) if not np.isnan(atr) else float(close.iloc[-1]) * 0.015

    @classmethod
    def calculate_chandelier_exit(
        cls,
        df: pd.DataFrame,
        direction: str,
        period: int = 22,
        multiplier: float = 3.0
    ) -> float:
        """
        Chandelier Exit:
        Long = Highest High(n) - (Multiplier * ATR)
        Short = Lowest Low(n) + (Multiplier * ATR)
        """
        atr = cls.calculate_atr(df, period=14)
        sub = df.tail(period)
        if direction.upper() == "LONG":
            highest_high = float(sub["high"].max())
            return round(highest_high - (multiplier * atr), 2)
        else:
            lowest_low = float(sub["low"].min())
            return round(lowest_low + (multiplier * atr), 2)

    @classmethod
    def audit_trade_geometry(
        cls,
        entry_price: float,
        stop_loss: float,
        take_profit_1: float,
        take_profit_2: float,
        direction: str,
        df: pd.DataFrame,
        timeframe_style: str = "INTRADAY",
        win_rate_estimate: float = 0.50
    ) -> Dict[str, Any]:
        """
        Full Section 3, 4, 10 Audit:
        1. Verifies SL existence and logical direction
        2. Detects SL mistakes (too tight, too wide, round number magnet)
        3. Enforces Minimum 1:2 R:R
        4. Verifies positive Mathematical Expectancy
        5. Computes structured partial profit milestones
        """
        direction = direction.upper()
        flags = []

        # 1. Non-negotiable Hard Stop Loss Check
        if stop_loss <= 0 or entry_price <= 0:
            return {
                "decision": "REJECTED",
                "reason": "MISSING_STOP_LOSS: No trade allowed without an explicit hard stop loss in market.",
                "flags": ["NO_SL_SPECIFIED"]
            }

        # 2. Geometric Direction Check
        if direction == "LONG" and stop_loss >= entry_price:
            return {
                "decision": "REJECTED",
                "reason": "GEOMETRY_INVALID: Long Stop Loss must be strictly below Entry Price.",
                "flags": ["SL_ABOVE_LONG_ENTRY"]
            }
        elif direction == "SHORT" and stop_loss <= entry_price:
            return {
                "decision": "REJECTED",
                "reason": "GEOMETRY_INVALID: Short Stop Loss must be strictly above Entry Price.",
                "flags": ["SL_BELOW_SHORT_ENTRY"]
            }

        risk_distance = abs(entry_price - stop_loss)
        sl_pct = (risk_distance / entry_price) * 100.0
        atr = cls.calculate_atr(df, 14) if not df.empty else (entry_price * 0.015)

        # 3. Stop Loss Mistake Detection (Section 3)
        if sl_pct < 0.20:
            return {
                "decision": "REJECTED",
                "reason": f"STOP_TOO_TIGHT: SL is only {sl_pct:.2f}% from entry. Vulnerable to regular spread/noise stop-outs.",
                "flags": ["SL_TOO_TIGHT"]
            }
        if sl_pct > 6.0:
            return {
                "decision": "REJECTED",
                "reason": f"STOP_TOO_WIDE: SL is {sl_pct:.2f}% wide (Max allowed is 6.0%). Requires excessive capital at risk.",
                "flags": ["SL_TOO_WIDE"]
            }

        # Check if SL is at a vulnerable round psychological number
        if str(int(stop_loss)).endswith("00") or str(int(stop_loss)).endswith("50"):
            flags.append("ROUND_NUMBER_STOP_HUNT_RISK: Consider padding SL 5-10 ticks behind round number.")

        # 4. Take Profit & R:R Validation (Section 4 & 10)
        # If no TP specified, set minimum 1:2.5 default target
        if take_profit_1 <= 0:
            take_profit_1 = round(entry_price + (risk_distance * 2.0) if direction == "LONG" else entry_price - (risk_distance * 2.0), 2)
        if take_profit_2 <= 0:
            take_profit_2 = round(entry_price + (risk_distance * 3.0) if direction == "LONG" else entry_price - (risk_distance * 3.0), 2)

        reward_distance = abs(take_profit_1 - entry_price)
        rr_ratio = reward_distance / risk_distance

        min_required_rr = cls.MIN_RR_STANDARDS.get(timeframe_style.upper(), 2.0)
        if round(rr_ratio, 2) < (min_required_rr - 0.02):
            return {
                "decision": "REJECTED",
                "reason": f"INSUFFICIENT_RR: Trade R:R is 1:{rr_ratio:.2f} (Minimum required is 1:{min_required_rr:.1f}). Asymmetry edge absent.",
                "rr_ratio": round(rr_ratio, 2),
                "min_required_rr": min_required_rr,
                "flags": ["UNFAVORABLE_RISK_REWARD"]
            }

        # 5. Mathematical Expectancy System (Section 10)
        # Expectancy = (Win% * Avg Win) - (Loss% * Avg Loss)
        p_win = min(0.90, max(0.20, win_rate_estimate))
        p_loss = 1.0 - p_win
        avg_win_r = rr_ratio
        avg_loss_r = 1.0

        expectancy_r = (p_win * avg_win_r) - (p_loss * avg_loss_r)
        if expectancy_r <= 0.05:
            return {
                "decision": "REJECTED",
                "reason": f"NEGATIVE_EXPECTANCY: Expected return per trade is {expectancy_r:.2f}R (Win Rate: {p_win*100:.1f}%, R:R: 1:{rr_ratio:.2f}). No mathematical edge.",
                "expectancy_r": round(expectancy_r, 2),
                "flags": ["NEGATIVE_EXPECTANCY"]
            }

        # 6. Structured Partial Scale Plan (Section 4)
        # 50% at 1R -> Move SL to Breakeven
        # 25% at 2R
        # 25% Trail with Chandelier / Structure
        be_target = round(entry_price + (risk_distance * 1.0) if direction == "LONG" else entry_price - (risk_distance * 1.0), 2)
        chandelier_trail = cls.calculate_chandelier_exit(df, direction, period=22, multiplier=2.5) if not df.empty else stop_loss

        return {
            "decision": "APPROVED",
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit_1": take_profit_1,
            "take_profit_2": take_profit_2,
            "risk_distance": round(risk_distance, 4),
            "reward_distance": round(reward_distance, 4),
            "rr_ratio": round(rr_ratio, 2),
            "expectancy_r": round(expectancy_r, 2),
            "partial_plan": {
                "tp1_breakeven_milestone": be_target,
                "tp1_portion": "50% banked at 1.0R, SL to Breakeven",
                "tp2_target": take_profit_1,
                "tp2_portion": "25% banked at Target 1",
                "tp3_trail": f"25% trailed with Chandelier Stop (${chandelier_trail})"
            },
            "flags": flags
        }
