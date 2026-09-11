"""
Execution Sniper & 50-Year Master Trader Execution Agent
Implements the Complete 13-Section Master Trader Knowledge Base:

1. EXECUTION PHILOSOPHY: Exit is everything, precision over speed, pre-planned execution, no emotion.
2. PRE-EXECUTION PREPARATION: HTF bias, key levels, margin check, daily loss limit & max trades limiter.
3. ENTRY EXECUTION SYSTEM: 4 Order Types (Limit, Market, Stop-Limit, Stop-Market), 5 Timing Models, 8-Tier Entry Trigger Hierarchy.
4. EXIT EXECUTION SYSTEM: Hard SL, 3-tier partial scale-outs (33% at 1.0R -> BE, 33% at 2.0R -> +1.0R, 34% runner on Chandelier trail).
5. EXECUTION TIMING: Indian NSE/BSE session windows (9:15-9:30 AM avoidance, 9:30-11:30 AM prime, 11:30-1:00 PM lull, 2:30-3:15 PM power hour, 3:00 PM square-off), Crypto kill zones, and News Blackout.
6. ORDER TYPES: Master-level order mechanics with anti-chase guard (<0.5% drift).
7. TRADE MANAGEMENT: First 30-min rule, Anti-Martingale pyramiding (never add to losers).
8. TRADE TYPES: Scalp (1M-5M), Intraday (15M-1H), Swing (4H-Daily), Positional (Weekly).
9. EXECUTION MATH: Position sizing, STT/taxes breakeven calculator, R-multiples, portfolio heat.
10. EXECUTION QUALITY MEASUREMENT: Slippage per trade, MAE, MFE, Entry Efficiency %, Exit Efficiency %, Trade Efficiency %, Quality Scores (1-10).
11. FAILURE MODES & FIXES: Anti-chase, Hard SL, Auto-cooldowns.
12. PLATFORM & TOOLS SETUP: Institutional 1-click & bracket safeguards.
13. INTER-AGENT INTEGRATION: Complete input/output wiring with Strategy, Risk, Analytical, News, and Sump Agents.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import time
import datetime
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from agents.execution_agent.paper_broker import PaperBroker
from agents.execution_agent.sump_agent import SumpAgent
from agents.execution_agent.session_timing_controller import SessionTimingController
from agents.execution_agent.order_routing_engine import OrderRoutingEngine
from agents.execution_agent.execution_quality_metrics import ExecutionQualityMetrics
from agents.execution_agent.trade_lifecycle_manager import TradeLifecycleManager
from agents.execution_agent.news_execution_upguard import NewsExecutionUpGuard
from shared_brain.omni_calculator import OmniCalculator

logger = logging.getLogger("ExecutionAgent")


class ExecutionAgent:
    """
    50-Year Master Trader Execution Agent.
    Unifies Order Routing, Session Timing, Lifecycle Management,
    Execution Quality Analytics, Sump Agent Post-Trade Forensics,
    and Real-Time News UpGuard Crisis Interception.
    """

    def __init__(self, starting_balance: float = 100000.0, max_daily_trades: int = 10):
        self.calc = OmniCalculator(owner="ExecutionAgent")
        self.broker = PaperBroker(starting_balance)
        self.sump_agent = SumpAgent()
        self.session_controller = SessionTimingController()
        self.order_router = OrderRoutingEngine()
        self.quality_metrics = ExecutionQualityMetrics()
        self.lifecycle_manager = TradeLifecycleManager()
        self.upguard = NewsExecutionUpGuard()

        # Section 2 & 11: Daily Limits & Cooldowns
        self.max_daily_trades = max_daily_trades
        self.daily_trades_count = 0
        self.daily_realized_loss = 0.0
        self.max_daily_loss = starting_balance * 0.03  # 3.0% hard daily circuit breaker
        self.current_trading_day = datetime.date.today().isoformat()

    def _reset_daily_limits_if_needed(self):
        """Resets daily counters at the start of a new calendar day."""
        today = datetime.date.today().isoformat()
        if today != self.current_trading_day:
            self.current_trading_day = today
            self.daily_trades_count = 0
            self.daily_realized_loss = 0.0
            logger.info(f"[ExecutionAgent] 🌅 New trading day initialized ({today}). Limits reset.")

    def process_order(
        self,
        risk_approval: Dict[str, Any],
        strategy_decision: Dict[str, Any],
        market: str,
        symbol: str,
        market_regime: str = "TRENDING",
        atr_pct: float = 1.5,
        in_killzone: bool = False,
        adx_value: float = 22.0,
        trade_type: str = "INTRADAY",
        analytical_report: Optional[Dict[str, Any]] = None,
        is_news_pending: bool = False,
        simulated_time: Optional[datetime.datetime] = None
    ) -> Dict[str, Any]:
        """
        Executes order after passing all 50-Year Master Trader filters:
        1. Daily circuit breaker check (max daily loss & max daily trades)
        2. Session Timing Gate (Avoids opening volatility 9:15-9:45 AM & news blackouts)
        3. Anti-Chase Protection (Blocks entries that drifted >0.5%)
        4. 8-Tier Entry Trigger Hierarchy Gate (Requires score >= 4/8)
        5. Order Routing Type Selection (Limit / Market / Stop-Limit)
        """
        self._reset_daily_limits_if_needed()

        # Step 1: Risk Approval Check
        if risk_approval.get("decision") != "APPROVED":
            return {"status": "SKIPPED", "reason": f"Risk Agent rejected: {risk_approval.get('reason')}"}

        # Step 2: Daily Circuit Breaker Check (Section 2 & 11)
        if self.daily_trades_count >= self.max_daily_trades:
            return {
                "status": "BLOCKED",
                "reason": f"Overtrading protection: Reached max daily trades limit ({self.max_daily_trades})."
            }
        if self.daily_realized_loss >= self.max_daily_loss:
            return {
                "status": "BLOCKED",
                "reason": f"Daily loss circuit breaker hit: -${self.daily_realized_loss:,.2f} >= max -${self.max_daily_loss:,.2f}."
            }

        # Step 3: Session Timing Controller Evaluation (Section 5)
        session_eval = self.session_controller.evaluate_session_timing(
            market=market,
            simulated_time_ist=simulated_time,
            is_news_pending=is_news_pending
        )
        if not session_eval["can_execute"]:
            return {
                "status": "POSTPONED",
                "reason": f"Session Timing Guard: {session_eval['reason']} ({session_eval['session_name']})"
            }

        direction = strategy_decision.get("direction", "LONG").upper()
        entry_price = float(strategy_decision.get("entry_price", 0.0))
        stop_loss = float(strategy_decision.get("stop_loss", 0.0))
        tp1 = float(strategy_decision.get("take_profit_1", 0.0))
        tp2 = float(strategy_decision.get("take_profit_2", 0.0))
        strat_name = strategy_decision.get("champion_strategy", {}).get("name", "DISCRETIONARY_SETUP")

        units = float(risk_approval.get("units", 0.0))
        dollar_risk = float(risk_approval.get("dollar_risk", 0.0))
        risk_pct = float(risk_approval.get("risk_pct", 1.0))

        # Step 4: Anti-Chase Protection (Section 3 rule)
        current_market_price = float(analytical_report.get("current_price", entry_price)) if analytical_report else entry_price
        chase_check = self.order_router.validate_anti_chase(direction, entry_price, current_market_price)
        if chase_check["chasing"]:
            return {
                "status": "REJECTED_CHASING",
                "reason": chase_check["reason"]
            }

        # Step 5: 8-Tier Entry Trigger Hierarchy Evaluation (Section 3)
        ar = analytical_report or {}
        htf_bias_aligned = (strategy_decision.get("macro_bias", "NEUTRAL") == ("BULLISH" if direction == "LONG" else "BEARISH"))
        price_at_key_level = (ar.get("at_key_level") is not False)
        session_ok = session_eval["can_execute"]
        liquidity_swept = (ar.get("liquidity_sweep", {}).get("status") == "CONFIRMED" or ar.get("smc_analysis", {}).get("sweep_detected") is True)
        displacement_candle = (ar.get("displacement_candle") is not False)
        candlestick_pattern_confirmed = bool(ar.get("chart_pattern") or ar.get("candlestick_pattern"))
        ltf_structure_shift = (ar.get("structure_shift_choch") is not False)
        sl_and_rr_valid = (stop_loss > 0.0 and abs(entry_price - stop_loss) > 0.0)

        trigger_hierarchy = self.order_router.evaluate_entry_trigger_hierarchy(
            htf_bias_aligned=htf_bias_aligned,
            price_at_key_level=price_at_key_level,
            session_timing_ok=session_ok,
            liquidity_swept=liquidity_swept,
            displacement_candle=displacement_candle,
            candlestick_pattern_confirmed=candlestick_pattern_confirmed,
            ltf_structure_shift=ltf_structure_shift,
            sl_defined_and_rr_valid=sl_and_rr_valid
        )

        if not trigger_hierarchy["can_enter"]:
            return {
                "status": "REJECTED_HIERARCHY",
                "reason": f"Entry Trigger Hierarchy Score {trigger_hierarchy['score']}/8 too low. Setup lacks institutional edge."
            }

        # Step 6: Order Type Selection (Section 6)
        timing_method = strategy_decision.get("timing_method", "CANDLE_CLOSE")
        order_type_spec = self.order_router.select_order_type(market, timing_method)

        # Step 7: Execution via PaperBroker
        pos = self.broker.execute_market_order(
            market=market,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            units=units,
            dollar_risk=dollar_risk,
            risk_pct=risk_pct,
            strategy_name=strat_name,
            market_regime=market_regime,
            atr_pct=atr_pct,
            in_killzone=session_eval["is_killzone"],
            adx_value=adx_value,
            trade_type=trade_type
        )

        self.daily_trades_count += 1
        pos["order_routing"] = order_type_spec
        pos["trigger_hierarchy"] = trigger_hierarchy
        pos["session_phase"] = session_eval["session_name"]

        return {
            "status": "EXECUTED",
            "position": pos,
            "hierarchy_score": f"{trigger_hierarchy['score']}/8 ({trigger_hierarchy['rating']})",
            "session_phase": session_eval["session_name"]
        }

    # Aliases
    execute_trade = process_order

    def on_candle_tick(
        self,
        symbol: str,
        current_price: float,
        recent_df: pd.DataFrame,
        adx_value: float = 22.0,
        macro_news_alert: Optional[Dict[str, Any]] = None,
        learned_guidance: Optional[Dict[str, Any]] = None,
        simulated_time: Optional[datetime.datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Active Trade Surveillance:
        1. Evaluates session timing for mandatory intraday square-off (3:00 PM IST).
        2. Evaluates active trades with 3-tier partial scale-outs, trailing stops, and micro invalidations.
        3. Updates MAE (Maximum Adverse Excursion) and MFE (Maximum Favorable Excursion) live.
        4. Calculates institutional Execution Quality Metrics (efficiencies & scores) on trade close.
        5. Transmits closed trade data directly to SUMP AGENT for counterfactual forensic lab audit.
        """
        self._reset_daily_limits_if_needed()

        # Step A: Check session square-off requirement
        # Check market type of any open position for this symbol
        matching_market = "CRYPTO"
        for p in self.broker.open_positions.values():
            if p["symbol"] == symbol:
                matching_market = p.get("market", "CRYPTO")
                break

        session_eval = self.session_controller.evaluate_session_timing(
            market=matching_market,
            simulated_time_ist=simulated_time
        )
        is_square_off_time = session_eval.get("intraday_square_off_required", False)

        # Step B: Update positions in PaperBroker
        closed_trades = self.broker.update_positions_on_candle(
            symbol=symbol,
            current_price=current_price,
            recent_df=recent_df,
            adx_value=adx_value,
            macro_news_alert=macro_news_alert,
            learned_guidance=learned_guidance,
            is_intraday_square_off_time=is_square_off_time
        )

        # Step C: Post-trade Sump Forensics & Daily Loss Ledger
        for trade in closed_trades:
            pnl = float(trade.get("realized_pnl", 0.0))
            if pnl < 0.0:
                self.daily_realized_loss += abs(pnl)

            # Hand off to Sump Agent for counterfactual deep investigation
            forensic_report = self.sump_agent.run_post_trade_forensics(
                closed_trade=trade,
                full_candles_df=recent_df,
                macro_news_context=macro_news_alert
            )
            trade["sump_forensics"] = forensic_report
            logger.info(
                f"[ExecutionAgent] 🔬 Sump Agent completed forensics for {trade['symbol']} ({trade['trade_id']}). "
                f"Entry Eff: {trade.get('execution_quality', {}).get('entry_efficiency_pct', 0)}%, "
                f"Exit Eff: {trade.get('execution_quality', {}).get('exit_efficiency_pct', 0)}%"
            )

            # Synchronize with Long-Term Evolution Memory & Mem0 Knowledge Store
            try:
                from agents.evolution_memory.agent import EvolutionMemoryAgent
                from agents.evolution_memory.mem0_memory_engine import Mem0MemoryEngine
                EvolutionMemoryAgent().log_trade_post_mortem(trade)
                Mem0MemoryEngine().record_episodic_trade(trade)
            except Exception as e:
                logger.error(f"[ExecutionAgent] Evolution memory sync error: {e}")

        return closed_trades

    update_open_positions = on_candle_tick

    def pyramid_position(
        self,
        trade_id: str,
        current_equity: float,
        has_new_bos: bool,
        add_units: float,
        add_risk: float
    ) -> Dict[str, Any]:
        """
        Anti-Martingale Pyramiding API (Section 7).
        Enforces addition only to winning positions, after confirmed BOS, with reduced size and risk <= 2%.
        """
        pos = self.broker.open_positions.get(trade_id)
        if not pos:
            return {"status": "FAILED", "reason": "Trade ID not found in open positions."}

        verdict = self.lifecycle_manager.validate_pyramid_addition(
            position=pos,
            has_new_bos=has_new_bos,
            current_equity=current_equity,
            proposed_add_units=add_units,
            proposed_add_risk=add_risk
        )

        if not verdict["can_pyramid"]:
            return {"status": "REJECTED", "reason": verdict["reason"]}

        pos["remaining_units"] += add_units
        pos["dollar_risk"] += add_risk
        logger.info(f"[ExecutionAgent] 🔺 PYRAMID ADDITION SUCCESSFUL for {pos['symbol']} (+{add_units} units).")
        return {"status": "SUCCESS", "new_units": pos["remaining_units"], "reason": verdict["reason"]}

    def intercept_breaking_macro_news(self, news_alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Real-Time News UpGuard:
        Directly receives breaking news alerts from News Agent and executes
        immediate protective measures across pending orders and active positions.
        """
        open_positions = list(self.broker.open_positions.values())
        threat_eval = self.upguard.evaluate_breaking_news_threat(news_alert)
        defensive_plan = self.upguard.determine_defensive_actions(
            threat_assessment=threat_eval,
            open_positions=open_positions,
            has_pending_orders=len(self.broker.open_positions) > 0
        )

        if defensive_plan["interception_active"]:
            logger.warning(
                f"[ExecutionAgent] 🛡️ NEWS UPGUARD INTERCEPTION ACTIVE! Actions: {defensive_plan['actions_summary']}"
            )

            # Apply position defensive modifications in paper broker
            for trade_id, action_info in defensive_plan["position_actions"].items():
                if trade_id in self.broker.open_positions:
                    pos = self.broker.open_positions[trade_id]
                    act = str(action_info.get("action", ""))
                    sym_str = str(pos.get("symbol", "UNKNOWN"))
                    if act == "TIGHTEN_STOP_LOSS_TO_BREAKEVEN":
                        new_sl = float(action_info.get("new_stop_loss") or pos.get("entry_price") or 0.0)
                        pos["stop_loss"] = new_sl
                        pos["sl_state"] = "BREAKEVEN"
                        logger.info(f"[ExecutionAgent] 🛡️ Position {sym_str} SL tightened to Breakeven via News UpGuard.")
                    elif act == "EMERGENCY_EARLY_EXIT":
                        closed_rec = self.broker.force_close_position(
                            trade_id=trade_id,
                            reason=action_info.get("reason", "NEWS_UPGUARD_EMERGENCY_EXIT"),
                            exit_type="EMERGENCY_EARLY_EXIT"
                        )
                        if closed_rec:
                            logger.warning(
                                f"[ExecutionAgent] 🚨 Position {sym_str} EMERGENCY CLOSED via News UpGuard at "
                                f"${closed_rec['exit_price']:,.2f} | PnL: ${closed_rec['realized_pnl']:,.2f}!"
                            )

        return defensive_plan

    def force_close_trade(
        self,
        trade_id_or_symbol: str,
        reason: str = "CEO_SUPREME_FORCE_EXIT",
        exit_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Supreme force-close command invoked by CEO Agent or Human Commander.
        Immediately liquidates target trade or all trades matching the symbol.
        """
        closed_records = []
        target_ids = []

        if trade_id_or_symbol in self.broker.open_positions:
            target_ids.append(trade_id_or_symbol)
        else:
            for tid, pos in list(self.broker.open_positions.items()):
                if pos.get("symbol", "").upper() == trade_id_or_symbol.upper():
                    target_ids.append(tid)

        for tid in target_ids:
            rec = self.broker.force_close_position(
                trade_id=tid,
                reason=reason,
                exit_price=exit_price,
                exit_type="EMERGENCY_EARLY_EXIT"
            )
            if rec:
                closed_records.append(rec)
                logger.warning(f"[ExecutionAgent] ⚡ SUPREME FORCE-CLOSE executed on {rec['symbol']} ({tid}): {reason}")

        return closed_records

    def get_latest_sump_forensics(self) -> List[Dict[str, Any]]:
        """Returns recent Sump Agent forensic investigation records."""
        return self.sump_agent.forensic_records

    def get_optimal_strategy_parameters(self, strategy_name: str) -> Dict[str, Any]:
        """Returns self-tuned execution parameters derived from counterfactual forensic simulations."""
        return self.sump_agent.get_optimal_parameters_for_strategy(strategy_name)

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Returns portfolio performance metrics with daily limit indicators."""
        summary = self.broker.get_portfolio_summary()
        summary["daily_trades_count"] = self.daily_trades_count
        summary["max_daily_trades"] = self.max_daily_trades
        summary["daily_realized_loss"] = round(self.daily_realized_loss, 2)
        summary["max_daily_loss"] = round(self.max_daily_loss, 2)
        summary["daily_loss_limit_hit"] = self.daily_realized_loss >= self.max_daily_loss
        return summary

    def get_open_positions_list(self) -> List[Dict[str, Any]]:
        return list(self.broker.open_positions.values())


if __name__ == "__main__":
    exec_agent = ExecutionAgent(starting_balance=100000.0)
    print("Testing Execution Sniper & Sump Agent...")
    summary = exec_agent.get_portfolio_summary()
    print(f"Paper Broker Online - Balance: ${summary['balance']:,.2f} | Equity: ${summary['equity']:,.2f}")
    print(f"Open Positions: {len(exec_agent.get_open_positions_list())} | Daily Trades: {summary['daily_trades_count']}/{summary['max_daily_trades']}")


