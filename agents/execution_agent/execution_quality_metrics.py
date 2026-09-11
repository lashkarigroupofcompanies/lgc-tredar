"""
Execution Quality Metrics Engine - 50-Year Master Trader Execution Engine
Section 9: Execution Math & Section 10: Execution Quality Measurement

Implements institutional post-trade analytics:
1. Slippage Analysis: Actual Fill vs Intended Price.
2. MAE (Maximum Adverse Excursion): Worst intra-trade drawdown before winning.
3. MFE (Maximum Favorable Excursion): Peak intra-trade profit available.
4. Entry Efficiency:
   E_entry = (MFE - Entry) / (MFE - MAE) * 100
   (Quantifies how close the entry was to the absolute cyclical trough/peak)
5. Exit Efficiency:
   E_exit = (Exit - MAE) / (MFE - MAE) * 100
   (Quantifies what percentage of the cyclical potential was captured on exit)
6. Trade Efficiency:
   E_trade = (E_entry * E_exit) / 100
7. Entry Quality Score (1 - 10) & Exit Quality Score (1 - 10).
8. Institutional Fee & Breakeven Calculator (Brokerage + STT + Turnover + GST).
9. R-Multiple: Realized PnL / Initial Risk.
"""

from typing import Dict, Any, List, Optional
import math
import logging

logger = logging.getLogger("ExecutionQualityMetrics")


class ExecutionQualityMetrics:
    """
    Precision Execution Quality & Excursion Metrics Calculator.
    Supplies granular quantitative data to Sump Agent and Evolution Memory.
    """

    # Indian STT and Turnover Fee Schedule (Equity Intraday / Futures)
    INDIAN_CHARGES = {
        "BROKERAGE_PER_ORDER": 20.0,       # Rs 20 flat brokerage per leg
        "STT_SELL_RATE": 0.00025,          # 0.025% on sell side (intraday equity)
        "EXCHANGE_TURNOVER_RATE": 0.0000345,
        "GST_RATE": 0.18                   # 18% on brokerage + turnover
    }

    @classmethod
    def calculate_slippage(cls, intended_price: float, actual_price: float) -> Dict[str, Any]:
        """Calculates absolute and percentage slippage."""
        if intended_price <= 0.0:
            return {"slippage_abs": 0.0, "slippage_pct": 0.0}

        slip_abs = abs(actual_price - intended_price)
        slip_pct = (slip_abs / intended_price) * 100.0
        return {
            "slippage_abs": round(slip_abs, 4),
            "slippage_pct": round(slip_pct, 4)
        }

    @classmethod
    def calculate_indian_breakeven(
        cls,
        direction: str,
        entry_price: float,
        quantity: float
    ) -> Dict[str, Any]:
        """
        Calculates exact breakeven price accounting for round-trip brokerage, STT, and taxes (Section 9).
        """
        if quantity <= 0.0 or entry_price <= 0.0:
            return {"breakeven_price": entry_price, "total_charges": 0.0, "cost_per_share": 0.0}

        turnover = entry_price * quantity * 2.0  # Round trip approx
        brokerage = cls.INDIAN_CHARGES["BROKERAGE_PER_ORDER"] * 2.0  # Buy + Sell
        stt = (entry_price * quantity) * cls.INDIAN_CHARGES["STT_SELL_RATE"]
        exch_turnover = turnover * cls.INDIAN_CHARGES["EXCHANGE_TURNOVER_RATE"]
        gst = (brokerage + exch_turnover) * cls.INDIAN_CHARGES["GST_RATE"]

        total_charges = brokerage + stt + exch_turnover + gst
        cost_per_unit = total_charges / quantity

        if direction.upper() == "LONG":
            be_price = entry_price + cost_per_unit
        else:
            be_price = entry_price - cost_per_unit

        return {
            "entry_price": round(entry_price, 2),
            "breakeven_price": round(be_price, 2),
            "cost_per_unit": round(cost_per_unit, 4),
            "total_charges": round(total_charges, 2),
            "brokerage": round(brokerage, 2),
            "stt": round(stt, 2),
            "gst": round(gst, 2)
        }

    @classmethod
    def calculate_efficiency_metrics(
        cls,
        direction: str,
        entry_price: float,
        exit_price: float,
        mae_price: float,
        mfe_price: float
    ) -> Dict[str, Any]:
        """
        Calculates Entry Efficiency, Exit Efficiency, and Overall Trade Efficiency (Section 10).
        For LONG:
          MAE is lowest price during trade (< entry_price)
          MFE is highest price during trade (> entry_price)
        For SHORT:
          MAE is highest price during trade (> entry_price)
          MFE is lowest price during trade (< entry_price)
        """
        dir_upper = direction.upper()

        if dir_upper == "LONG":
            total_range = abs(mfe_price - mae_price)
            if total_range <= 1e-6:
                entry_eff = 100.0
                exit_eff = 100.0
            else:
                entry_eff = max(0.0, min(100.0, ((mfe_price - entry_price) / total_range) * 100.0))
                exit_eff = max(0.0, min(100.0, ((exit_price - mae_price) / total_range) * 100.0))

            mfe_capture_pct = 0.0
            if (mfe_price - entry_price) > 1e-6:
                mfe_capture_pct = max(0.0, min(100.0, ((exit_price - entry_price) / (mfe_price - entry_price)) * 100.0))

        else:  # SHORT
            total_range = abs(mae_price - mfe_price)
            if total_range <= 1e-6:
                entry_eff = 100.0
                exit_eff = 100.0
            else:
                entry_eff = max(0.0, min(100.0, ((entry_price - mfe_price) / total_range) * 100.0))
                exit_eff = max(0.0, min(100.0, ((mae_price - exit_price) / total_range) * 100.0))

            mfe_capture_pct = 0.0
            if (entry_price - mfe_price) > 1e-6:
                mfe_capture_pct = max(0.0, min(100.0, ((entry_price - exit_price) / (entry_price - mfe_price)) * 100.0))

        trade_eff = (entry_eff * exit_eff) / 100.0

        # Score calculations (1-10)
        entry_score = cls._score_entry_quality(entry_eff)
        exit_score = cls._score_exit_quality(exit_eff, mfe_capture_pct)

        return {
            "entry_efficiency_pct": round(entry_eff, 1),
            "exit_efficiency_pct": round(exit_eff, 1),
            "trade_efficiency_pct": round(trade_eff, 1),
            "mfe_capture_pct": round(mfe_capture_pct, 1),
            "entry_quality_score": entry_score,
            "exit_quality_score": exit_score,
            "mae_price": round(mae_price, 2),
            "mfe_price": round(mfe_price, 2)
        }

    @classmethod
    def _score_entry_quality(cls, entry_eff: float) -> int:
        """Scores entry quality 1 to 10 (Section 10 rubric)."""
        if entry_eff >= 90.0:
            return 10  # Entered at best possible price in zone
        elif entry_eff >= 75.0:
            return 8   # Entered near ideal zone proximal edge
        elif entry_eff >= 60.0:
            return 7   # Entered at OK price in zone
        elif entry_eff >= 45.0:
            return 5   # Entered at edge of zone
        elif entry_eff >= 25.0:
            return 3   # Chased entry slightly
        else:
            return 1   # Heavy adverse drift / FOMO entry

    @classmethod
    def _score_exit_quality(cls, exit_eff: float, mfe_capture_pct: float) -> int:
        """Scores exit quality 1 to 10 (Section 10 rubric)."""
        if exit_eff >= 85.0 and mfe_capture_pct >= 80.0:
            return 10  # Exited near peak target
        elif exit_eff >= 70.0:
            return 8   # Exited within 1R of target
        elif exit_eff >= 50.0:
            return 6   # Standard trailing stop or scale-out
        elif exit_eff >= 30.0:
            return 4   # Exited early, left significant profit
        else:
            return 2   # Held past major reversal signal
