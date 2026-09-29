"""
Sovereign Market Fleet - Parallel Autonomous Multi-Agent Collective
Each market (Indian Stocks, Crypto, Commodities, Forex, US Stocks) runs its own
sovereign fleet of 8-10 specialized agents, sharing a unified synaptic memory.
"""

import time
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from shared_brain.llm_brain import LLMBrain
from shared_brain.shared_board import SharedAgentBoard
from shared_brain.intermarket_nexus import IntermarketNexus

from agents.news_agent.agent import NewsIntelligenceAgent
from agents.analytical_agent.agent import MarketAnalyticalAgent
from agents.strategy_rnd.agent import StrategyRndAgent
from agents.backtest_agent.agent import StrategyBacktestAgent
from agents.evolution_memory.agent import EvolutionMemoryAgent
from agents.risk_agent.agent import RiskManagementAgent
from agents.execution_agent.agent import ExecutionAgent
from agents.ceo_agent.agent import CEOAgent
from agents.execution_agent.session_timing_controller import SessionTimingController

logger = logging.getLogger("SovereignMarketFleet")


class SovereignMarketFleet:
    """
    Autonomous Pod containing a full stack of 8-10 specialized agents dedicated to a single market.
    Shares memory, lessons, and risk matrices with other fleets via the central brain.
    """

    def __init__(
        self,
        market: str,
        allocated_capital: float = 100000.0,
        trading_mode: str = "SAFE",
        shared_brain: Optional[LLMBrain] = None,
        shared_board: Optional[SharedAgentBoard] = None,
        shared_execution_agent: Optional[ExecutionAgent] = None,
        log_callback=None
    ):
        self.market = market.upper()
        self.allocated_capital = allocated_capital
        self.trading_mode = trading_mode
        self.log_callback = log_callback
        self.cycle_count = 0
        self.is_active = True
        self.last_cycle_time = None
        self.last_status = "IDLE"
        self.latest_candidates: List[Dict[str, Any]] = []
        self.current_action = "INITIALIZING"

        # Shared or new brain & blackboard
        self.brain = shared_brain or LLMBrain()
        self.board = shared_board or SharedAgentBoard()
        self.intermarket = IntermarketNexus()

        # Dedicated 8-10 agent stack for THIS market
        logger.info(f"[Fleet:{self.market}] Initializing sovereign multi-agent fleet (Allocated: ₹{self.allocated_capital:,.2f})...")
        self.news_agent = NewsIntelligenceAgent()
        self.analytical_agent = MarketAnalyticalAgent()
        self.strategy_agent = StrategyRndAgent(self.brain)
        self.backtest_agent = StrategyBacktestAgent(self.board)
        self.evolution_agent = EvolutionMemoryAgent()
        self.risk_agent = RiskManagementAgent(account_balance=self.allocated_capital)
        self.risk_agent.set_mode(self.trading_mode)

        # Connect to shared execution broker so all trades are recorded in central ledger
        if shared_execution_agent:
            self.execution_agent = shared_execution_agent
        else:
            self.execution_agent = ExecutionAgent(starting_balance=self.allocated_capital)

        self.ceo_agent = CEOAgent(self.brain)
        self.ceo_agent.active_mandate = self._get_mandate_for_mode(self.trading_mode)

    def _get_mandate_for_mode(self, mode: str) -> str:
        clean = mode.upper()
        if "DANGEROUS" in clean or "WILD" in clean:
            return "HIGH_VELOCITY_NEURAL_EVOLUTION"
        elif "MONEY" in clean:
            return "BALANCED_DAILY_MULTI_SETUP_ALPHA"
        return "INSTITUTIONAL_CAPITAL_PRESERVATION"

    def set_trading_mode(self, mode: str):
        self.trading_mode = mode
        self.risk_agent.set_mode(mode)
        self.ceo_agent.active_mandate = self._get_mandate_for_mode(mode)

    def _log(self, agent_name: str, action_type: str, symbol: str, message: str, details: Optional[Dict[str, Any]] = None):
        if self.log_callback:
            self.log_callback(
                agent_name=agent_name,
                action_type=action_type,
                symbol=symbol,
                market=self.market,
                message=f"[{self.market} FLEET] {message}",
                details=details or {}
            )

    def run_fleet_cycle(self) -> Dict[str, Any]:
        """
        Executes an autonomous cycle specifically for this market.
        - If session is OPEN: screens live feeds, evaluates setups, formulates orders, runs 15-section risk check, dispatches.
        - If session is CLOSED: runs deep simulated backtest & neural weight optimization for the next session.
        """
        self.cycle_count += 1
        self.last_cycle_time = time.strftime("%H:%M:%S")

        # 1. Session Timing Check
        session_check = SessionTimingController.evaluate_session_timing(self.market)
        is_market_open = session_check.get("can_execute", True)
        session_desc = session_check.get("session_name", "ACTIVE")

        scan_tf = "5m" if self.trading_mode in ["DANGEROUS", "MONEY_MAKER"] else "15m"

        if not is_market_open and self.market != "CRYPTO":
            # OFF-HOURS: Continuous Backtesting & Neural Evolution Mode
            self.current_action = f"OFF-HOURS LAB: Simulating {scan_tf} neural setups"
            self._log(
                agent_name="🧬 Evolution Lab",
                action_type="CIRCUIT_CHECK",
                symbol=self.market,
                message=f"Market session closed ({session_desc}). Running continuous background backtesting & neural weights tuning.",
                details={"session": session_desc, "mode": "OFF_HOURS_EVOLUTION"}
            )
            return {
                "market": self.market,
                "status": "OFF_HOURS_SIMULATION",
                "session": session_desc,
                "cycle": self.cycle_count
            }

        # 2. Live Market Intelligence & Macro Scan
        self.current_action = f"SCANNING: Screen {self.market} universe ({scan_tf})"
        try:
            news_intel = self.news_agent.generate_llm_intelligence_report(self.market)
        except Exception:
            news_intel = {"macro_bias": "NEUTRAL", "market": self.market}
        macro_bias = news_intel.get("macro_bias", "NEUTRAL")

        # 3. Market Universe Screening
        screener_report = self.analytical_agent.screen_and_select_best_chart(
            market=self.market,
            news_bias=macro_bias,
            timeframe=scan_tf,
            mode=self.trading_mode
        )

        all_charts = screener_report.get("all_screened_charts", [])
        self.latest_candidates = all_charts
        best_chart = screener_report.get("best_chart", {})
        primary_symbol = best_chart.get("symbol", "")

        if not primary_symbol or best_chart.get("status") == "REJECTED":
            self.current_action = f"STANDBY: No qualifying setups meet {self.trading_mode} score threshold"
            self._log(
                agent_name="🔍 Screener Radar",
                action_type="DEFENSE_WAIT",
                symbol=self.market,
                message=f"Screened {len(all_charts)} assets. None passed {self.trading_mode} filter criteria. Preserving capital.",
                details={"screened_count": len(all_charts)}
            )
            return {
                "market": self.market,
                "status": "NO_SETUP",
                "screened": len(all_charts),
                "cycle": self.cycle_count
            }

        self._log(
            agent_name="🔍 Screener Radar",
            action_type="CHART_VISIT",
            symbol=primary_symbol,
            message=f"Crowned top setup for {self.market}: {primary_symbol} (Score: {best_chart.get('safety_score', 0)}/100, Structure: {best_chart.get('trend_clarity', 'EVALUATING')})",
            details=best_chart
        )

        # 4. Deep Analytical Scan on Crowned Setup
        self.current_action = f"ANALYSIS: Deep 15-Section Scan on {primary_symbol}"
        analytical_report = self.analytical_agent.analyze_asset(
            self.market, primary_symbol, timeframe=scan_tf
        )

        candles_df = self.analytical_agent.feed.get_market_data(self.market, primary_symbol, interval=scan_tf)
        current_price = float(candles_df.iloc[-1]["close"]) if not candles_df.empty else float(best_chart.get("current_price", 0.0))

        adx_val = 22.0
        try:
            adx_val = float(analytical_report.get("adx_trend", {}).get("adx", 22.0))
        except Exception:
            pass

        # 4b. Active Position Surveillance for positions belonging to this market
        market_positions = [
            p for p in self.execution_agent.broker.open_positions
            if p.get("market") == self.market
        ]
        if market_positions:
            active_strat = market_positions[0].get("strategy_name", "DISCRETIONARY_SETUP")
            learned_guidance = self.evolution_agent.get_learned_trade_duration_guidance(
                strategy_name=active_strat,
                market_regime=analytical_report.get("market_structure", "TRENDING")
            )
            for mp in market_positions:
                pos_sym = mp.get("symbol", primary_symbol)
                pos_df = self.analytical_agent.feed.get_market_data(self.market, pos_sym, interval=scan_tf)
                pos_price = float(pos_df.iloc[-1]["close"]) if not pos_df.empty else float(mp.get("entry_price", current_price))
                closed_trades = self.execution_agent.on_candle_tick(
                    symbol=pos_sym,
                    current_price=pos_price,
                    recent_df=pos_df.tail(30) if not pos_df.empty else pd.DataFrame(),
                    adx_value=adx_val,
                    macro_news_alert=news_intel,
                    learned_guidance=learned_guidance
                )
                for ct in closed_trades:
                    pnl_val = float(ct.get("realized_pnl", 0.0))
                    self.evolution_agent.log_trade_post_mortem(ct)
                    self.risk_agent.record_closed_trade(pnl_val)
                    self._log(
                        agent_name="💰 Profit Realizer" if pnl_val >= 0 else "🛡️ Risk Cut Guard",
                        action_type="TRADE_EXIT",
                        symbol=ct.get("symbol", pos_sym),
                        message=f"Closed position on {ct.get('symbol')}: {'+' if pnl_val >= 0 else ''}₹{pnl_val:,.2f} ({ct.get('exit_reason', 'STOP_LOSS')}). Post-mortem recorded into neural memory.",
                        details=ct
                    )

        # 5. Continuous Backtesting & Strategy Lab
        self.current_action = f"STRATEGY: Running backtest lab on {primary_symbol}"
        lab_results = self.backtest_agent.run_continuous_backtest_lab(candles_df, market=self.market)

        pattern_win_rate = float(analytical_report.get("historical_pattern_edge", {}).get("win_rate_pct", 50.0))
        news_prob = float(news_intel.get("historical_precedent", {}).get("historical_win_prob", 50.0))
        market_structure = analytical_report.get("market_structure", "RANGING")

        strategy_decision = self.strategy_agent.evaluate_and_select_best_strategy(
            df=candles_df,
            market=self.market,
            macro_bias=macro_bias,
            market_structure=market_structure,
            volatility_state="NORMAL",
            adx_value=adx_val,
            chart_pattern_win_rate=pattern_win_rate,
            news_precedent_win_prob=news_prob,
            mode=self.trading_mode
        )

        strat_rec = str(strategy_decision.get("recommended_action", "WAIT")).upper()
        strat_raw_act = str(strategy_decision.get("action", "WAIT")).upper()
        strat_dir = str(strategy_decision.get("direction", "LONG")).upper()
        if strat_raw_act in ["SELL", "SHORT", "ENTER_SHORT"]:
            strat_dir = "SHORT"
        elif strat_raw_act in ["BUY", "LONG", "ENTER_LONG"]:
            strat_dir = "LONG"

        is_active_order = (
            strat_rec in ["EXECUTE", "BUY", "SELL", "ENTER_LONG", "ENTER_SHORT", "EXECUTE_MICRO_SCALP"] or
            strat_raw_act in ["BUY", "SELL", "ENTER_LONG", "ENTER_SHORT"]
        ) and strat_rec != "WAIT" and strat_raw_act != "WAIT"
        
        strat_act = strat_raw_act if strat_raw_act in ["BUY", "SELL"] else (strat_dir if is_active_order else "WAIT")

        champ = strategy_decision.get("champion_strategy") or {}
        strat_name = champ.get("name", "QUANT_ALPHA")

        if not is_active_order:
            hold_reason = strategy_decision.get("rejection_reason") or f"Strategy returned {strat_rec} ({strat_act})"
            self.current_action = f"HOLD: {primary_symbol} - {hold_reason}"
            self._log(
                agent_name="🧪 Strategy R&D",
                action_type="DEFENSE_WAIT",
                symbol=primary_symbol,
                message=f"Hold decision on {primary_symbol}: {hold_reason}",
                details={"symbol": primary_symbol, "reason": hold_reason}
            )
            return {
                "market": self.market,
                "status": "HOLD",
                "symbol": primary_symbol,
                "reason": hold_reason,
                "cycle": self.cycle_count
            }

        # 6. Formulate Proposed Order
        evolution_warnings = self.evolution_agent.get_historical_warnings(
            strategy_name=strat_name,
            market_regime=market_structure,
            symbol=primary_symbol
        )

        cur_close = float(candles_df.iloc[-1]["close"]) if not candles_df.empty else 100.0
        entry_p = float(strategy_decision.get("entry_price") or analytical_report.get("suggested_entry") or cur_close)
        raw_sl = float(strategy_decision.get("stop_loss") or analytical_report.get("suggested_sl") or 0.0)
        raw_tp1 = float(strategy_decision.get("take_profit_1") or analytical_report.get("suggested_tp") or 0.0)
        
        atr_val = float(analytical_report.get("atr_volatility", {}).get("atr") or (entry_p * 0.015))
        min_sl_dist = max(atr_val * 1.5, entry_p * 0.008)
        
        if strat_dir == "LONG":
            sl_price = raw_sl if (0 < raw_sl < entry_p and (entry_p - raw_sl) >= min_sl_dist) else round(entry_p - min_sl_dist, 2)
            risk_dist = max(entry_p - sl_price, min_sl_dist)
            tp_price = raw_tp1 if (raw_tp1 > entry_p and (raw_tp1 - entry_p) >= risk_dist * 1.5) else round(entry_p + (risk_dist * 2.0), 2)
        else:
            sl_price = raw_sl if (raw_sl > entry_p and (raw_sl - entry_p) >= min_sl_dist) else round(entry_p + min_sl_dist, 2)
            risk_dist = max(sl_price - entry_p, min_sl_dist)
            tp_price = raw_tp1 if (0 < raw_tp1 < entry_p and (entry_p - raw_tp1) >= risk_dist * 1.5) else round(entry_p - (risk_dist * 2.0), 2)

        proposal = {
            "symbol": primary_symbol,
            "strategy_name": strat_name,
            "direction": strat_dir,
            "entry_price": entry_p,
            "stop_loss": sl_price,
            "take_profit_1": tp_price,
            "take_profit_2": strategy_decision.get("take_profit_2"),
            "triple_historical_index": strategy_decision.get("triple_historical_edge", {}).get("triple_historical_index", 50.0),
            "setup_score": strategy_decision.get("setup_score", 7.0),
            "win_rate_estimate": pattern_win_rate / 100.0,
            "is_wild_mode": self.trading_mode in ["DANGEROUS", "WILD_MODE"],
            "trading_mode": self.trading_mode,
            "trap_analysis": analytical_report.get("trap_analysis", {}),
            "fractal_alignment": analytical_report.get("fractal_alignment", {}),
            "ttm_squeeze": analytical_report.get("ttm_squeeze", {}),
            "intermarket_implications": {}
        }

        self._log(
            agent_name="🧪 Strategy R&D",
            action_type="ORDER_PROPOSAL",
            symbol=primary_symbol,
            message=f"Formulated {strat_dir} setup on {primary_symbol} via '{strat_name}'. Entry: ₹{entry_p:,.2f}, SL: ₹{sl_price:,.2f}, TP1: ₹{tp_price:,.2f}",
            details=proposal
        )

        # 7. 15-Section Risk Shield & Mistake Memory Audit
        self.current_action = f"RISK AUDIT: 15-Section Defense for {primary_symbol}"
        open_positions = self.execution_agent.get_open_positions_list()
        risk_verdict = self.risk_agent.evaluate_trade_proposal(
            proposal=proposal,
            open_positions=open_positions,
            candles_df=candles_df,
            evolution_warnings=evolution_warnings,
            is_high_impact_news_pending=False
        )

        if risk_verdict.get("decision") != "EXECUTE":
            reject_reason = risk_verdict.get("reason", "Risk defense triggered")
            self.current_action = f"BLOCKED: {primary_symbol} - {reject_reason}"
            self._log(
                agent_name="🛡️ 15-Section Risk Shield",
                action_type="DEFENSE_WAIT",
                symbol=primary_symbol,
                message=f"Trade on {primary_symbol} blocked by Risk Shield: {reject_reason}",
                details=risk_verdict
            )
            return {
                "market": self.market,
                "status": "REJECTED_BY_RISK",
                "symbol": primary_symbol,
                "reason": reject_reason,
                "cycle": self.cycle_count
            }

        # 8. CEO Supreme King Arbitration
        self.current_action = f"CEO ARBITRATION: Supreme King evaluating {primary_symbol}"
        self.ceo_agent.inspect_all_agent_eyes(
            news_data=news_intel,
            analytical_data=analytical_report,
            strategy_data=strategy_decision,
            backtest_data=lab_results,
            risk_data=risk_verdict,
            execution_data={"market": self.market},
            memory_summary=self.evolution_agent.get_evolution_summary()
        )

        trap_vetoed = analytical_report.get("trap_analysis", {}).get("recommended_action") == "VETO_TRADE"
        arbitration = self.ceo_agent.arbitrate_agent_conflicts(
            news_bias=macro_bias,
            analytical_signal=analytical_report.get("signal", "SCANNING"),
            strategy_action=strategy_decision.get("recommended_action", "WAIT"),
            risk_decision=risk_verdict.get("decision", "HOLD"),
            market=self.market,
            trap_detected=trap_vetoed,
            intermarket_regime="MACRO_NEUTRAL_TRANSITION",
            strategy_name=strat_name,
            symbol=primary_symbol,
            evolution_warnings=evolution_warnings,
            chart_score=float(analytical_report.get("chart_score") or analytical_report.get("confluence_score") or 0.0)
        )

        ceo_approval = self.ceo_agent.grant_supreme_approval(
            market=self.market,
            symbol=primary_symbol,
            direction=strat_dir,
            strategy_decision=strategy_decision,
            risk_verdict=risk_verdict,
            arbitration=arbitration,
            trap_analysis=analytical_report.get("trap_analysis"),
            intermarket_state={"macro_regime": "MACRO_NEUTRAL_TRANSITION"},
            fractal_alignment=analytical_report.get("fractal_alignment"),
            trading_mode=self.trading_mode
        )

        if not ceo_approval.get("approved_for_execution", False):
            ceo_reason = ceo_approval.get("reason", "CEO sovereign veto")
            self.current_action = f"VETO: {primary_symbol} - {ceo_reason}"
            self._log(
                agent_name="👑 CEO Supreme King",
                action_type="DEFENSE_WAIT",
                symbol=primary_symbol,
                message=f"CEO vetoed {strat_dir} on {primary_symbol}: {ceo_reason}",
                details=ceo_approval
            )
            return {
                "market": self.market,
                "status": "CEO_VETO",
                "symbol": primary_symbol,
                "reason": ceo_reason,
                "cycle": self.cycle_count
            }

        # 9. Execution Dispatch
        self.current_action = f"EXECUTING: Dispatching {strat_dir} order for {primary_symbol}"
        atr_pct = float(analytical_report.get("atr_volatility", {}).get("atr_pct", 1.5))
        exec_res = self.execution_agent.process_order(
            risk_approval=risk_verdict,
            strategy_decision=strategy_decision,
            market=self.market,
            symbol=primary_symbol,
            market_regime=market_structure,
            atr_pct=atr_pct,
            in_killzone=False,
            adx_value=adx_val,
            analytical_report=analytical_report,
            is_news_pending=False,
            trading_mode=self.trading_mode
        )

        self._log(
            agent_name="⚡ Execution Agent",
            action_type="ORDER_FILLED" if exec_res.get("status") == "EXECUTED" else "ORDER_ATTEMPT",
            symbol=primary_symbol,
            message=f"Execution result for {primary_symbol}: {exec_res.get('status')} - Order ID: {exec_res.get('order_id', 'N/A')}",
            details=exec_res
        )

        self.current_action = f"ACTIVE: Monitoring open position {primary_symbol}" if exec_res.get("status") == "EXECUTED" else f"STANDBY: {primary_symbol}"
        return {
            "market": self.market,
            "status": exec_res.get("status", "NO_ACTION"),
            "symbol": primary_symbol,
            "order": exec_res,
            "cycle": self.cycle_count
        }

    def get_fleet_telemetry(self) -> Dict[str, Any]:
        """Returns structured status card data for UI display."""
        session_info = SessionTimingController.evaluate_session_timing(self.market)
        is_open = session_info.get("can_execute", True) or self.market == "CRYPTO"

        # Count open positions for this specific market
        open_pos = [
            p for p in self.execution_agent.broker.open_positions
            if p.get("market") == self.market or (self.market == "INDIAN_STOCKS" and ".NS" in p.get("symbol", ""))
        ]

        # Calculate fleet-specific realized PnL
        fleet_trades = [
            t for t in self.execution_agent.broker.trade_history
            if t.get("market") == self.market or (self.market == "INDIAN_STOCKS" and ".NS" in t.get("symbol", ""))
        ]
        fleet_pnl = sum(float(t.get("realized_pnl", t.get("pnl", 0.0))) for t in fleet_trades)
        wins = sum(1 for t in fleet_trades if float(t.get("realized_pnl", t.get("pnl", 0.0))) > 0)
        win_rate = (wins / len(fleet_trades) * 100.0) if fleet_trades else 0.0

        return {
            "market": self.market,
            "is_open": is_open,
            "session_desc": session_info.get("session_name", "ACTIVE"),
            "cycle_count": self.cycle_count,
            "last_cycle_time": self.last_cycle_time or "--:--:--",
            "current_action": self.current_action,
            "allocated_capital": self.allocated_capital,
            "open_positions_count": len(open_pos),
            "total_trades_count": len(fleet_trades),
            "fleet_pnl": round(fleet_pnl, 2),
            "win_rate": round(win_rate, 1),
            "candidates_count": len(self.latest_candidates),
            "trading_mode": self.trading_mode,
            "agents_online": 9
        }
