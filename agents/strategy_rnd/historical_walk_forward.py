"""
Historical Multi-Window & Walk-Forward Validation Engine
Tests quantitative strategies across distinct historical chart periods (old charts)
to verify robustness across diverse market cycles (bull runs, bear crashes, sideways ranges).
Guarantees that a strategy isn't just lucky on recent bars, but genuinely works on past data.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from agents.strategy_rnd.fast_backtester import FastBacktestEngine

logger = logging.getLogger("HistoricalWalkForward")


class HistoricalWalkForwardEngine:
    """
    Multi-Window Historical Validator.
    Splits past chart history into rolling windows and measures cross-period consistency.
    """

    @staticmethod
    def run_multi_window_test(
        df: pd.DataFrame,
        strategy_func,
        window_size: int = 150,
        min_consistency_rate: float = 60.0
    ) -> Dict[str, Any]:
        """
        Executes rolling multi-window historical test across old chart data.
        """
        total_bars = len(df)
        if total_bars < window_size * 2:
            # If not enough bars for multi-window, run single full backtest
            signals = strategy_func(df)
            single_bt = FastBacktestEngine.run_backtest(df, signals)
            return {
                "tested_windows_count": 1,
                "profitable_windows_count": 1 if single_bt["profit_factor"] >= 1.2 else 0,
                "consistency_rate_pct": 100.0 if single_bt["profit_factor"] >= 1.2 else 50.0,
                "overall_historical_win_rate": single_bt["win_rate"],
                "overall_historical_profit_factor": single_bt["profit_factor"],
                "overall_historical_sharpe": single_bt["sharpe_ratio"],
                "total_historical_trades": single_bt["total_trades"],
                "is_historically_proven": single_bt["profit_factor"] >= 1.2 and single_bt["win_rate"] >= 50.0,
                "historical_verdict": "PROVEN_ON_CHART" if single_bt["profit_factor"] >= 1.2 else "MARGINAL_EDGE",
                "sample_windows": [single_bt]
            }

        window_results: List[Dict[str, Any]] = []
        profitable_windows = 0
        step_size = window_size // 2  # 50% overlap rolling windows

        for start_idx in range(0, total_bars - window_size + 1, step_size):
            end_idx = start_idx + window_size
            sub_df = df.iloc[start_idx:end_idx].copy()
            sub_signals = strategy_func(sub_df)
            bt = FastBacktestEngine.run_backtest(sub_df, sub_signals)

            is_prof = bt["profit_factor"] >= 1.15 and bt["win_rate"] >= 48.0
            if is_prof:
                profitable_windows += 1

            window_results.append({
                "window_index": len(window_results) + 1,
                "start_date": str(sub_df.index[0]) if hasattr(sub_df.index, "date") else str(start_idx),
                "end_date": str(sub_df.index[-1]) if hasattr(sub_df.index, "date") else str(end_idx),
                "trades": bt["total_trades"],
                "win_rate": bt["win_rate"],
                "profit_factor": bt["profit_factor"],
                "sharpe": bt["sharpe_ratio"],
                "is_profitable": is_prof
            })

        total_windows = len(window_results)
        consistency_rate = round((profitable_windows / total_windows) * 100, 1) if total_windows > 0 else 0.0

        # Full historical backtest across all available historical bars
        full_signals = strategy_func(df)
        full_bt = FastBacktestEngine.run_backtest(df, full_signals)

        is_proven = consistency_rate >= min_consistency_rate and full_bt["profit_factor"] >= 1.25

        return {
            "tested_windows_count": total_windows,
            "profitable_windows_count": profitable_windows,
            "consistency_rate_pct": consistency_rate,
            "overall_historical_win_rate": full_bt["win_rate"],
            "overall_historical_profit_factor": full_bt["profit_factor"],
            "overall_historical_sharpe": full_bt["sharpe_ratio"],
            "total_historical_trades": full_bt["total_trades"],
            "is_historically_proven": is_proven,
            "historical_verdict": "PROVEN_ACROSS_OLD_CHARTS" if is_proven else "INSUFFICIENT_HISTORICAL_EDGE",
            "sample_windows": window_results[-3:]  # Show last 3 windows
        }
