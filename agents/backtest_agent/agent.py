"""
Strategy Backtest Engine Agent (Institutional Stress-Testing Laboratory)
Role: Runs ultra-fast vectorized historical backtests, calculates Sortino/Expectancy/Monte Carlo metrics,
and stress-screens all candidate strategies (Old, New, Mixed) to return ONLY proven models to Strategy R&D.
Publishes continuous audit metrics to SharedAgentBoard for full cross-agent visibility.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from agents.strategy_rnd.fast_backtester import FastBacktestEngine
from agents.strategy_rnd.strategy_library import StrategyLibrary
from agents.analytical_agent.market_feed import MarketFeedEngine
from agents.backtest_agent.strategy_stress_lab import StrategyStressLab
from agents.evolution_memory.market_memory_matrix import MarketMemoryMatrix
from agents.evolution_memory.mem0_memory_engine import Mem0MemoryEngine
from shared_brain.shared_board import SharedAgentBoard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BacktestAgent")


class StrategyBacktestAgent:
    """
    Dedicated quant backtesting laboratory with bidirectional Evolution Memory feedback.
    Conducts deep multi-window stress testing, incorporates market empirical priors
    and Mem0 failure constraints, and publishes verified champions to the blackboard.
    """

    def __init__(self, shared_board: Optional[SharedAgentBoard] = None):
        self.feed = MarketFeedEngine()
        self.board = shared_board or SharedAgentBoard()
        self.stress_lab = StrategyStressLab()
        self.matrix = MarketMemoryMatrix
        self.mem0 = Mem0MemoryEngine()

    def run_continuous_backtest_lab(
        self,
        df: pd.DataFrame,
        market: str = "CRYPTO",
        candidate_strategies: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Exhaustively screens all candidate strategies on historical bars.
        Incorporates bidirectional Evolution Memory empirical priors and Mem0 negative constraints.
        Publishes the audited champions to the SharedAgentBoard.
        """
        norm_market = self.matrix.normalize_market_key(market)
        logger.info(f"[BacktestAgent] Running continuous backtesting laboratory across {len(df)} bars for {norm_market}...")

        # Pull market-specific empirical priors
        all_strats = candidate_strategies or StrategyLibrary.get_all_strategies()
        memory_priors: Dict[str, Any] = {}
        for s_name in all_strats.keys():
            affinity = self.matrix.get_market_strategy_affinity(norm_market, s_name)
            memory_priors[s_name] = affinity

        # Pull Mem0 negative constraints
        constraints = self.mem0.get_all_negative_constraints()

        lab_results = self.stress_lab.run_exhaustive_screen(
            df=df,
            candidate_strategies=candidate_strategies,
            market_name=norm_market,
            memory_matrix_priors=memory_priors,
            mem0_negative_constraints=constraints
        )
        lab_results["market"] = norm_market
        lab_results["memory_constraints_considered"] = len(constraints)

        # Publish to SharedAgentBoard
        self.board.post_backtest_lab_results(lab_results)
        return lab_results

    def deep_backtest_strategy(
        self,
        strategy_name: str,
        market_type: str = "CRYPTO",
        symbol: str = "BTC",
        timeframe: str = "15m",
        candle_count: int = 500
    ) -> Dict[str, Any]:
        """
        Runs deep historical backtest for a specific strategy on real historical candles.
        """
        logger.info(f"[BacktestAgent] Running deep backtest for {strategy_name} on {symbol} ({candle_count} candles)...")
        if market_type.upper() == "CRYPTO":
            df = self.feed.fetch_crypto_candles(symbol, interval=timeframe, limit=candle_count)
        else:
            df = self.feed.get_market_data(market_type, symbol, interval=timeframe)

        if df.empty or len(df) < 30:
            logger.warning("[BacktestAgent] Insufficient data for backtest.")
            return {"status": "INSUFFICIENT_DATA", "metrics": {}}

        strategies = StrategyLibrary.get_all_strategies()
        if strategy_name not in strategies:
            logger.warning(f"Strategy {strategy_name} not found in library.")
            return {"status": "STRATEGY_NOT_FOUND", "metrics": {}}

        signals = strategies[strategy_name](df)
        results = FastBacktestEngine.run_backtest(df, signals)

        affinity = self.matrix.get_market_strategy_affinity(market_type, strategy_name)

        return {
            "status": "SUCCESS",
            "strategy": strategy_name,
            "market_type": market_type,
            "symbol": symbol,
            "timeframe": timeframe,
            "candles_analyzed": len(df),
            "start_time": str(df.index[0]),
            "end_time": str(df.index[-1]),
            "metrics": results,
            "evolution_memory_affinity": affinity,
            "is_market_champion": affinity.get("is_market_champion", False)
        }


if __name__ == "__main__":
    agent = StrategyBacktestAgent()
    feed = MarketFeedEngine()
    print("Testing Strategy Backtest Agent Lab on BTC 15m Candles...")
    df_btc = feed.fetch_crypto_candles("BTC", interval="15m", limit=150)
    lab = agent.run_continuous_backtest_lab(df_btc)
    champ = lab.get("champion_strategy") or {}
    print(f"\nAudit Complete: Screened {lab['total_screened']} Strategies | Qualified: {lab['total_qualified']}")
    print(f"Top Champion: {champ.get('name')} | Win Rate: {champ.get('win_rate')}% | Sortino: {champ.get('sortino_ratio')}")
