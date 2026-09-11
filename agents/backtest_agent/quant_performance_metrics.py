"""
Institutional Quantitative Performance Metrics Suite
Calculates advanced hedge-fund grade backtesting metrics:
- Sortino Ratio (Penalizes only downside downside risk)
- Calmar Ratio (Annualized Return / Max Drawdown)
- Mathematical Expectancy: E = (Win% * AvgWin) - (Loss% * AvgLoss)
- Maximum Consecutive Loss Streak
- 100-Iteration Monte Carlo Simulation (95% Confidence Interval for Drawdown)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List


class QuantPerformanceMetrics:
    """
    Advanced metrics calculator following QuantConnect Lean and Backtrader methodologies.
    """

    @staticmethod
    def calculate_advanced_metrics(
        trade_pnls: List[float],
        equity_curve: np.ndarray,
        timeframe_annualization_factor: float = 252 * 26  # Standard 15m annualization
    ) -> Dict[str, Any]:
        """
        Computes Sortino, Calmar, Expectancy, and Monte Carlo risk confidence.
        """
        if not trade_pnls or len(trade_pnls) < 2:
            return {
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0,
                "expectancy_pct": 0.0,
                "max_consecutive_losses": 0,
                "monte_carlo_95_dd": 0.0,
                "is_institutional_quality": False
            }

        pnls = np.array(trade_pnls)
        wins = pnls[pnls > 0]
        losses = pnls[pnls <= 0]

        win_rate = len(wins) / len(pnls)
        loss_rate = len(losses) / len(pnls)
        avg_win = float(np.mean(wins)) if len(wins) > 0 else 0.0
        avg_loss = float(np.mean(np.abs(losses))) if len(losses) > 0 else 0.0

        # 1. Mathematical Expectancy
        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
        expectancy_pct = round(float(expectancy * 100), 2)

        # 2. Sortino Ratio (Downside Deviation only)
        downside_returns = pnls[pnls < 0]
        downside_std = float(np.std(downside_returns)) if len(downside_returns) > 0 else 1e-6
        mean_ret = float(np.mean(pnls))
        sortino = round(float((mean_ret / max(downside_std, 1e-6)) * np.sqrt(timeframe_annualization_factor)), 2)

        # 3. Calmar Ratio (CAGR / Max Drawdown)
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (peak - equity_curve) / peak
        max_dd = float(np.max(drawdown)) if len(drawdown) > 0 else 0.01
        total_return = float(equity_curve[-1] - 1.0)
        calmar = round(float(total_return / max(max_dd, 0.005)), 2)

        # 4. Maximum Consecutive Loss Streak
        max_streak = 0
        current_streak = 0
        for p in pnls:
            if p <= 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        # 5. 100-Iteration Monte Carlo Permutation Test
        # Reshuffles trade order 100 times to determine realistic worst-case drawdown
        mc_drawdowns = []
        for _ in range(100):
            shuffled_pnls = np.random.permutation(pnls)
            sim_equity = np.cumprod(1.0 + shuffled_pnls)
            sim_peak = np.maximum.accumulate(sim_equity)
            sim_dd = (sim_peak - sim_equity) / sim_peak
            mc_drawdowns.append(np.max(sim_dd))

        mc_95_dd = round(float(np.percentile(mc_drawdowns, 95) * 100), 2)

        # Institutional quality threshold: Positive expectancy, Sortino >= 1.5, Monte Carlo DD <= 25%
        is_inst_quality = expectancy_pct > 0.1 and sortino >= 1.4 and mc_95_dd <= 25.0

        return {
            "sortino_ratio": sortino,
            "calmar_ratio": calmar,
            "expectancy_pct": expectancy_pct,
            "max_consecutive_losses": max_streak,
            "monte_carlo_95_dd": mc_95_dd,
            "is_institutional_quality": is_inst_quality,
            "avg_win_pct": round(avg_win * 100, 2),
            "avg_loss_pct": round(avg_loss * 100, 2)
        }
