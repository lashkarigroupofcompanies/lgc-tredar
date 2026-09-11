"""
Monte Carlo & Drawdown Risk Analyzer (Section 7 & 8 Framework)
Simulates 1,000 randomized forward futures to evaluate tail risk:
- 95th & 99th Percentile Max Drawdown
- Probability of Ruin (Chance of losing >= 50% capital)
- Ulcer Index (Combined Drawdown Depth + Duration Penalty)
- Drawdown Recovery Mathematics
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List


class MonteCarloDrawdownAnalyzer:
    """
    Simulates worst-case drawdown distributions under thousands of trade sequence permutations.
    """

    @staticmethod
    def calculate_drawdown_recovery(loss_pct: float) -> float:
        """Calculates exact gain required to recover from a loss percentage."""
        loss_decimal = min(abs(loss_pct) / 100.0, 0.95)
        needed_gain = (1.0 / (1.0 - loss_decimal)) - 1.0
        return round(needed_gain * 100, 2)

    @classmethod
    def run_1000_monte_carlo_simulations(
        cls,
        trade_returns_pct: List[float],
        starting_capital: float = 100000.0,
        simulations_count: int = 1000
    ) -> Dict[str, Any]:
        """
        Executes 1000 Monte Carlo bootstrap permutations on the strategy trade log.
        """
        if not trade_returns_pct or len(trade_returns_pct) < 3:
            return {
                "monte_carlo_simulations": 0,
                "mc_95_max_drawdown_pct": 0.0,
                "mc_99_max_drawdown_pct": 0.0,
                "probability_of_ruin_pct": 0.0,
                "ulcer_index": 0.0,
                "recovery_gain_needed_pct": 0.0,
                "risk_verdict": "INSUFFICIENT_DATA"
            }

        returns_arr = np.array(trade_returns_pct) / 100.0
        n_trades = len(returns_arr)

        sim_drawdowns = []
        ruin_events = 0
        final_returns = []

        for _ in range(simulations_count):
            # Bootstrap with replacement
            sampled = np.random.choice(returns_arr, size=n_trades, replace=True)
            equity = starting_capital * np.cumprod(1.0 + sampled)

            peak = np.maximum.accumulate(equity)
            dd = (peak - equity) / peak
            max_sim_dd = float(np.max(dd)) * 100
            sim_drawdowns.append(max_sim_dd)

            # Ruin defined as losing >= 50% of peak capital
            if max_sim_dd >= 50.0:
                ruin_events += 1

            final_returns.append(float((equity[-1] - starting_capital) / starting_capital) * 100)

        mc_95_dd = round(float(np.percentile(sim_drawdowns, 95)), 2)
        mc_99_dd = round(float(np.percentile(sim_drawdowns, 99)), 2)
        p_ruin = round((ruin_events / simulations_count) * 100, 2)

        # Ulcer Index computation on median equity curve
        median_equity = starting_capital * np.cumprod(1.0 + returns_arr)
        med_peak = np.maximum.accumulate(median_equity)
        med_dd_pct = ((med_peak - median_equity) / med_peak) * 100
        ulcer_index = round(float(np.sqrt(np.mean(med_dd_pct ** 2))), 2)

        recovery_needed = cls.calculate_drawdown_recovery(mc_95_dd)

        # Drawdown Risk Verdict
        if mc_95_dd <= 15.0 and p_ruin == 0.0:
            verdict = "EXCELLENT_CAPITAL_PRESERVATION"
        elif mc_95_dd <= 25.0 and p_ruin < 2.0:
            verdict = "ACCEPTABLE_INSTITUTIONAL_RISK"
        elif mc_95_dd <= 40.0:
            verdict = "HIGH_DRAWDOWN_WARNING"
        else:
            verdict = "CATASTROPHIC_RUIN_RISK"

        return {
            "monte_carlo_simulations": simulations_count,
            "mc_95_max_drawdown_pct": mc_95_dd,
            "mc_99_max_drawdown_pct": mc_99_dd,
            "probability_of_ruin_pct": p_ruin,
            "ulcer_index": ulcer_index,
            "recovery_gain_needed_pct": recovery_needed,
            "median_expected_return_pct": round(float(np.median(final_returns)), 2),
            "risk_verdict": verdict,
            "is_risk_acceptable": mc_95_dd <= 25.0 and p_ruin < 2.0
        }
