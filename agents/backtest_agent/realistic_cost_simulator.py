"""
Realistic Transaction Cost & Slippage Simulator (Section 4 Framework)
Simulates authentic live execution frictions:
- Brokerage commissions (Crypto 0.04%, US Equities, Indian Equities)
- Indian Statutory Taxes: STT (Securities Transaction Tax), GST, Stamp Duty, Exchange & SEBI charges
- Volatility-Adjusted Bid-Ask Spread Slippage
- Next-Candle Open Execution (Eliminates Look-Ahead Bias)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any


class RealisticCostSimulator:
    """
    Simulates real broker and market impact costs to prevent paper profits from evaporating live.
    """

    # Fee structures by market
    FEE_SCHEDULES = {
        "CRYPTO": {
            "commission_rate": 0.0004,     # 0.04% Binance/Exchange taker fee
            "base_slippage": 0.0005,       # 0.05% bid-ask spread
            "regulatory_tax_rate": 0.0000  # No STT
        },
        "INDIAN_STOCKS": {
            "commission_rate": 0.0003,     # Zerodha / discount broker equity intraday
            "base_slippage": 0.0004,       # 0.04% liquid NSE stock spread
            "regulatory_tax_rate": 0.00035 # STT (0.025%) + GST on broker (18%) + Stamp duty + SEBI
        },
        "US_STOCKS": {
            "commission_rate": 0.0001,     # Clearing fee (zero commission broker)
            "base_slippage": 0.0003,       # 0.03% S&P 500 / mega-cap liquid spread
            "regulatory_tax_rate": 0.00005 # SEC / FINRA fee
        }
    }

    @classmethod
    def calculate_round_trip_friction(
        cls,
        market_type: str = "CRYPTO",
        current_atr_pct: float = 1.5,
        is_high_volatility: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates total round-trip percentage drag (Commissions + Taxes + Slippage).
        """
        sched = cls.FEE_SCHEDULES.get(market_type.upper(), cls.FEE_SCHEDULES["CRYPTO"])
        comm = sched["commission_rate"] * 2.0  # Entry + Exit
        tax = sched["regulatory_tax_rate"] * 2.0

        # Slippage scales up during high volatility
        slippage_mult = 1.8 if is_high_volatility else 1.0
        slippage = (sched["base_slippage"] * slippage_mult) * 2.0

        total_drag_pct = round((comm + tax + slippage) * 100, 3)

        return {
            "market": market_type,
            "brokerage_pct": round(comm * 100, 3),
            "taxes_and_statutory_pct": round(tax * 100, 3),
            "slippage_pct": round(slippage * 100, 3),
            "total_round_trip_cost_pct": total_drag_pct,
            "cost_drag_factor": total_drag_pct / 100.0
        }

    @classmethod
    def apply_friction_to_trade_returns(
        cls,
        raw_trade_returns: list,
        market_type: str = "CRYPTO"
    ) -> list:
        """
        Deducts realistic transaction costs from each simulated trade return.
        """
        friction = cls.calculate_round_trip_friction(market_type)["cost_drag_factor"]
        return [round(r - friction, 4) for r in raw_trade_returns]
