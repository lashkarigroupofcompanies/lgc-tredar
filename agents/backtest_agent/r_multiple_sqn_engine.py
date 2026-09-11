"""
Van Tharp R-Multiple & System Quality Number (SQN) Engine (Section 15 Framework)
Measures trade outcomes strictly in terms of initial risk (R).
Calculates authentic mathematical expectancy and Van Tharp SQN:
  SQN = (Mean R / StdDev R) * sqrt(Total Trades)
Grades:
  < 1.6: Poor / Below Average
  1.6 - 2.4: Average
  2.5 - 2.9: Good
  3.0 - 5.0: Excellent
  5.0 - 6.9: Superb
  > 7.0: Holy Grail (Flagged for potential Overfitting)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List


class RMultipleSQNEngine:
    """
    Van Tharp Quantitative System Evaluation.
    Normalizes all trade profits/losses to R units.
    """

    @staticmethod
    def compute_r_multiples_and_sqn(
        trade_returns_pct: List[float],
        risk_per_trade_pct: float = 1.5
    ) -> Dict[str, Any]:
        """
        Converts trade return percentages into R-multiples and computes SQN.
        """
        if not trade_returns_pct or len(trade_returns_pct) < 3:
            return {
                "total_trades": len(trade_returns_pct) if trade_returns_pct else 0,
                "mean_r": 0.0,
                "std_r": 1.0,
                "sqn": 0.0,
                "sqn_tier": "INSUFFICIENT_DATA",
                "expectancy_r": 0.0,
                "positive_skew": False,
                "r_distribution": []
            }

        risk_unit = max(risk_per_trade_pct, 0.1)
        r_multiples = np.array([round(pnl / risk_unit, 2) for pnl in trade_returns_pct])
        n = len(r_multiples)

        mean_r = float(np.mean(r_multiples))
        std_r = float(np.std(r_multiples))
        if std_r < 1e-5:
            std_r = 1.0

        # Van Tharp SQN formula
        sqn = float((mean_r / std_r) * np.sqrt(n))
        sqn = round(sqn, 2)

        # Skewness (prefer positive skew - large right tail wins)
        diff = r_multiples - mean_r
        skewness = float(np.mean(diff ** 3) / (std_r ** 3)) if std_r > 0 else 0.0

        # Expectancy in R: (Win% * AvgWinR) - (Loss% * AvgLossR)
        wins_r = r_multiples[r_multiples > 0]
        losses_r = np.abs(r_multiples[r_multiples <= 0])
        win_rate = len(wins_r) / n
        loss_rate = len(losses_r) / n
        avg_win_r = float(np.mean(wins_r)) if len(wins_r) > 0 else 0.0
        avg_loss_r = float(np.mean(losses_r)) if len(losses_r) > 0 else 1.0
        expectancy_r = round((win_rate * avg_win_r) - (loss_rate * avg_loss_r), 2)

        # SQN Tier
        if sqn >= 7.0:
            tier = "HOLY_GRAIL_SUSPICIOUS_OVERFIT"
        elif sqn >= 5.0:
            tier = "SUPERB"
        elif sqn >= 3.0:
            tier = "EXCELLENT"
        elif sqn >= 2.5:
            tier = "GOOD"
        elif sqn >= 1.6:
            tier = "AVERAGE"
        else:
            tier = "POOR"

        return {
            "total_trades": n,
            "mean_r": round(mean_r, 2),
            "std_r": round(std_r, 2),
            "sqn": sqn,
            "sqn_tier": tier,
            "expectancy_r": expectancy_r,
            "skewness": round(skewness, 2),
            "positive_skew": skewness > 0,
            "avg_win_r": round(avg_win_r, 2),
            "avg_loss_r": round(avg_loss_r, 2),
            "win_rate_pct": round(win_rate * 100, 1),
            "is_viable": sqn >= 2.0 and expectancy_r > 0.2
        }
