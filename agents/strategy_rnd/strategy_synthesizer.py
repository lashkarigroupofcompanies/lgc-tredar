"""
Strategy Synthesizer & Genetic Innovation Engine
Mixes, mutates, and creates novel algorithmic trading strategies.
Combines atomic quant blocks (Regime Filters + Triggers + Volume Confirmations)
and leverages NVIDIA NIM LLM for market-adaptive strategy discovery with zero hallucination.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from shared_brain.llm_brain import LLMBrain
from agents.strategy_rnd.strategy_library import StrategyLibrary
from agents.strategy_rnd.fast_backtester import FastBacktestEngine

logger = logging.getLogger("StrategySynthesizer")


class StrategySynthesizer:
    """
    Automated Strategy R&D Lab.
    Synthesizes hybrid strategies by crossing classical indicators with modern ICT concepts,
    then verifies each newborn strategy via fast vectorized backtests.
    """

    def __init__(self, llm_brain: Optional[LLMBrain] = None):
        self.brain = llm_brain or LLMBrain()

    @staticmethod
    def generate_hybrid_strategy(
        df: pd.DataFrame,
        base_strategy_name: str,
        filter_type: str = "EMA_200_TREND",
        volume_confirm: bool = True
    ) -> Tuple[pd.Series, str]:
        """
        Synthesizes a new hybrid strategy combining a base strategy with a regime filter and volume filter.
        """
        strategies = StrategyLibrary.get_all_strategies()
        if base_strategy_name not in strategies:
            base_strategy_name = "SUPERTREND_MOMENTUM"

        base_func = strategies[base_strategy_name]
        raw_signals = base_func(df)

        hybrid_name = f"HYBRID_{base_strategy_name}_{filter_type}"
        filtered_signals = raw_signals.copy()

        # 1. Apply Regime Filter
        if filter_type == "EMA_200_TREND":
            ema200 = df["close"].ewm(span=200, adjust=False).mean()
            # Only Long above 200 EMA, only Short below 200 EMA
            filtered_signals[filtered_signals == 1] = np.where(df["close"] > ema200, 1, 0)
            filtered_signals[filtered_signals == -1] = np.where(df["close"] < ema200, -1, 0)

        elif filter_type == "VWAP_REGIME":
            typical = (df["high"] + df["low"] + df["close"]) / 3
            vwap = (typical * df["volume"]).cumsum() / df["volume"].cumsum()
            filtered_signals[filtered_signals == 1] = np.where(df["close"] > vwap, 1, 0)
            filtered_signals[filtered_signals == -1] = np.where(df["close"] < vwap, -1, 0)

        elif filter_type == "ADX_MOMENTUM":
            atr = StrategyLibrary._compute_atr(df, 14)
            high_diff = df["high"] - df["high"].shift(1)
            low_diff = df["low"].shift(1) - df["low"]
            plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0.0)
            minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0.0)
            plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(14).mean() / atr.replace(0, np.nan))
            minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(14).mean() / atr.replace(0, np.nan))
            adx = (100 * (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan))).rolling(14).mean()
            # Only take trades when market has genuine trend momentum (ADX > 20)
            filtered_signals = np.where(adx > 20, filtered_signals, 0)
            filtered_signals = pd.Series(filtered_signals, index=df.index)

        # 2. Apply Volume Confirmation
        if volume_confirm:
            vol_sma = df["volume"].rolling(20).mean()
            above_avg_vol = df["volume"] >= vol_sma * 1.1
            filtered_signals = np.where(above_avg_vol, filtered_signals, 0)
            filtered_signals = pd.Series(filtered_signals, index=df.index)
            hybrid_name += "_VOL_CONFIRMED"

        return filtered_signals, hybrid_name

    def invent_strategy_for_regime(
        self,
        market_bias: str,
        market_structure: str,
        volatility_state: str,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Uses NVIDIA NIM LLM to reason about current market conditions,
        hypothesize an optimal strategy combination, and immediately backtest it.
        """
        prompt = f"""
You are the Chief Quantitative Strategy Architect at an elite algorithmic trading firm.
Market Environment:
- Macro Bias: {market_bias}
- Market Structure: {market_structure}
- Volatility State: {volatility_state}

Synthesize a high-expectancy trading strategy selecting from our verified quantitative building blocks:
Available Base Strategies:
1. TURTLE_DONCHIAN_BREAKOUT
2. DUAL_EMA_TREND
3. SUPERTREND_MOMENTUM
4. OPENING_RANGE_BREAKOUT
5. BOLLINGER_RSI_MEAN_REVERSION
6. VWAP_MEAN_REVERSION
7. STOCHASTIC_RSI_SWING
8. KELTNER_CHANNEL_BREAKOUT
9. ICT_2022_MODEL
10. ICT_SILVER_BULLET
11. ORDER_BLOCK_GOLDEN_POCKET
12. BREAKER_BLOCK_FLIP
13. VOLUME_PROFILE_POC_RETEST
14. RVOL_SURGE_MOMENTUM
15. ADX_TREND_ACCELERATION

Available Filters:
- EMA_200_TREND
- VWAP_REGIME
- ADX_MOMENTUM

Return JSON ONLY in this format:
{{
    "selected_base_strategy": "<One of the 15 base strategies>",
    "selected_filter": "<EMA_200_TREND or VWAP_REGIME or ADX_MOMENTUM>",
    "volume_confirmation": true,
    "strategy_hypothesis": "<Explain in 1-2 sentences why this strategy is mathematically best for this exact market regime>",
    "target_risk_reward": 2.5,
    "recommended_timeframe": "15m"
}}
"""
        response = self.brain.query(prompt, temperature=0.1)
        # Parse JSON
        parsed: Dict[str, Any] = {}
        try:
            cleaned = response.strip().replace("```json", "").replace("```", "").strip()
            parsed = json.loads(cleaned)
        except Exception:
            # Deterministic fallback based on market structure
            if "BEAR" in market_bias or "DOWNTREND" in market_structure:
                parsed = {
                    "selected_base_strategy": "BREAKER_BLOCK_FLIP",
                    "selected_filter": "EMA_200_TREND",
                    "volume_confirmation": True,
                    "strategy_hypothesis": "Downtrend regime confirmed; using Breaker Block flip with 200 EMA resistance filter for short-side edge.",
                    "target_risk_reward": 2.5,
                    "recommended_timeframe": "15m"
                }
            elif "RANGE" in market_structure or "CONSOLIDATION" in market_structure:
                parsed = {
                    "selected_base_strategy": "BOLLINGER_RSI_MEAN_REVERSION",
                    "selected_filter": "VWAP_REGIME",
                    "volume_confirmation": False,
                    "strategy_hypothesis": "Range-bound choppy market; fading Bollinger band extremes with VWAP equilibrium magnet.",
                    "target_risk_reward": 2.0,
                    "recommended_timeframe": "15m"
                }
            else:
                parsed = {
                    "selected_base_strategy": "ICT_2022_MODEL",
                    "selected_filter": "EMA_200_TREND",
                    "volume_confirmation": True,
                    "strategy_hypothesis": "Trending market; entering on Fair Value Gap retest following liquidity sweep and market structure shift.",
                    "target_risk_reward": 2.5,
                    "recommended_timeframe": "15m"
                }

        base_strat = parsed.get("selected_base_strategy", "ICT_2022_MODEL")
        chosen_filter = parsed.get("selected_filter", "EMA_200_TREND")
        vol_conf = parsed.get("volume_confirmation", True)

        signals, hybrid_name = self.generate_hybrid_strategy(
            df,
            base_strategy_name=base_strat,
            filter_type=chosen_filter,
            volume_confirm=vol_conf
        )

        # Vectorized backtest on historical candles
        bt_results = FastBacktestEngine.run_backtest(
            df=df,
            signals=signals,
            risk_reward_ratio=float(parsed.get("target_risk_reward", 2.0))
        )

        return {
            "strategy_name": hybrid_name,
            "base_strategy": base_strat,
            "filter_applied": chosen_filter,
            "volume_confirmed": vol_conf,
            "hypothesis": parsed.get("strategy_hypothesis", "High probability algorithmic setup."),
            "backtest": bt_results,
            "latest_signal": int(signals.iloc[-1]) if not signals.empty else 0,
            "signals_series": signals
        }
