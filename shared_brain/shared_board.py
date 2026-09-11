"""
Shared Multi-Agent Blackboard Architecture
Central synchronized state bus enabling real-time bidirectional communication
among News Agent, Analytical Agent, Strategy R&D Agent, and Backtest Agent.
Allows all agents to observe each other's live findings and coordinate their next steps.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import logging
from typing import Dict, Any, Optional

from shared_brain.live_trade_working_memory import LiveTradeWorkingMemory
from agents.evolution_memory.mem0_memory_engine import Mem0MemoryEngine

logger = logging.getLogger("SharedAgentBoard")


class SharedAgentBoard:
    """
    Central blackboard for autonomous multi-agent quantitative firm.
    Thread-safe in-memory state repository connecting short-term working memory and long-term Mem0 memory.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SharedAgentBoard, cls).__new__(cls)
            cls._instance._init_board()
        return cls._instance

    def _init_board(self):
        self.last_updated = time.time()
        self.live_memory = LiveTradeWorkingMemory()
        self.mem0 = Mem0MemoryEngine()
        self.news_state: Dict[str, Any] = {
            "macro_bias": "NEUTRAL",
            "risk_stance": "NORMAL",
            "targets": [],
            "precedent_verdict": "AWAITING_SCAN",
            "historical_prob": 50.0,
            "headline_count": 0
        }
        self.analytical_state: Dict[str, Any] = {
            "symbol": "BTC",
            "market_structure": "UNKNOWN",
            "chart_pattern": "NONE",
            "candlestick_pattern": "NONE",
            "pattern_historical_win_rate": 50.0,
            "pattern_verdict": "AWAITING_SCAN",
            "vwap": 0.0,
            "adx": 0.0,
            "killzone": "OFF_SESSION"
        }
        self.backtest_state: Dict[str, Any] = {
            "total_screened": 0,
            "total_qualified": 0,
            "champion_strategy_name": "NONE",
            "champion_metrics": {},
            "passing_champions": []
        }
        self.strategy_state: Dict[str, Any] = {
            "action": "WAIT",
            "entry_price": 0.0,
            "stop_loss": 0.0,
            "take_profit_1": 0.0,
            "setup_score": 0.0,
            "triple_historical_index": 0.0,
            "rationale": "Initializing"
        }
        self.intermarket_state: Dict[str, Any] = {
            "macro_regime": "MACRO_NEUTRAL_TRANSITION",
            "dxy_level": 104.5,
            "dxy_change_pct": 0.0,
            "us10y_yield": 4.25,
            "vix_level": 16.5,
            "cross_market_warnings": [],
            "timestamp": time.time()
        }

    def post_news_intel(self, news_report: Dict[str, Any]):
        """Called by NewsIntelligenceAgent."""
        prec = news_report.get("historical_precedent") or {}
        self.news_state = {
            "macro_bias": news_report.get("macro_bias", "NEUTRAL"),
            "risk_stance": news_report.get("risk_stance", "NORMAL"),
            "targets": news_report.get("recommended_targets", []),
            "precedent_verdict": prec.get("precedent_verdict", "ROUTINE"),
            "historical_prob": prec.get("historical_win_prob", 50.0),
            "dominant_catalyst": prec.get("dominant_catalyst", "NONE"),
            "headline_count": news_report.get("total_stories_analyzed", 0),
            "timestamp": time.time()
        }
        self.last_updated = time.time()

    def get_news_intel(self) -> Dict[str, Any]:
        return self.news_state

    def post_analytical_intel(self, analytical_report: Dict[str, Any]):
        """Called by MarketAnalyticalAgent."""
        pat_edge = analytical_report.get("historical_pattern_edge") or {}
        self.analytical_state = {
            "symbol": analytical_report.get("symbol", "BTC"),
            "market_structure": analytical_report.get("market_structure", "UNKNOWN"),
            "chart_pattern": analytical_report.get("chart_pattern", "NONE"),
            "candlestick_pattern": analytical_report.get("candlestick_pattern", "NONE"),
            "pattern_historical_win_rate": pat_edge.get("win_rate_pct", 50.0),
            "pattern_verdict": pat_edge.get("edge_verdict", "UNKNOWN"),
            "vwap": analytical_report.get("vwap", 0.0),
            "adx": analytical_report.get("adx_trend", {}).get("adx", 20.0) if isinstance(analytical_report.get("adx_trend"), dict) else 20.0,
            "killzone": analytical_report.get("session_killzone", "OFF_SESSION"),
            "timestamp": time.time()
        }
        self.last_updated = time.time()

    def get_analytical_intel(self) -> Dict[str, Any]:
        return self.analytical_state

    def post_backtest_lab_results(self, lab_results: Dict[str, Any]):
        """Called by StrategyBacktestAgent."""
        top_champ = lab_results.get("champion_strategy") or {}
        self.backtest_state = {
            "total_screened": lab_results.get("total_screened", 0),
            "total_qualified": lab_results.get("total_qualified", 0),
            "champion_strategy_name": top_champ.get("name", "NONE"),
            "champion_metrics": top_champ,
            "passing_champions": lab_results.get("passing_champions", []),
            "timestamp": time.time()
        }
        self.last_updated = time.time()

    def get_backtest_lab_results(self) -> Dict[str, Any]:
        return self.backtest_state

    def post_strategy_decision(self, decision: Dict[str, Any]):
        """Called by StrategyRndAgent."""
        self.strategy_state = {
            "action": decision.get("recommended_action", "WAIT"),
            "entry_price": decision.get("entry_price", 0.0),
            "stop_loss": decision.get("stop_loss", 0.0),
            "take_profit_1": decision.get("take_profit_1", 0.0),
            "take_profit_2": decision.get("take_profit_2", 0.0),
            "setup_score": decision.get("setup_score_10_pt", {}).get("total_score", 0.0),
            "triple_historical_index": decision.get("triple_historical_edge", {}).get("triple_historical_index", 0.0),
            "market_regime": decision.get("market_regime", "UNKNOWN"),
            "timestamp": time.time()
        }
        self.last_updated = time.time()

    def get_strategy_decision(self) -> Dict[str, Any]:
        return self.strategy_state

    def post_intermarket_telemetry(self, telemetry: Dict[str, Any]):
        """Posts real-time cross-asset macro telemetry (DXY, US10Y, VIX, BTC)."""
        self.intermarket_state = {
            "macro_regime": telemetry.get("macro_regime", "MACRO_NEUTRAL_TRANSITION"),
            "dxy_level": telemetry.get("dxy_level", 104.5),
            "dxy_change_pct": telemetry.get("dxy_change_pct", 0.0),
            "us10y_yield": telemetry.get("us10y_yield", 4.25),
            "us10y_change_pct": telemetry.get("us10y_change_pct", 0.0),
            "vix_level": telemetry.get("vix_level", 16.5),
            "vix_change_pct": telemetry.get("vix_change_pct", 0.0),
            "btc_price": telemetry.get("btc_price", 65000.0),
            "btc_change_pct": telemetry.get("btc_change_pct", 0.0),
            "cross_market_warnings": telemetry.get("cross_market_warnings", []),
            "timestamp": time.time()
        }
        self.last_updated = time.time()

    def get_intermarket_telemetry(self) -> Dict[str, Any]:
        return self.intermarket_state

    def get_full_board_snapshot(self) -> Dict[str, Any]:
        """Provides instant real-time snapshot of all agents' working states for the UI."""
        return {
            "last_updated": self.last_updated,
            "news": self.news_state,
            "analytical": self.analytical_state,
            "backtest": self.backtest_state,
            "strategy": self.strategy_state,
            "intermarket": self.intermarket_state,
            "live_trade_memory": self.live_memory.get_live_trade_snapshot(),
            "mem0_summary": {
                "total_memories": self.mem0.memory_store.get("total_memories", 0),
                "negative_constraints": self.mem0.get_all_negative_constraints()
            }
        }
