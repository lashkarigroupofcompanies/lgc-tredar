"""
Core Agent - Master Quantitative Orchestrator & Lifecycle Engine
Connects all 7 specialist agents into a synchronized, autonomous loop:
1. News Intelligence Agent (Macro bias, catalysts, 50+ historical event precedents)
2. Market Analytical Agent (15 sections, SMC/ICT, 500+ candle historical pattern lookback)
3. Strategy Backtest Agent (Quant performance lab, Monte Carlo Ruin check, Realistic costs)
4. Strategy R&D Agent (20+ strategies, genetic evolution mutator, Triple Historical Confluence)
5. Evolution Memory Agent (Post-mortem diagnostics, pre-trade warnings, XP leveling)
6. Risk Management Shield (1-2% sizing, setup quality tiering, -4% daily circuit breaker)
7. Execution Sniper / Paper Broker (Dynamic situation horizons, split-second early invalidations, TP1 partials)
"""

import sys
import os
import time
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from shared_brain.llm_brain import LLMBrain
from shared_brain.shared_board import SharedAgentBoard
from agents.news_agent.agent import NewsIntelligenceAgent
from agents.analytical_agent.agent import MarketAnalyticalAgent
from agents.strategy_rnd.agent import StrategyRndAgent
from agents.backtest_agent.agent import StrategyBacktestAgent
from agents.risk_agent.agent import RiskManagementAgent
from agents.execution_agent.agent import ExecutionAgent
from agents.evolution_memory.agent import EvolutionMemoryAgent
from agents.ceo_agent.agent import CEOAgent
from shared_brain.shadow_clone_manager import ShadowCloneManager
from shared_brain.intermarket_nexus import IntermarketNexus
from shared_brain.omni_calculator import OmniCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CoreAgent")


class CoreTradingAgent:
    """
    Central Nervous System of the Autonomous Trading Machine.
    Orchestrates the entire multi-agent loop, manages paper execution, and updates UI state.
    """

    def __init__(self):
        self.brain = LLMBrain()
        self.board = SharedAgentBoard()
        self.calc = OmniCalculator(owner="CoreTradingAgent")
        self.is_running = False
        self.selected_market = "CRYPTO"  # CRYPTO | INDIAN_STOCKS | US_STOCKS
        self.trading_mode = "CONSERVATIVE_SAFE"  # CONSERVATIVE_SAFE | WILD_MODE
        
        # Initialize Subsystem Agents connected to Shared Board
        logger.info("[CoreAgent] Bootstrapping Multi-Agent Quant Engine...")
        self.intermarket = IntermarketNexus()
        self.news_agent = NewsIntelligenceAgent()
        self.analytical_agent = MarketAnalyticalAgent()
        self.strategy_agent = StrategyRndAgent(self.brain)
        self.backtest_agent = StrategyBacktestAgent(self.board)
        self.evolution_agent = EvolutionMemoryAgent()
        self.risk_agent = RiskManagementAgent(account_balance=500000.0)
        self.execution_agent = ExecutionAgent(starting_balance=500000.0)
        self.ceo_agent = CEOAgent(self.brain)
        self.clone_manager = ShadowCloneManager()
        self.started_at: Optional[float] = None
        
        # System State
        self.system_state: Dict[str, Any] = {
            "status": "STOPPED",  # RUNNING | PAUSED | STOPPED
            "started_at": None,
            "uptime_seconds": 0,
            "last_session_uptime": 0,
            "active_market": self.selected_market,
            "trading_mode": self.trading_mode,
            "cycle_count": 0,
            "last_tick_time": None,
            "agent_statuses": {
                "ceo_agent": "ONLINE",
                "core_agent": "ONLINE",
                "news_agent": "ONLINE",
                "analytical_agent": "ONLINE",
                "strategy_rnd": "ONLINE",
                "backtest_agent": "ONLINE",
                "risk_agent": "ONLINE",
                "execution_agent": "ONLINE",
                "evolution_memory": "ONLINE",
                "sump_agent": "ONLINE",
                "shadow_clone_jutsu": "ONLINE"
            },
            "portfolio": {},
            "open_positions": [],
            "recent_trades": [],
            "latest_sump_forensics": [],
            "evolution_summary": {},
            "latest_intelligence": {},
            "latest_analytical_verdict": {},
            "latest_strategy_decision": {},
            "latest_risk_verdict": {},
            "latest_ceo_verdict": {},
            "ceo_dashboard": {},
            "shadow_clones": {}
        }
        self._refresh_state_snapshots()

    def _refresh_state_snapshots(self):
        """Refreshes portfolio, positions, and evolution memory in system state."""
        self.system_state["portfolio"] = self.execution_agent.get_portfolio_summary()
        self.system_state["open_positions"] = self.execution_agent.get_open_positions_list()
        self.system_state["recent_trades"] = self.execution_agent.broker.trade_history[-10:]
        self.system_state["latest_sump_forensics"] = self.execution_agent.get_latest_sump_forensics()[-5:]
        self.system_state["evolution_summary"] = self.evolution_agent.get_evolution_summary()
        self.system_state["live_trade_working_memory"] = self.board.live_memory.get_live_trade_snapshot()
        self.system_state["mem0_memory_summary"] = {
            "total_memories": self.board.mem0.memory_store.get("total_memories", 0),
            "negative_constraints": self.board.mem0.get_all_negative_constraints()
        }
        self.system_state["ceo_dashboard"] = self.ceo_agent.get_ceo_dashboard_snapshot()
        self.system_state["shadow_clones"] = self.clone_manager.get_manager_snapshot()
        self.risk_agent.update_account_balance(self.system_state["portfolio"]["equity"])

    def set_market(self, market: str):
        """Switch active trading market across all global share markets or select ALL."""
        valid_markets = [
            "CRYPTO", "INDIAN_STOCKS", "US_STOCKS",
            "UK_STOCKS", "EU_STOCKS", "ASIAN_STOCKS", "FOREX", "COMMODITIES",
            "ALL", "ALL_THREE", "MULTI_MARKET"
        ]
        if market.upper() in valid_markets:
            self.selected_market = market.upper()
            self.system_state["active_market"] = self.selected_market
            logger.info(f"[CoreAgent] Market switched to {self.selected_market}")

    def set_trading_mode(self, mode: str):
        """
        Switch operational trading mode across the 3 specialized regimes:
        - SAFE: Steady trends, high confluence, 15m/1h timeframes (~1 trade / 3-5 hrs). Target win rate ~70%.
        - MONEY_MAKER: Balanced intraday driver, 5m/15m timeframes, top 3-5 setups (3-6 trades / 5-6 hrs).
        - DANGEROUS: Rapid neural evolution learning lab, 1m/5m fast scalps, micro-sizing (10-20 trades / hr).
        """
        clean_mode = str(mode).upper()
        if "DANGEROUS" in clean_mode or "WILD" in clean_mode:
            self.trading_mode = "DANGEROUS"
            self.ceo_agent.active_mandate = "HIGH_VELOCITY_NEURAL_EVOLUTION"
            logger.info("[CoreAgent] ⚡ DANGEROUS MODE ENGAGED! High-frequency paper trading evolution active (10-20 trades/hr target, micro-sizing 0.35%).")
        elif "MONEY" in clean_mode or "MAKER" in clean_mode:
            self.trading_mode = "MONEY_MAKER"
            self.ceo_agent.active_mandate = "BALANCED_DAILY_MULTI_SETUP_ALPHA"
            logger.info("[CoreAgent] 💰 MONEY MAKER MODE ENGAGED! Multi-asset intraday scanning active. Top 3-5 setups executed with dynamic profit targets.")
        else:
            self.trading_mode = "SAFE"
            self.ceo_agent.active_mandate = "INSTITUTIONAL_CAPITAL_PRESERVATION"
            logger.info("[CoreAgent] 🛡️ SAFE MODE ENGAGED. Institutional sniper setup filter active (70% win-rate target, 1 trade / 3-5 hrs).")

        self.system_state["trading_mode"] = self.trading_mode
        self.risk_agent.set_mode(self.trading_mode)

    def start(self):
        """Starts the autonomous trading loop"""
        self.is_running = True
        self.started_at = time.time()
        self.system_state["status"] = "RUNNING"
        self.system_state["started_at"] = self.started_at
        self.system_state["uptime_seconds"] = 0
        logger.info(f"[CoreAgent] Autonomous trading engine STARTED on {self.selected_market} at {time.strftime('%Y-%m-%d %H:%M:%S')}!")

    def pause(self):
        """Pauses the trading loop"""
        self.is_running = False
        self.system_state["status"] = "PAUSED"
        logger.info("[CoreAgent] Autonomous trading engine PAUSED.")

    def stop(self):
        """Stops the trading loop"""
        self.is_running = False
        final_uptime = int(time.time() - self.started_at) if self.started_at else 0
        self.system_state["status"] = "STOPPED"
        self.system_state["last_session_uptime"] = final_uptime
        self.system_state["uptime_seconds"] = 0
        self.started_at = None
        self.system_state["started_at"] = None
        logger.info(f"[CoreAgent] Autonomous trading engine STOPPED after running for {final_uptime}s.")

    def configure_and_start(
        self,
        markets: Optional[List[str]] = None,
        trading_style: str = "ALL",
        mode: str = "PAPER",
        starting_capital: float = 500000.0,
        currency: str = "INR",
        allocation_mode: str = "DISTRIBUTED_TOTAL",
        market_capitals: Optional[Dict[str, float]] = None
    ):
        """Configures market filters, trading style, paper capital, and starts trading."""
        active_list = ["INDIAN_STOCKS", "CRYPTO", "US_STOCKS", "COMMODITIES"]
        if markets:
            if "ALL" in [m.upper() for m in markets]:
                self.selected_market = "ALL"
            else:
                self.selected_market = markets[0].upper()
                active_list = [m.upper() for m in markets]
            self.system_state["active_market"] = self.selected_market
            self.system_state["selected_markets"] = markets

        self.system_state["trading_style"] = trading_style
        self.system_state["execution_mode"] = mode
        self.system_state["currency"] = currency
        self.system_state["allocation_mode"] = allocation_mode

        # Institutional Multi-Market Allocation: Each market receives dedicated ₹1,00,000 capital
        standard_markets = ["INDIAN_STOCKS", "US_STOCKS", "CRYPTO", "COMMODITIES", "FOREX"]
        alloc_map = {}
        if market_capitals and len(market_capitals) > 0:
            alloc_map = {k.upper(): float(v) for k, v in market_capitals.items()}
        else:
            # Each market gets dedicated ₹1,00,000 to trade
            target_list = active_list if active_list and "ALL" not in active_list else standard_markets
            for m in standard_markets:
                alloc_map[m] = 100000.0
        
        total_cap = sum(alloc_map.values())
        self.system_state["market_allocations"] = alloc_map
        self.system_state["starting_market_allocations"] = dict(alloc_map)
        self.execution_agent.broker.market_starting_cap = dict(alloc_map)
        self.execution_agent.broker.starting_balance = total_cap
        
        # Recalculate cash balance based on actual starting capital and realized trades
        total_realized_pnl = sum(float(t.get("realized_pnl", t.get("pnl", 0.0))) for t in self.execution_agent.broker.trade_history)
        self.execution_agent.broker.balance = total_cap + total_realized_pnl

        self.start()
        logger.info(
            f"[CoreAgent] Configured & Started: Each market allocated ₹1,00,000. "
            f"Allocations={alloc_map}, Total Portfolio Capital=₹{total_cap:,.2f} {currency}"
        )

    def reset_state(self, starting_capital: float = 500000.0):
        """Halts engine and cleanly resets portfolio, trade history, and evolution ledger."""
        self.stop()
        self.execution_agent.broker.reset(starting_balance=500000.0, per_market_capital=100000.0)
        # Clear ledger
        clean_ledger = {
            "agent_level": 1,
            "rank": "Novice Quant",
            "xp": 0,
            "xp_next_level": 250,
            "total_trades_analyzed": 0,
            "wins_analyzed": 0,
            "losses_analyzed": 0,
            "early_exits_saved_capital_count": 0,
            "lessons_learned": [],
            "strategy_performance_matrix": {},
            "strategy_duration_learning": {},
            "market_strategy_matrix": {},
            "market_pattern_matrix": {},
            "regime_mistake_records": [],
            "recent_trade_post_mortems": []
        }
        self.evolution_agent.state = clean_ledger
        self.evolution_agent._save_ledger(clean_ledger)
        self._refresh_state_snapshots()
        logger.info(f"[CoreAgent] Trading engine, ledger and portfolio cleanly reset to fresh state with capital {starting_capital:,.2f}")

    def run_single_cycle(self, override_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Executes one full synchronized cycle across all 7 agents:
        1. News Intelligence scan (Macro bias, 50+ event precedents)
        2. Analytical Scan (15 sections, SMC/ICT, 500+ candle historical pattern lookback)
        3. Active Position Surveillance (Evaluate open trades for dynamic horizon, TP1, or Early Invalidation)
        4. Backtest Lab Screening (Screens 20 strategies against live candles)
        5. Strategy R&D Selection & Triple Historical Confluence Gate
        6. Evolution Memory Warning Check
        7. Risk Management Shield Check (1-2% sizing, Circuit Breaker)
        8. Execution Sniper (Opens new position if approved)
        """
        self.system_state["cycle_count"] += 1
        self.system_state["last_tick_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[CoreAgent] === STARTING CYCLE #{self.system_state['cycle_count']} on {self.selected_market} ===")

        # Step 1: News & Macro Intelligence Scan + Intermarket Cross-Asset Nexus
        macro_telemetry = self.intermarket.refresh_macro_telemetry()
        self.board.post_intermarket_telemetry(macro_telemetry)
        self.system_state["intermarket_telemetry"] = macro_telemetry

        news_report = self.news_agent.generate_llm_intelligence_report(self.selected_market)
        self.board.post_news_intel(news_report)
        self.system_state["latest_intelligence"] = news_report

        # Real-Time News UpGuard: Instantly intercept breaking news across pending orders & positions
        upguard_defense = self.execution_agent.intercept_breaking_macro_news(news_report)
        self.system_state["latest_upguard_verdict"] = upguard_defense

        # Step 2: Multi-Chart Screener tuned to active regime:
        # - DANGEROUS: 5m high-velocity setup screening, relaxed threshold (>=42 pts) for fast evolution.
        # - MONEY_MAKER: 5m multi-asset intraday scanning, balanced threshold (>=60 pts) for top 3-5 setups.
        # - SAFE: 15m steady trend confluence, institutional threshold (>=75 pts) for ~70% win-rate.
        if self.trading_mode == "DANGEROUS":
            scan_timeframe = "5m"
            chart_label = "⚡ Dangerous Evolution Setup"
        elif self.trading_mode == "MONEY_MAKER":
            scan_timeframe = "5m"
            chart_label = "💰 Money Maker Intraday Setup"
        else:
            scan_timeframe = "15m"
            chart_label = "🛡️ Institutional Safe Setup"

        screener_report = self.analytical_agent.screen_and_select_best_chart(
            market=self.selected_market,
            news_bias=news_report.get("macro_bias", "NEUTRAL"),
            timeframe=scan_timeframe,
            mode=self.trading_mode
        )
        self.system_state["screener_report"] = screener_report
        best_chart = screener_report.get("best_chart", {})
        active_market = best_chart.get("market", self.selected_market)
        primary_symbol = best_chart.get("symbol", "BTC")

        logger.info(
            f"[CoreAgent] 🎯 Best {chart_label} Chosen: {active_market}:{primary_symbol} "
            f"(Score: {best_chart.get('safety_score', 0.0)}/100 | {best_chart.get('status')} | "
            f"Structure: {best_chart.get('trend_clarity', 'NEUTRAL')})"
        )

        # Step 3: Analytical Deep Scan & Indicators on Chosen Chart (15 sections + SMC + 500 candles)
        analytical_report = self.analytical_agent.analyze_asset(
            active_market, primary_symbol, timeframe=scan_timeframe, df_override=override_df
        )
        self.board.post_analytical_intel(analytical_report)
        self.system_state["latest_analytical_verdict"] = analytical_report

        if override_df is not None:
            candles_df = override_df
        else:
            candles_df = self.analytical_agent.feed.get_market_data(active_market, primary_symbol, interval=scan_timeframe)
        current_price = float(candles_df.iloc[-1]["close"]) if not candles_df.empty else float(best_chart.get("current_price", 0.0))

        adx_val = 22.0
        try:
            adx_val = float(analytical_report.get("adx_trend", {}).get("adx", 22.0))
        except Exception:
            pass

        # Step 4: Active Trade Surveillance (Split-second early invalidations & emergent duration)
        active_strat = "DISCRETIONARY_SETUP"
        if self.system_state.get("open_positions"):
            active_strat = self.system_state["open_positions"][0].get("strategy_name", "DISCRETIONARY_SETUP")
        
        learned_guidance = self.evolution_agent.get_learned_trade_duration_guidance(
            strategy_name=active_strat,
            market_regime=analytical_report.get("market_structure", "TRENDING")
        )

        closed_trades = self.execution_agent.on_candle_tick(
            symbol=primary_symbol,
            current_price=current_price,
            recent_df=candles_df.tail(30) if not candles_df.empty else pd.DataFrame(),
            adx_value=adx_val,
            macro_news_alert=news_report,
            learned_guidance=learned_guidance
        )

        # Feed any closed trade directly into Evolution Memory & Risk Agent!
        for ct in closed_trades:
            self.evolution_agent.log_trade_post_mortem(ct)
            self.risk_agent.record_closed_trade(float(ct.get("realized_pnl", 0.0)))

        # Step 5: Backtest Lab Screening with Bidirectional Evolution Memory Feedback
        lab_results = self.backtest_agent.run_continuous_backtest_lab(candles_df, market=active_market)

        # Step 6: Strategy R&D Selection & Triple Historical Confluence Gate
        pattern_win_rate = float(analytical_report.get("historical_pattern_edge", {}).get("win_rate_pct", 50.0))
        news_prob = float(news_report.get("historical_precedent", {}).get("historical_win_prob", 50.0))
        market_structure = analytical_report.get("market_structure", "RANGING")

        strategy_decision = self.strategy_agent.evaluate_and_select_best_strategy(
            df=candles_df,
            market=active_market,
            macro_bias=news_report.get("macro_bias", "NEUTRAL"),
            market_structure=market_structure,
            volatility_state="NORMAL",
            adx_value=adx_val,
            chart_pattern_win_rate=pattern_win_rate,
            news_precedent_win_prob=news_prob
        )
        self.board.post_strategy_decision(strategy_decision)
        self.system_state["latest_strategy_decision"] = strategy_decision

        champ = strategy_decision.get("champion_strategy") or {}
        triple_edge = strategy_decision.get("triple_historical_edge") or {}
        strat_name = champ.get("name", "DISCRETIONARY_SETUP")

        # Step 7: Evolution Memory Pre-Trade Query
        evolution_warnings = self.evolution_agent.get_historical_warnings(
            strategy_name=strat_name,
            market_regime=market_structure,
            symbol=primary_symbol
        )

        # Step 8: 15-Section Risk Management Shield Audit (with Depth 2/3 Trap & Intermarket Gates)
        strat_dir = strategy_decision.get("direction") or ("SHORT" if strategy_decision.get("action") == "SELL" else "LONG")
        intermarket_implications = self.intermarket.get_cross_market_implications(
            market=active_market,
            direction=strat_dir
        )

        proposal = {
            "symbol": primary_symbol,
            "strategy_name": strat_name,
            "direction": strat_dir,
            "entry_price": strategy_decision.get("entry_price") or analytical_report.get("suggested_entry"),
            "stop_loss": strategy_decision.get("stop_loss") or analytical_report.get("suggested_sl"),
            "take_profit_1": strategy_decision.get("take_profit_1") or analytical_report.get("suggested_tp"),
            "take_profit_2": strategy_decision.get("take_profit_2"),
            "triple_historical_index": triple_edge.get("triple_historical_index", 50.0),
            "setup_score": strategy_decision.get("setup_score", 7.0),
            "win_rate_estimate": pattern_win_rate / 100.0,
            "is_wild_mode": self.trading_mode == "WILD_MODE",
            "trap_analysis": analytical_report.get("trap_analysis", {}),
            "fractal_alignment": analytical_report.get("fractal_alignment", {}),
            "ttm_squeeze": analytical_report.get("ttm_squeeze", {}),
            "intermarket_implications": intermarket_implications
        }

        open_positions = self.execution_agent.get_open_positions_list()
        risk_verdict = self.risk_agent.evaluate_trade_proposal(
            proposal=proposal,
            open_positions=open_positions,
            candles_df=candles_df,
            evolution_warnings=evolution_warnings,
            is_high_impact_news_pending=False
        )
        self.system_state["latest_risk_verdict"] = risk_verdict

        # Step 9: CEO Supreme King Council Review & Conflict Arbitration
        self.ceo_agent.inspect_all_agent_eyes(
            news_data=news_report,
            analytical_data=analytical_report,
            strategy_data=strategy_decision,
            backtest_data=lab_results,
            risk_data=risk_verdict,
            execution_data=self.system_state,
            memory_summary=self.system_state["evolution_summary"]
        )

        trap_vetoed = analytical_report.get("trap_analysis", {}).get("recommended_action") == "VETO_TRADE"
        arbitration = self.ceo_agent.arbitrate_agent_conflicts(
            news_bias=news_report.get("macro_bias", "NEUTRAL"),
            analytical_signal=analytical_report.get("signal", "SCANNING"),
            strategy_action=strategy_decision.get("recommended_action", "WAIT"),
            risk_decision=risk_verdict.get("decision", "HOLD"),
            market=active_market,
            trap_detected=trap_vetoed,
            intermarket_regime=macro_telemetry.get("macro_regime", "MACRO_NEUTRAL_TRANSITION"),
            strategy_name=strat_name,
            symbol=primary_symbol,
            evolution_warnings=evolution_warnings,
            chart_score=float(analytical_report.get("chart_score") or analytical_report.get("confluence_score") or 0.0)
        )

        ceo_approval = self.ceo_agent.grant_supreme_approval(
            market=active_market,
            symbol=primary_symbol,
            direction=strategy_decision.get("direction", "LONG"),
            strategy_decision=strategy_decision,
            risk_verdict=risk_verdict,
            arbitration=arbitration,
            trap_analysis=analytical_report.get("trap_analysis"),
            intermarket_state=macro_telemetry,
            fractal_alignment=analytical_report.get("fractal_alignment")
        )
        self.system_state["latest_ceo_verdict"] = ceo_approval

        # Step 10: Execution Sniper Order Entry (If approved by CEO & Risk)
        exec_result = {"status": "NO_ACTION"}
        if ceo_approval.get("approved_for_execution"):
            atr_pct = float(analytical_report.get("atr_volatility", {}).get("atr_pct", 1.5))
            exec_result = self.execution_agent.process_order(
                risk_approval=risk_verdict,
                strategy_decision=strategy_decision,
                market=active_market,
                symbol=primary_symbol,
                market_regime=market_structure,
                atr_pct=atr_pct,
                in_killzone=False,
                adx_value=adx_val,
                analytical_report=analytical_report,
                is_news_pending=False,
                trading_mode=self.trading_mode
            )

        # Step 11: Tick All Active Shadow Clones (Naruto Multi-Market Concurrency)
        market_tick_data = {
            f"{active_market}:{primary_symbol}": {
                "price": current_price,
                "high": float(candles_df["high"].iloc[-1]) if not candles_df.empty else current_price,
                "low": float(candles_df["low"].iloc[-1]) if not candles_df.empty else current_price,
                "rejection_wick": analytical_report.get("chart_pattern") in ["SHOOTING_STAR", "HAMMER_REVERSAL"],
                "micro_choch": False
            }
        }
        self.clone_manager.tick_all_active_clones(market_tick_data)

        self._refresh_state_snapshots()

        cycle_summary = {
            "cycle": self.system_state["cycle_count"],
            "timestamp": self.system_state["last_tick_time"],
            "market": self.selected_market,
            "target_asset": primary_symbol,
            "current_price": current_price,
            "macro_bias": news_report.get("macro_bias"),
            "market_structure": market_structure,
            "chart_pattern": analytical_report.get("chart_pattern"),
            "pattern_historical_win_rate": pattern_win_rate,
            "news_precedent_prob": news_prob,
            "triple_historical_index": triple_edge.get("triple_historical_index"),
            "champion_strategy": strat_name,
            "strategy_action": strategy_decision.get("recommended_action"),
            "risk_decision": risk_verdict.get("decision"),
            "risk_tier": risk_verdict.get("risk_tier"),
            "ceo_decision": ceo_approval.get("ceo_decision"),
            "ceo_mandate": ceo_approval.get("mandate"),
            "active_clones_count": len(self.clone_manager.active_clones),
            "execution_status": exec_result.get("status"),
            "portfolio": self.system_state["portfolio"],
            "portfolio_equity": float((self.system_state.get("portfolio") or {}).get("equity", 100000.0)),
            "open_positions_count": len(self.system_state["open_positions"]),
            "risk_reason": risk_verdict.get("reason"),
            "agent_level": self.system_state["evolution_summary"].get("agent_level"),
            "rank": self.system_state["evolution_summary"].get("rank")
        }

        portfolio_data = self.system_state.get("portfolio") or {}
        equity_val = float(portfolio_data.get("equity", 0.0))
        open_count = len(self.system_state.get("open_positions") or [])

        logger.info(
            f"[CoreAgent] Cycle #{cycle_summary['cycle']} Done. "
            f"Action: {cycle_summary['strategy_action']} | Risk: {cycle_summary['risk_decision']} | "
            f"Open Positions: {open_count} | Portfolio Equity: ${equity_val:,.2f}"
        )

        return cycle_summary

    def get_dashboard_state(self) -> Dict[str, Any]:
        """Provides full snapshot of all agents for the UI dashboard."""
        self._refresh_state_snapshots()
        if self.is_running and self.started_at:
            self.system_state["uptime_seconds"] = int(time.time() - self.started_at)
            self.system_state["started_at"] = self.started_at
        return self.system_state


if __name__ == "__main__":
    core = CoreTradingAgent()
    print("Testing Core Agent synchronized cycle with all 7 agents...")
    core.start()
    res = core.run_single_cycle()
    print("\n--- CYCLE SUMMARY ---")
    for k, v in res.items():
        print(f"  {k}: {v}")
