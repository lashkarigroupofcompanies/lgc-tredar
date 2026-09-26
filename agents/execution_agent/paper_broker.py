"""
Simulated Paper Broker Engine with Realistic Slippage & Cost Models
50-Year Master Trader Execution Engine

Features:
1. Virtual balance management ($100,000 starting default).
2. Multi-asset execution (CRYPTO, INDIAN_STOCKS, US_STOCKS).
3. 3-Tier Partial Profit Booking (Section 4):
   - Tier 1: 33% at +1.0R -> Moves Stop Loss to Breakeven (+0.0R)
   - Tier 2: 33% at +2.0R -> Trails Stop Loss to +1.0R Locked Profit
   - Tier 3: Remaining 34% Runner -> Rides with Chandelier ATR / Structural Trailing Stop
4. Continuous MAE / MFE Real-Time Tracking:
   - Updates Maximum Adverse Excursion (MAE) and Maximum Favorable Excursion (MFE) on every candle.
5. Institutional Execution Quality Metrics (Section 10):
   - Entry Efficiency %, Exit Efficiency %, Trade Efficiency %, MFE Capture %, Quality Scores (1-10).
6. Indian Market Brokerage & STT/GST Precision Math.
7. Seamless Hand-off to Sump Agent for counterfactual post-trade learning.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import time
import logging
import uuid
from typing import Dict, Any, List, Optional
import pandas as pd

from agents.analytical_agent.active_trade_monitor import ActiveTradeMonitor
from agents.execution_agent.execution_quality_metrics import ExecutionQualityMetrics
from agents.execution_agent.trade_lifecycle_manager import TradeLifecycleManager
from shared_brain.live_trade_working_memory import LiveTradeWorkingMemory
from agents.evolution_memory.mem0_memory_engine import Mem0MemoryEngine

logger = logging.getLogger("PaperBroker")


class PaperBroker:
    """
    Institutional paper broker supporting multi-tier execution,
    MAE/MFE quantitative tracking, and execution efficiency analysis.
    """

    SLIPPAGE_RATES = {
        "CRYPTO": 0.0002,         # 2 bps slippage
        "INDIAN_STOCKS": 0.0003,  # 3 bps slippage
        "US_STOCKS": 0.0002,      # 2 bps slippage
        "UK_STOCKS": 0.0003,      # 3 bps slippage
        "EU_STOCKS": 0.0003,      # 3 bps slippage
        "ASIAN_STOCKS": 0.0003,   # 3 bps slippage
        "FOREX": 0.0001,          # 1 pip spread/slippage
        "COMMODITIES": 0.0002     # 2 bps slippage
    }

    FEE_RATES = {
        "CRYPTO": 0.0005,         # 5 bps exchange fee
        "INDIAN_STOCKS": 0.0006,  # 6 bps STT/GST/exchange
        "US_STOCKS": 0.0003,      # 3 bps clearing fee
        "UK_STOCKS": 0.0005,      # 5 bps Stamp duty reserve / broker
        "EU_STOCKS": 0.0005,      # 5 bps exchange turnover / fee
        "ASIAN_STOCKS": 0.0005,   # 5 bps exchange fee
        "FOREX": 0.0002,          # 2 bps liquidity fee
        "COMMODITIES": 0.0004     # 4 bps exchange clearing
    }

    SUPPORTED_MARKETS = ["INDIAN_STOCKS", "US_STOCKS", "CRYPTO", "COMMODITIES", "FOREX"]

    def __init__(self, starting_balance: float = 500000.0, per_market_capital: float = 100000.0):
        self.per_market_capital = float(per_market_capital)
        self.market_starting_cap: Dict[str, float] = {
            m: self.per_market_capital for m in self.SUPPORTED_MARKETS
        }
        # Dedicated ₹5,00,000 fixed starting capital pools for each operational mode
        self.mode_starting_cap: Dict[str, float] = {
            "SAFE": 500000.0,
            "MONEY_MAKER": 500000.0,
            "DANGEROUS": 500000.0
        }
        self.starting_balance = float(sum(self.market_starting_cap.values())) if starting_balance == 500000.0 else float(starting_balance)
        self.balance = self.starting_balance
        self.open_positions: Dict[str, Dict[str, Any]] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self._hydrate_from_cloud()

    def _hydrate_from_cloud(self):
        """Hydrates past closed trades from Turso Cloud Database on initialization."""
        try:
            from shared_brain.turso_sync import turso_client
            cloud_trades = turso_client.get_all_trades()
            if cloud_trades:
                self.trade_history = cloud_trades
                total_realized_pnl = sum(float(t.get("realized_pnl", t.get("pnl", 0.0))) for t in self.trade_history)
                self.balance = self.starting_balance + total_realized_pnl
                logger.info(f"[PaperBroker] Hydrated {len(self.trade_history)} trades from Turso Cloud. Adjusted Balance: ₹{self.balance:,.2f}")
        except Exception as e:
            logger.warning(f"[PaperBroker] Cloud trade hydration deferred: {e}")

    def reset(self, starting_balance: float = 500000.0, per_market_capital: float = 100000.0):
        """Cleans out open positions and trade history and re-allocates starting capital (₹1,00,000 per market, ₹5,00,000 per mode)."""
        self.per_market_capital = float(per_market_capital)
        self.market_starting_cap = {m: self.per_market_capital for m in self.SUPPORTED_MARKETS}
        self.mode_starting_cap = {
            "SAFE": 500000.0,
            "MONEY_MAKER": 500000.0,
            "DANGEROUS": 500000.0
        }
        self.starting_balance = float(sum(self.market_starting_cap.values()))
        self.balance = self.starting_balance
        self.open_positions = {}
        self.trade_history = []
        logger.info(f"[PaperBroker] Account reset to ₹1,00,000 per market and ₹5,00,000 per mode (Total Starting: ₹{self.starting_balance:,.2f})")

    def get_mode_portfolio(self, mode: str) -> Dict[str, Any]:
        """Calculates dedicated ₹5,00,000 portfolio ledger for a trading mode (SAFE, MONEY_MAKER, DANGEROUS)."""
        clean_m = str(mode).upper()
        if "DANGEROUS" in clean_m or "WILD" in clean_m:
            m_key = "DANGEROUS"
            mode_display = "⚡ Dangerous Mode (Learning Lab)"
        elif "MONEY" in clean_m or "MAKER" in clean_m:
            m_key = "MONEY_MAKER"
            mode_display = "💰 Money Maker Mode (Multi-Setup)"
        else:
            m_key = "SAFE"
            mode_display = "🛡️ Safe Mode (Institutional Sniper)"

        start_cap = self.mode_starting_cap.get(m_key, 500000.0)

        def matches_mode(record_mode):
            rm = str(record_mode or "SAFE").upper()
            if m_key == "DANGEROUS":
                return "DANGEROUS" in rm or "WILD" in rm
            elif m_key == "MONEY_MAKER":
                return "MONEY" in rm or "MAKER" in rm
            else:
                return "SAFE" in rm or rm in ["CONSERVATIVE_SAFE", "NORMAL", ""]

        m_trades = [t for t in self.trade_history if matches_mode(t.get("trading_mode"))]
        m_positions = [p for p in self.open_positions.values() if matches_mode(p.get("trading_mode"))]

        realized_pnl = sum(float(t.get("realized_pnl", t.get("pnl", 0.0))) for t in m_trades)
        unrealized_pnl = sum(float(p.get("unrealized_pnl", 0.0)) for p in m_positions)
        total_pnl = realized_pnl + unrealized_pnl
        current_val = start_cap + total_pnl
        pnl_pct = round((total_pnl / max(1.0, start_cap)) * 100.0, 2)

        margin_used = sum(float(p.get("entry_price", 0.0)) * float(p.get("remaining_units", 1.0)) * 0.20 for p in m_positions)
        available_cash = max(0.0, current_val - margin_used)

        wins = [t for t in m_trades if float(t.get("realized_pnl", t.get("pnl", 0.0))) > 0]
        losses = [t for t in m_trades if float(t.get("realized_pnl", t.get("pnl", 0.0))) < 0]
        tot_closed = len(m_trades)
        win_rate = round((len(wins) / max(1, tot_closed)) * 100.0, 1) if tot_closed > 0 else 0.0

        return {
            "mode": m_key,
            "name": mode_display,
            "starting_capital": round(start_cap, 2),
            "current_value": round(current_val, 2),
            "equity": round(current_val, 2),
            "balance": round(start_cap + realized_pnl, 2),
            "total_pnl": round(total_pnl, 2),
            "realized_pnl": round(realized_pnl, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "pnl_percent": pnl_pct,
            "margin_used": round(margin_used, 2),
            "available_cash": round(available_cash, 2),
            "open_positions_count": len(m_positions),
            "total_trades_count": tot_closed,
            "wins_count": len(wins),
            "losses_count": len(losses),
            "win_rate_pct": win_rate,
            "open_positions": m_positions,
            "trade_history": m_trades[-30:]
        }

    def get_market_portfolio(self, market: str) -> Dict[str, Any]:
        """Calculates dedicated ₹1,00,000 portfolio book for an individual market."""
        m_key = market.upper()
        start_cap = self.market_starting_cap.get(m_key, self.per_market_capital)
        
        m_trades = [t for t in self.trade_history if str(t.get("market", "")).upper() == m_key]
        m_positions = [p for p in self.open_positions.values() if str(p.get("market", "")).upper() == m_key]
        
        realized_pnl = sum(float(t.get("realized_pnl", t.get("pnl", 0.0))) for t in m_trades)
        unrealized_pnl = sum(float(p.get("unrealized_pnl", 0.0)) for p in m_positions)
        total_pnl = realized_pnl + unrealized_pnl
        current_val = start_cap + total_pnl
        pnl_pct = round((total_pnl / max(1.0, start_cap)) * 100.0, 2)
        
        # Approximate margin in use (20% margin requirement or position size)
        margin_used = sum(float(p.get("entry_price", 0.0)) * float(p.get("remaining_units", 1.0)) * 0.20 for p in m_positions)
        available_cash = max(0.0, current_val - margin_used)
        
        wins = [t for t in m_trades if float(t.get("realized_pnl", t.get("pnl", 0.0))) > 0]
        losses = [t for t in m_trades if float(t.get("realized_pnl", t.get("pnl", 0.0))) < 0]
        tot_closed = len(m_trades)
        win_rate = round((len(wins) / max(1, tot_closed)) * 100.0, 1) if tot_closed > 0 else 0.0

        return {
            "market": m_key,
            "starting_capital": round(start_cap, 2),
            "current_value": round(current_val, 2),
            "equity": round(current_val, 2),
            "balance": round(start_cap + realized_pnl, 2),
            "total_pnl": round(total_pnl, 2),
            "realized_pnl": round(realized_pnl, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "pnl_percent": pnl_pct,
            "margin_used": round(margin_used, 2),
            "available_cash": round(available_cash, 2),
            "open_positions_count": len(m_positions),
            "total_trades_count": tot_closed,
            "wins_count": len(wins),
            "losses_count": len(losses),
            "win_rate_pct": win_rate
        }

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Returns institutional aggregated portfolio metrics across all markets.
        Guarantees mathematical integrity: Equity = Starting Capital + Total P&L.
        """
        total_realized_pnl = sum(float(t.get("realized_pnl", t.get("pnl", 0.0))) for t in self.trade_history)
        unrealized_pnl = sum(float(p.get("unrealized_pnl", 0.0)) for p in self.open_positions.values())
        total_pnl = total_realized_pnl + unrealized_pnl
        
        total_starting = sum(self.market_starting_cap.values())
        equity = total_starting + total_pnl
        cash_balance = total_starting + total_realized_pnl
        
        total_closed = len(self.trade_history)
        winning_trades = [t for t in self.trade_history if float(t.get("realized_pnl", t.get("pnl", 0.0))) > 0]
        losing_trades = [t for t in self.trade_history if float(t.get("realized_pnl", t.get("pnl", 0.0))) < 0]
        win_rate = round((len(winning_trades) / max(1, total_closed) * 100.0), 1) if total_closed > 0 else 0.0
        
        margin_in_use = sum(float(p.get("entry_price", 0.0)) * float(p.get("remaining_units", 1.0)) * 0.20 for p in self.open_positions.values())
        available_cash = max(0.0, equity - margin_in_use)

        avg_trade_eff = 0.0
        if total_closed > 0:
            effs = [float(t.get("execution_quality", {}).get("trade_efficiency_pct", 0.0)) for t in self.trade_history]
            avg_trade_eff = round(sum(effs) / total_closed, 1)

        market_portfolios = {m: self.get_market_portfolio(m) for m in self.SUPPORTED_MARKETS}
        mode_portfolios = {m: self.get_mode_portfolio(m) for m in ["SAFE", "MONEY_MAKER", "DANGEROUS"]}

        return {
            "starting_balance": round(total_starting, 2),
            "starting_capital": round(total_starting, 2),
            "balance": round(cash_balance, 2),
            "equity": round(equity, 2),
            "current_capital": round(equity, 2),
            "total_pnl": round(total_pnl, 2),
            "total_realized_pnl": round(total_realized_pnl, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "pnl_percent": round((total_pnl / max(1.0, total_starting)) * 100.0, 2),
            "margin_used": round(margin_in_use, 2),
            "available_cash": round(available_cash, 2),
            "open_positions_count": len(self.open_positions),
            "total_trades_count": total_closed,
            "wins_count": len(winning_trades),
            "losses_count": len(losing_trades),
            "win_rate_pct": win_rate,
            "avg_trade_efficiency_pct": avg_trade_eff,
            "market_portfolios": market_portfolios,
            "mode_portfolios": mode_portfolios
        }

    @classmethod
    def calculate_hft_queue_fill_probability(
        cls,
        limit_price: float,
        high: float,
        low: float,
        candle_volume: float,
        direction: str = "LONG",
        estimated_queue_depth: float = 50.0,
        l2_ofi_imbalance: float = 0.0
    ) -> Dict[str, Any]:
        """
        HFT Queue Position & Adverse Selection Simulator (inspired by hftbacktest).
        Calculates realistic fill probability based on price penetration and volume clearance.
        """
        if direction.upper() == "LONG":
            penetration_pct = (limit_price - low) / max(1e-6, limit_price) * 100.0
        else:
            penetration_pct = (high - limit_price) / max(1e-6, limit_price) * 100.0

        if penetration_pct >= 0.05:
            fill_prob = 1.0
            fill_status = "CLEARED_THROUGH_QUEUE"
        elif penetration_pct >= 0.0:
            clearance_ratio = candle_volume / max(1.0, estimated_queue_depth)
            imbalance_factor = 1.0 + (l2_ofi_imbalance if direction.upper() == "LONG" else -l2_ofi_imbalance)
            fill_prob = min(0.95, max(0.15, (clearance_ratio * 0.5) * max(0.2, imbalance_factor)))
            fill_status = "PROBABILISTIC_QUEUE_CLEARANCE"
        else:
            fill_prob = 0.0
            fill_status = "PRICE_NOT_REACHED"

        return {
            "fill_probability": round(fill_prob, 2),
            "fill_status": fill_status,
            "penetration_pct": round(penetration_pct, 4),
            "is_filled": fill_prob >= 0.70
        }

    def execute_market_order(
        self,
        market: str,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit_1: float,
        take_profit_2: float,
        units: float,
        dollar_risk: float,
        risk_pct: float,
        strategy_name: str,
        market_regime: str = "TRENDING",
        atr_pct: float = 1.5,
        in_killzone: bool = False,
        adx_value: float = 22.0,
        trade_type: str = "INTRADAY",
        trading_mode: str = "SAFE"
    ) -> Dict[str, Any]:
        """
        Executes order with dynamic volatility-scaled slippage, HFT queue modeling,
        STT/brokerage fee schedule, and initializes MAE/MFE tracking.
        """
        base_slip = self.SLIPPAGE_RATES.get(market.upper(), 0.0002)
        vol_mult = 1.0 + max(0.0, (atr_pct - 1.0) / 2.0)
        dynamic_slip_rate = base_slip * vol_mult
        fee_rate = self.FEE_RATES.get(market.upper(), 0.0005)

        # Apply dynamic slippage
        if direction.upper() == "LONG":
            exec_price = entry_price * (1.0 + dynamic_slip_rate)
        else:
            exec_price = entry_price * (1.0 - dynamic_slip_rate)

        slip_info = ExecutionQualityMetrics.calculate_slippage(entry_price, exec_price)

        entry_fee = (exec_price * units) * fee_rate
        self.balance -= entry_fee

        # Calculate Indian Breakeven if Indian stock
        breakeven_info = {}
        if market.upper() == "INDIAN_STOCKS":
            breakeven_info = ExecutionQualityMetrics.calculate_indian_breakeven(direction, exec_price, units)

        trade_id = str(uuid.uuid4())[:8]
        position = {
            "trade_id": trade_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "market": market,
            "symbol": symbol,
            "direction": direction.upper(),
            "intended_entry_price": entry_price,
            "entry_price": exec_price,
            "current_price": exec_price,
            "initial_stop_loss": stop_loss,
            "stop_loss": stop_loss,
            "take_profit_1": take_profit_1,
            "take_profit_2": take_profit_2,
            "initial_units": units,
            "remaining_units": units,
            "dollar_risk": dollar_risk,
            "risk_pct": risk_pct,
            "strategy_name": strategy_name,
            "trade_type": trade_type,
            "trading_mode": trading_mode,
            "holding_mode": "3_TIER_SCALE_OUT_WITH_CHANDELIER_RUNNER",
            "can_exit_in_1_bar": True,
            "bars_held": 0,
            "sl_state": "ORIGINAL",  # ORIGINAL | BREAKEVEN | TRAILING_1R_LOCK | CHANDELIER_RUNNER_TRAIL
            "tp1_closed": False,
            "tp2_closed": False,
            "unrealized_pnl": 0.0,
            "unrealized_r": 0.0,
            "fees_paid": entry_fee,
            "entry_slippage_pct": slip_info["slippage_pct"],
            "mae_price": exec_price,    # Maximum Adverse Excursion price
            "mfe_price": exec_price,    # Maximum Favorable Excursion price
            "peak_price": exec_price,   # For trailing stops
            "trough_price": exec_price,
            "breakeven_details": breakeven_info
        }

        self.open_positions[trade_id] = position
        LiveTradeWorkingMemory().activate_trade(position)
        logger.info(
            f"[PaperBroker] 🚀 POSITION OPENED [{direction} {symbol}] at ${exec_price:,.2f} "
            f"(Slip: {slip_info['slippage_pct']:.3f}%) | SL: ${stop_loss:,.2f} | Mode: 3-TIER SCALE-OUT"
        )

        return position

    def force_close_position(
        self,
        trade_id: str,
        reason: str = "EMERGENCY_FORCE_CLOSE",
        exit_price: Optional[float] = None,
        exit_type: str = "EMERGENCY_EARLY_EXIT"
    ) -> Optional[Dict[str, Any]]:
        """
        Instantly liquidates an open position in the paper broker.
        Can be triggered by CEO Supreme Agent, Risk Shield, or News UpGuard mid-trade.
        """
        if trade_id not in self.open_positions:
            return None

        pos = self.open_positions[trade_id]
        direction = pos["direction"]
        entry_p = pos["entry_price"]
        fee_rate = self.FEE_RATES.get(pos.get("market", "CRYPTO").upper(), 0.0005)
        
        p_exit = float(exit_price or pos.get("current_price") or entry_p)

        # Apply slippage on exit
        if direction == "LONG":
            exec_exit = p_exit * (1.0 - 0.0002)
            gross_pnl = (exec_exit - entry_p) * pos["remaining_units"]
        else:
            exec_exit = p_exit * (1.0 + 0.0002)
            gross_pnl = (entry_p - exec_exit) * pos["remaining_units"]

        exit_fee = (exec_exit * pos["remaining_units"]) * fee_rate
        net_pnl = gross_pnl - exit_fee
        self.balance += net_pnl

        # Execution quality metrics
        exec_quality = ExecutionQualityMetrics.calculate_efficiency_metrics(
            direction=direction,
            entry_price=entry_p,
            exit_price=exec_exit,
            mae_price=pos.get("mae_price", entry_p),
            mfe_price=pos.get("mfe_price", entry_p)
        )

        r_mult = round(gross_pnl / pos["dollar_risk"], 2) if pos.get("dollar_risk", 0) > 0 else 0.0

        closed_record = {
            "trade_id": trade_id,
            "symbol": pos["symbol"],
            "market": pos["market"],
            "trading_mode": pos.get("trading_mode", "SAFE"),
            "direction": direction,
            "strategy_name": pos["strategy_name"],
            "trade_type": pos.get("trade_type", "INTRADAY"),
            "entry_price": round(entry_p, 2),
            "exit_price": round(exec_exit, 2),
            "initial_stop_loss": round(float(pos["initial_stop_loss"]), 2),
            "final_stop_loss": round(float(pos["stop_loss"]), 2),
            "bars_held": pos["bars_held"],
            "realized_pnl": round(net_pnl, 2),
            "r_multiple": r_mult,
            "exit_reason": reason,
            "exit_type": exit_type,
            "fees_paid": round(pos["fees_paid"] + exit_fee, 2),
            "entry_slippage_pct": pos.get("entry_slippage_pct", 0.0),
            "execution_quality": exec_quality,
            "timestamp_close": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        self.trade_history.append(closed_record)
        del self.open_positions[trade_id]

        LiveTradeWorkingMemory().close_and_archive_trade(closed_record)
        Mem0MemoryEngine().record_episodic_trade(closed_record)

        # Real-time Cloud Sync to Turso Edge Database
        try:
            from shared_brain.turso_sync import turso_client
            turso_client.sync_trade({
                "trade_id": closed_record.get("trade_id"),
                "symbol": closed_record.get("symbol"),
                "market": closed_record.get("market", "GLOBAL"),
                "side": closed_record.get("direction"),
                "entry_price": closed_record.get("entry_price"),
                "exit_price": closed_record.get("exit_price"),
                "quantity": closed_record.get("initial_size"),
                "pnl": closed_record.get("realized_pnl"),
                "pnl_percent": closed_record.get("pnl_percent", 0.0),
                "strategy": closed_record.get("strategy", "Dynamic Quant Alpha"),
                "exit_reason": closed_record.get("exit_reason"),
                "confidence": 0.85,
                "time": closed_record.get("timestamp_close")
            })
            turso_client.sync_neural_memory({
                "id": f"MEM-{closed_record.get('trade_id')}",
                "trade_id": closed_record.get("trade_id"),
                "symbol": closed_record.get("symbol"),
                "outcome": "WIN" if closed_record.get("realized_pnl", 0) > 0 else "LOSS",
                "pnl": closed_record.get("realized_pnl"),
                "regime": closed_record.get("market", "Trend"),
                "lesson": f"Closed via {closed_record.get('exit_reason')}. Execution efficiency: {exec_quality.get('trade_efficiency_pct', 0)}%.",
                "counterfactual_note": f"R-Multiple: {r_mult}R on bar #{pos.get('bars_held', 1)}"
            })
        except Exception as e:
            logger.debug(f"[PaperBroker] Turso sync notice: {e}")

        emoji = "✅" if net_pnl > 0 else ("⚡" if exit_type == "EMERGENCY_EARLY_EXIT" else "❌")
        logger.info(
            f"[PaperBroker] {emoji} POSITION CLOSED [{direction} {pos['symbol']}] on Bar #{pos['bars_held']} | "
            f"PnL: ${net_pnl:,.2f} ({r_mult}R) | Trade Eff: {exec_quality['trade_efficiency_pct']}% "
            f"(Entry: {exec_quality['entry_quality_score']}/10, Exit: {exec_quality['exit_quality_score']}/10) | "
            f"Reason: {reason}"
        )
        return closed_record

    def update_positions_on_candle(
        self,
        symbol: str,
        current_price: float,
        recent_df: pd.DataFrame,
        adx_value: float = 22.0,
        macro_news_alert: Optional[Dict[str, Any]] = None,
        learned_guidance: Optional[Dict[str, Any]] = None,
        is_intraday_square_off_time: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Evaluates open positions bar-by-bar:
        1. Updates MAE (Worst intra-trade drawdown) and MFE (Peak favorable price).
        2. Evaluates 3-Tier scale-outs via TradeLifecycleManager.
        3. Evaluates micro structural invalidations via ActiveTradeMonitor.
        4. Calculates institutional ExecutionQualityMetrics on close.
        """
        closed_events = []
        fee_rate = 0.0005

        # Extract current candle high/low if available
        candle_high = current_price
        candle_low = current_price
        atr_val = current_price * 0.015
        if not recent_df.empty:
            last_row = recent_df.iloc[-1]
            candle_high = float(last_row.get("high", current_price))
            candle_low = float(last_row.get("low", current_price))
            if "atr" in recent_df.columns:
                atr_val = float(recent_df.iloc[-1]["atr"])

        for trade_id, pos in list(self.open_positions.items()):
            if pos["symbol"] != symbol:
                continue

            pos["bars_held"] += 1
            pos["current_price"] = current_price
            direction = pos["direction"]
            units = pos["remaining_units"]
            entry_p = pos["entry_price"]

            # Step 1: Update MAE & MFE (Section 10)
            if direction == "LONG":
                pos["mae_price"] = min(pos["mae_price"], candle_low)
                pos["mfe_price"] = max(pos["mfe_price"], candle_high)
                pos["peak_price"] = max(pos["peak_price"], candle_high)
                pos["unrealized_pnl"] = (current_price - entry_p) * units
            else:
                pos["mae_price"] = max(pos["mae_price"], candle_high)
                pos["mfe_price"] = min(pos["mfe_price"], candle_low)
                pos["peak_price"] = min(pos["peak_price"], candle_low)
                pos["unrealized_pnl"] = (entry_p - current_price) * units

            # Sync with Short-Term Live Working Memory Agent
            curr_r = round(pos["unrealized_pnl"] / pos["dollar_risk"], 2) if pos["dollar_risk"] > 0 else 0.0
            pos["unrealized_r"] = curr_r
            LiveTradeWorkingMemory().update_live_position_tick(
                current_price=current_price,
                bars_held=pos["bars_held"],
                unrealized_pnl=pos["unrealized_pnl"],
                unrealized_r=curr_r,
                stop_loss=pos["stop_loss"],
                sl_state=pos["sl_state"],
                mae_price=pos["mae_price"],
                mfe_price=pos["mfe_price"],
                tier_1_banked=pos["tp1_closed"],
                tier_2_banked=pos["tp2_closed"]
            )

            # Step 2: Evaluate through TradeLifecycleManager (3-Tier scaling & trailing stops)
            lifecycle_decision = TradeLifecycleManager.evaluate_lifecycle_state(
                position=pos,
                current_price=current_price,
                atr_value=atr_val,
                bars_held=pos["bars_held"],
                is_intraday_square_off_time=is_intraday_square_off_time
            )

            # Step 3: Evaluate through ActiveTradeMonitor (structure traps, rejection wicks)
            monitor_decision = ActiveTradeMonitor.evaluate_active_position(
                position=pos,
                recent_df=recent_df,
                current_price=current_price,
                adx_value=adx_value,
                macro_news_alert=macro_news_alert,
                learned_guidance=learned_guidance
            )

            # Reconcile decisions (Prioritize safety/exits)
            chosen_action = lifecycle_decision.get("action", "HOLD")
            chosen_reason = lifecycle_decision.get("reason", "")
            exit_price = lifecycle_decision.get("exit_price", current_price)

            if monitor_decision.get("action") in ["CLOSE_POSITION", "EMERGENCY_EARLY_EXIT"]:
                chosen_action = monitor_decision["action"]
                chosen_reason = monitor_decision.get("reason", "Structural invalidation")
                exit_price = monitor_decision.get("exit_price", current_price)

            # Handle Actions
            if chosen_action == "UPDATE_STOP_LOSS":
                pos["stop_loss"] = lifecycle_decision.get("new_stop_loss", pos["stop_loss"])
                pos["sl_state"] = lifecycle_decision.get("sl_state", pos["sl_state"])
                logger.info(
                    f"[PaperBroker] 🛡️ Trailing Stop updated for {pos['symbol']} on Bar #{pos['bars_held']} "
                    f"-> ${pos['stop_loss']:,.2f} ({pos['sl_state']})"
                )

            elif chosen_action == "TAKE_PROFIT_PARTIAL":
                portion = lifecycle_decision.get("portion", 0.33)
                tier = lifecycle_decision.get("tier", 1)
                closed_units = pos["remaining_units"] * portion
                p_exit = lifecycle_decision.get("exit_price", current_price)

                if direction == "LONG":
                    realized_chunk = (p_exit - entry_p) * closed_units
                else:
                    realized_chunk = (entry_p - p_exit) * closed_units

                fee = (p_exit * closed_units) * fee_rate
                net_realized = realized_chunk - fee
                self.balance += net_realized
                pos["remaining_units"] -= closed_units
                pos["fees_paid"] += fee

                if tier == 1:
                    pos["tp1_closed"] = True
                    pos["stop_loss"] = lifecycle_decision.get("new_stop_loss", entry_p)
                    pos["sl_state"] = "BREAKEVEN"
                    logger.info(
                        f"[PaperBroker] 💰 TIER 1 PROFIT BANKED for {pos['symbol']} on Bar #{pos['bars_held']}: "
                        f"+${net_realized:,.2f} (33%). SL locked at Breakeven."
                    )
                elif tier == 2:
                    pos["tp2_closed"] = True
                    pos["stop_loss"] = lifecycle_decision.get("new_stop_loss", pos["stop_loss"])
                    pos["sl_state"] = "TRAILING_1R_LOCK"
                    logger.info(
                        f"[PaperBroker] 💰 TIER 2 PROFIT BANKED for {pos['symbol']} on Bar #{pos['bars_held']}: "
                        f"+${net_realized:,.2f} (33%). SL locked at +1.0R."
                    )

            elif chosen_action in ["CLOSE_POSITION", "EMERGENCY_EARLY_EXIT"]:
                closed_rec = self.force_close_position(
                    trade_id=trade_id,
                    reason=chosen_reason,
                    exit_price=exit_price,
                    exit_type=chosen_action
                )
                if closed_rec:
                    closed_events.append(closed_rec)

        return closed_events
