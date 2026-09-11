"""
Fast Vectorized Quantitative Backtesting Engine
Tests any trading strategy against historical OHLCV candle arrays in milliseconds.
Calculates authentic quantitative metrics: Win Rate, Profit Factor, Sharpe Ratio, Max Drawdown.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional


class FastBacktestEngine:
    """
    High-speed vectorized backtesting engine designed for automated strategy optimization
    and real-time sanity checking before any trade recommendation is generated.
    """

    @staticmethod
    def run_backtest(
        df: pd.DataFrame,
        signals: pd.Series,  # 1 = BUY, -1 = SELL, 0 = HOLD
        atr_multiplier_sl: float = 1.5,
        risk_reward_ratio: float = 2.0,
        fee_rate: float = 0.0005  # 0.05% per trade slippage/commission
    ) -> Dict[str, Any]:
        """
        Executes a vectorized bar-by-bar trade simulation based on signal series.
        """
        if df.empty or len(df) < 20 or signals.empty:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "net_profit_pct": 0.0,
                "status": "INSUFFICIENT_DATA"
            }

        # Compute True Range using pandas directly (bulletproof & type-safe)
        h = df["high"].astype(float)
        l = df["low"].astype(float)
        c = df["close"].astype(float)
        prev_c = c.shift(1).fillna(c)

        tr1 = h - l
        tr2 = (h - prev_c).abs()
        tr3 = (l - prev_c).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_series = tr.rolling(14, min_periods=1).mean().fillna(c * 0.01)

        closes: List[float] = [float(x) for x in c]
        highs: List[float] = [float(x) for x in h]
        lows: List[float] = [float(x) for x in l]
        atr: List[float] = [float(x) for x in atr_series]
        sig_vals: List[int] = [int(x) for x in signals.fillna(0)]

        trades: List[Dict[str, Any]] = []
        position = 0  # 1 = Long, -1 = Short, 0 = Flat
        entry_price = 0.0
        stop_loss = 0.0
        take_profit = 0.0
        entry_idx = 0

        for i in range(len(df) - 1):
            curr_close = closes[i]
            curr_high = highs[i]
            curr_low = lows[i]
            curr_sig = sig_vals[i]
            curr_atr = atr[i]

            # Check if active position hits SL or TP on current candle
            if position == 1:
                if curr_low <= stop_loss:
                    # SL Hit
                    exit_price = stop_loss
                    pnl_pct = (exit_price - entry_price) / entry_price - fee_rate * 2
                    trades.append({"type": "LONG", "pnl": pnl_pct, "bars": i - entry_idx, "exit": "SL"})
                    position = 0
                elif curr_high >= take_profit:
                    # TP Hit
                    exit_price = take_profit
                    pnl_pct = (exit_price - entry_price) / entry_price - fee_rate * 2
                    trades.append({"type": "LONG", "pnl": pnl_pct, "bars": i - entry_idx, "exit": "TP"})
                    position = 0

            elif position == -1:
                if curr_high >= stop_loss:
                    # SL Hit
                    exit_price = stop_loss
                    pnl_pct = (entry_price - exit_price) / entry_price - fee_rate * 2
                    trades.append({"type": "SHORT", "pnl": pnl_pct, "bars": i - entry_idx, "exit": "SL"})
                    position = 0
                elif curr_low <= take_profit:
                    # TP Hit
                    exit_price = take_profit
                    pnl_pct = (entry_price - exit_price) / entry_price - fee_rate * 2
                    trades.append({"type": "SHORT", "pnl": pnl_pct, "bars": i - entry_idx, "exit": "TP"})
                    position = 0

            # If flat, check for new entry signal
            if position == 0 and curr_sig != 0:
                if curr_sig == 1:
                    position = 1
                    entry_price = curr_close
                    sl_dist = curr_atr * atr_multiplier_sl
                    stop_loss = entry_price - sl_dist
                    take_profit = entry_price + (sl_dist * risk_reward_ratio)
                    entry_idx = i
                elif curr_sig == -1:
                    position = -1
                    entry_price = curr_close
                    sl_dist = curr_atr * atr_multiplier_sl
                    stop_loss = entry_price + sl_dist
                    take_profit = entry_price - (sl_dist * risk_reward_ratio)
                    entry_idx = i

        if not trades:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "net_profit_pct": 0.0,
                "status": "NO_TRADES"
            }

        pnls = [t["pnl"] for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        total_trades = len(trades)
        win_count = len(wins)
        win_rate = round((win_count / total_trades) * 100, 2)

        gross_profit = float(sum(wins)) if wins else 0.0
        gross_loss = float(abs(sum(losses))) if losses else 0.0
        profit_factor = round(float(gross_profit / gross_loss), 2) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

        # Equity Curve & Drawdown calculation
        equity_curve = np.cumprod(1.0 + np.array(pnls))
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (peak - equity_curve) / peak
        max_drawdown = round(float(np.max(drawdown)) * 100, 2) if len(drawdown) > 0 else 0.0

        # Sharpe ratio approximation (annualized for 15m/short timeframe)
        returns_arr = np.array(pnls)
        mean_ret = np.mean(returns_arr)
        std_ret = np.std(returns_arr)
        sharpe = round(float((mean_ret / std_ret) * np.sqrt(252 * 26)), 2) if std_ret > 0 else 0.0

        net_profit_pct = round(float((equity_curve[-1] - 1.0) * 100), 2)

        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "net_profit_pct": net_profit_pct,
            "avg_trade_bars": round(float(np.mean([t["bars"] for t in trades])), 1),
            "status": "VALIDATED" if win_rate >= 55.0 and profit_factor >= 1.3 else "REJECTED_LOW_EDGE"
        }
