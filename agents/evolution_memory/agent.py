"""
Self-Evolution & Long-Term Memory Agent
Role: Tracks trade post-mortems, records lessons from both winners and losers,
learns empirical trade duration distributions (No hardcoded limits; flexible from 1 bar to open-ended),
issues pre-trade warnings, and powers continuous system leveling.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
import numpy as np

from agents.evolution_memory.market_memory_matrix import MarketMemoryMatrix

from shared_brain.omni_calculator import OmniCalculator

logger = logging.getLogger("EvolutionMemory")

LEDGER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "trade_memory_ledger.json"))


class EvolutionMemoryAgent:
    """
    Self-Evolution & Institutional Memory Ledger.
    Ensures the system never repeats the same mistake twice and dynamically learns
    optimal holding behavior from real market outcomes over time.
    """

    def __init__(self, ledger_file: str = LEDGER_PATH):
        self.ledger_file = ledger_file
        self.calc = OmniCalculator(owner="EvolutionMemoryAgent")
        self.state = self._load_ledger()

    def _load_ledger(self) -> Dict[str, Any]:
        """Loads persistent memory ledger from disk or creates clean template."""
        if os.path.exists(self.ledger_file):
            try:
                with open(self.ledger_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"[EvolutionMemory] Could not load ledger ({e}). Initializing fresh ledger.")

        default_ledger = {
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
        self._save_ledger(default_ledger)
        return default_ledger

    def _save_ledger(self, data: Optional[Dict[str, Any]] = None):
        """Persists ledger safely to disk."""
        if data is None:
            data = self.state
        try:
            with open(self.ledger_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"[EvolutionMemory] Failed to save ledger: {e}")

    def log_trade_post_mortem(self, closed_trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conducts deep post-mortem analysis on a closed trade.
        Identifies why it won or lost, learns holding duration patterns, and updates memory ledger.
        """
        raw_pnl = closed_trade.get("realized_pnl")
        if raw_pnl is None:
            raw_pnl = closed_trade.get("pnl", 0.0)
        if isinstance(raw_pnl, (int, float)):
            pnl = float(raw_pnl)
        elif isinstance(raw_pnl, str):
            try:
                pnl = float(raw_pnl)
            except ValueError:
                pnl = 0.0
        else:
            pnl = 0.0

        raw_r = closed_trade.get("r_multiple", 0.0)
        if isinstance(raw_r, (int, float)):
            r_mult = float(raw_r)
        elif isinstance(raw_r, str):
            try:
                r_mult = float(raw_r)
            except ValueError:
                r_mult = 0.0
        else:
            r_mult = 0.0
        strat = closed_trade.get("strategy_name", "UNKNOWN")
        strat_family = closed_trade.get("strategy_family", "TREND_RIDING")
        exit_type = closed_trade.get("exit_type", "CLOSE_POSITION")
        exit_reason = closed_trade.get("exit_reason", "NORMAL")
        bars_held = closed_trade.get("bars_held", 0)
        regime = closed_trade.get("market_regime") or closed_trade.get("volatility_state") or ("WILD_MODE" if closed_trade.get("is_wild_mode") else "NORMAL")

        is_win = pnl > 0
        xp_gain = 50 if is_win else 30

        # Post-mortem diagnostic
        lesson_type = "GENERAL_REVIEW"
        verdict = f"Trade completed on Bar #{bars_held} with result {r_mult:.2f}R."

        if is_win:
            lesson_type = "VICTORY_REINFORCEMENT"
            verdict = f"Profitable run (+{r_mult}R). Strategy '{strat}' captured edge in {bars_held} bars."
            if "PARTIAL" in exit_reason or "TRAILING" in exit_reason:
                verdict += " Dynamic trailing stop successfully protected profits."
        else:
            if exit_type == "EMERGENCY_EARLY_EXIT":
                lesson_type = "EARLY_INVALIDATION_DEFENSE"
                verdict = f"Split-second early invalidation cut on Bar #{bars_held} ({exit_reason}). Saved capital before full SL!"
                self.state["early_exits_saved_capital_count"] = self.state.get("early_exits_saved_capital_count", 0) + 1
            elif "ALPHA_DECAY" in exit_reason or "TIME" in exit_reason:
                lesson_type = "MOMENTUM_STALL_DEFENSE"
                verdict = f"Alpha decay exit closed stagnant trade on Bar #{bars_held}, rotating capital out of flat chop."
            else:
                lesson_type = "STOP_LOSS_BREAKDOWN"
                verdict = f"Full stop loss hit ({r_mult:.2f}R). Structure invalidation reached on Bar #{bars_held} ({exit_reason})."
        # If Sump Agent forensics present, enrich the verdict
        sump_info = closed_trade.get("sump_forensics", {})
        if sump_info and sump_info.get("forensic_verdict"):
            verdict += f" | Sump Lab: {sump_info.get('forensic_verdict')}"

        post_mortem_record = {
            "trade_id": closed_trade.get("trade_id"),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": closed_trade.get("symbol"),
            "strategy": strat,
            "strategy_family": strat_family,
            "pnl": pnl,
            "r_multiple": r_mult,
            "bars_held": bars_held,
            "exit_reason": exit_reason,
            "lesson_type": lesson_type,
            "verdict": verdict,
            "market_regime": str(regime).upper(),
            "is_wild_mode": bool(closed_trade.get("is_wild_mode", "WILD" in str(regime).upper())),
            "sump_forensics": sump_info
        }

        # Update stats
        self.state["total_trades_analyzed"] += 1
        if is_win:
            self.state["wins_analyzed"] += 1
        else:
            self.state["losses_analyzed"] += 1

        self.state["recent_trade_post_mortems"].append(post_mortem_record)
        if len(self.state["recent_trade_post_mortems"]) > 50:
            self.state["recent_trade_post_mortems"].pop(0)

        # Update Strategy Performance Matrix
        if "strategy_performance_matrix" not in self.state:
            self.state["strategy_performance_matrix"] = {}
        if strat not in self.state["strategy_performance_matrix"]:
            self.state["strategy_performance_matrix"][strat] = {"wins": 0, "losses": 0, "total_r": 0.0}
        matrix_entry = self.state["strategy_performance_matrix"][strat]
        if is_win:
            matrix_entry["wins"] += 1
        else:
            matrix_entry["losses"] += 1
        matrix_entry["total_r"] = round(matrix_entry["total_r"] + r_mult, 2)

        # Update Market-Specific Strategy Matrix (Cross-Market Memory)
        market_norm = MarketMemoryMatrix.normalize_market_key(closed_trade.get("market", "CRYPTO"))
        if "market_strategy_matrix" not in self.state:
            self.state["market_strategy_matrix"] = {}
        if market_norm not in self.state["market_strategy_matrix"]:
            self.state["market_strategy_matrix"][market_norm] = {}
        if strat not in self.state["market_strategy_matrix"][market_norm]:
            self.state["market_strategy_matrix"][market_norm][strat] = {
                "wins": 0, "losses": 0, "total_r": 0.0, "sample_size": 0, "win_rate": 50.0, "avg_r": 1.5
            }
        m_strat = self.state["market_strategy_matrix"][market_norm][strat]
        if is_win:
            m_strat["wins"] += 1
        else:
            m_strat["losses"] += 1
        m_strat["sample_size"] += 1
        m_strat["total_r"] = round(m_strat["total_r"] + r_mult, 2)
        m_strat["win_rate"] = round((m_strat["wins"] / m_strat["sample_size"]) * 100.0, 1)
        m_strat["avg_r"] = round(m_strat["total_r"] / m_strat["sample_size"], 2)

        # Update Market-Specific Pattern Matrix
        chart_patt = closed_trade.get("chart_pattern")
        if chart_patt:
            if "market_pattern_matrix" not in self.state:
                self.state["market_pattern_matrix"] = {}
            if market_norm not in self.state["market_pattern_matrix"]:
                self.state["market_pattern_matrix"][market_norm] = {}
            if chart_patt not in self.state["market_pattern_matrix"][market_norm]:
                self.state["market_pattern_matrix"][market_norm][chart_patt] = {
                    "wins": 0, "losses": 0, "sample_size": 0, "win_rate": 50.0
                }
            m_patt = self.state["market_pattern_matrix"][market_norm][chart_patt]
            if is_win:
                m_patt["wins"] += 1
            else:
                m_patt["losses"] += 1
            m_patt["sample_size"] += 1
            m_patt["win_rate"] = round((m_patt["wins"] / m_patt["sample_size"]) * 100.0, 1)

        # Update Regime-Specific Performance Matrix (Wild Mode / Trending / Ranging)
        regime = closed_trade.get("market_regime") or closed_trade.get("volatility_state") or ("WILD_MODE" if closed_trade.get("is_wild_mode") else "NORMAL")
        regime_norm = str(regime).upper()
        if "regime_performance_matrix" not in self.state:
            self.state["regime_performance_matrix"] = {}
        if regime_norm not in self.state["regime_performance_matrix"]:
            self.state["regime_performance_matrix"][regime_norm] = {
                "wins": 0, "losses": 0, "sample_size": 0, "win_rate": 50.0, "total_r": 0.0
            }
        r_entry = self.state["regime_performance_matrix"][regime_norm]
        if is_win:
            r_entry["wins"] += 1
        else:
            r_entry["losses"] += 1
        r_entry["sample_size"] += 1
        r_entry["total_r"] = round(r_entry["total_r"] + r_mult, 2)
        r_entry["win_rate"] = round((r_entry["wins"] / r_entry["sample_size"]) * 100.0, 1)

        # Learn Duration Distribution over Time (Emergent & Flexible)
        if "strategy_duration_learning" not in self.state:
            self.state["strategy_duration_learning"] = {}
        if strat not in self.state["strategy_duration_learning"]:
            self.state["strategy_duration_learning"][strat] = {
                "win_durations": [],
                "loss_durations": [],
                "learned_win_median": 0.0,
                "learned_decay_threshold": 35
            }
        dur_entry = self.state["strategy_duration_learning"][strat]
        if is_win:
            dur_entry["win_durations"].append(bars_held)
            if len(dur_entry["win_durations"]) > 50:
                dur_entry["win_durations"].pop(0)
            dur_entry["learned_win_median"] = round(float(np.median(dur_entry["win_durations"])), 1)
        else:
            dur_entry["loss_durations"].append(bars_held)
            if len(dur_entry["loss_durations"]) > 50:
                dur_entry["loss_durations"].pop(0)

        # Compute dynamic alpha decay threshold:
        # If winning trades typically resolve in ~18 bars, holding beyond 1.8x median without profit shows alpha decay!
        if len(dur_entry["win_durations"]) >= 3:
            dur_entry["learned_decay_threshold"] = max(12, int(dur_entry["learned_win_median"] * 1.8))

        # Gain XP and Level Up
        self.state["xp"] += xp_gain
        if self.state["xp"] >= self.state["xp_next_level"]:
            self.state["agent_level"] += 1
            self.state["xp_next_level"] = int(self.state["xp_next_level"] * 1.8)
            ranks = ["Novice Quant", "Apprentice Trader", "Senior Quant Analyst", "Institutional Desk Lead", "Godfather Quant"]
            idx = min(self.state["agent_level"] - 1, len(ranks) - 1)
            self.state["rank"] = ranks[idx]
            logger.info(f"[EvolutionMemory] 🌟 LEVEL UP! Agent is now Level {self.state['agent_level']} ({self.state['rank']})!")

        self._save_ledger()
        logger.info(f"[EvolutionMemory] Post-Mortem logged: {verdict}")
        return post_mortem_record

    def get_learned_trade_duration_guidance(
        self,
        strategy_name: str,
        market_regime: str = "TRENDING"
    ) -> Dict[str, Any]:
        """
        Provides empirical holding duration guidance learned over time.
        Completely flexible: allows 1-bar exits and open-ended trend continuation.
        """
        dur_learning = self.state.get("strategy_duration_learning", {}).get(strategy_name, {})
        learned_decay = dur_learning.get("learned_decay_threshold", 35)
        learned_win_median = dur_learning.get("learned_win_median", 0.0)

        # If market regime is CHOP, compress alpha decay threshold so capital isn't trapped
        if "CHOP" in market_regime.upper() or "RANGING" in market_regime.upper():
            effective_decay = max(8, int(learned_decay * 0.7))
        elif "TREND" in market_regime.upper():
            effective_decay = int(learned_decay * 1.5)  # Let trends run
        else:
            effective_decay = learned_decay

        return {
            "strategy_name": strategy_name,
            "learned_win_median_bars": learned_win_median,
            "alpha_decay_bars": effective_decay,
            "can_exit_in_1_bar": True,
            "structure_riding_mode": "OPEN_ENDED_TRAILING",
            "guidance_note": "No fixed candle cutoff. Trade rides open-ended on structure, or exits on Bar 1 on flash invalidation."
        }

    def get_historical_warnings(
        self,
        strategy_name: str,
        market_regime: str = "TRENDING",
        symbol: str = "BTC"
    ) -> List[Dict[str, Any]]:
        """
        Scans long-term memory for vulnerabilities before opening a new trade.
        Warns if this strategy has recent failures, consecutive losses, or active negative constraints.
        """
        warnings = []
        matrix = self.state.get("strategy_performance_matrix", {}).get(strategy_name)

        if matrix:
            losses = matrix.get("losses", 0)
            wins = matrix.get("wins", 0)
            if losses > 0 and wins == 0:
                warnings.append({
                    "type": "CHRONIC_UNDERPERFORMANCE",
                    "severity": "HIGH",
                    "message": f"Strategy '{strategy_name}' has 0 wins and {losses} loss(es) in live trading. Proceed with extreme caution."
                })

        # 1. Check recent trade post-mortems for immediate repeat mistake risk
        recent_trade_losses = [
            m for m in self.state.get("recent_trade_post_mortems", [])[-10:]
            if m.get("strategy") == strategy_name and (symbol.upper() in m.get("symbol", "").upper() or not symbol) and float(m.get("pnl", 0.0)) < 0
        ]
        if recent_trade_losses:
            last_loss = recent_trade_losses[-1]
            warnings.append({
                "type": "RECENT_LOSS_REPEAT_RISK",
                "severity": "HIGH",
                "message": f"Strategy '{strategy_name}' suffered a recent loss on {symbol} (Exit: {last_loss.get('exit_reason', 'SL')}, PnL: ${last_loss.get('pnl', 0.0):,.2f}). High risk of repeating past mistake."
            })

        # 2. Check Mem0 negative constraints
        try:
            from agents.evolution_memory.mem0_memory_engine import Mem0MemoryEngine
            mem0_constraints = Mem0MemoryEngine().get_all_negative_constraints()
            for c in mem0_constraints:
                c_desc = c if isinstance(c, str) else c.get("description", str(c))
                if strategy_name.upper() in c_desc.upper() and symbol.upper() in c_desc.upper():
                    warnings.append({
                        "type": "NEGATIVE_CONSTRAINT_VIOLATION",
                        "severity": "CRITICAL",
                        "message": f"Mem0 Negative Constraint active: {c_desc}"
                    })
        except Exception:
            pass

        # 3. Check recent failures in chop
        if "CHOP" in market_regime.upper() or "RANGING" in market_regime.upper():
            recent_losses = [
                m for m in self.state.get("recent_trade_post_mortems", [])[-10:]
                if m.get("pnl", 0.0) < 0 and m.get("strategy_family") == "BREAKOUT_EXPANSION"
            ]
            if len(recent_losses) >= 2:
                warnings.append({
                    "type": "CHOP_BREAKOUT_TRAP_WARNING",
                    "severity": "MEDIUM",
                    "message": "Past trades show breakout strategies frequently failed in chop regime. Alpha decay compressed."
                })

        return warnings

    def get_evolution_summary(self) -> Dict[str, Any]:
        """Provides high-level snapshot for the UI dashboard."""
        return {
            "agent_level": self.state.get("agent_level", 1),
            "rank": self.state.get("rank", "Novice Quant"),
            "xp": self.state.get("xp", 0),
            "xp_next_level": self.state.get("xp_next_level", 250),
            "total_trades_analyzed": self.state.get("total_trades_analyzed", 0),
            "wins_analyzed": self.state.get("wins_analyzed", 0),
            "losses_analyzed": self.state.get("losses_analyzed", 0),
            "early_exits_saved_capital_count": self.state.get("early_exits_saved_capital_count", 0),
            "duration_learning_models": len(self.state.get("strategy_duration_learning", {})),
            "recent_lessons": self.state.get("recent_trade_post_mortems", [])[-5:],
            "active_market_matrices": list(self.state.get("market_strategy_matrix", {}).keys())
        }

    def get_market_strategy_affinity(self, market: str, strategy_name: str) -> Dict[str, Any]:
        """Queries how well a strategy has performed in this specific share market."""
        return MarketMemoryMatrix.get_market_strategy_affinity(
            market=market,
            strategy_name=strategy_name,
            live_ledger_matrix=self.state.get("market_strategy_matrix")
        )

    def get_market_pattern_affinity(self, market: str, pattern_name: str) -> Dict[str, Any]:
        """Queries the empirical reliability of a chart pattern in this specific share market."""
        return MarketMemoryMatrix.get_market_pattern_affinity(
            market=market,
            pattern_name=pattern_name,
            live_ledger_patterns=self.state.get("market_pattern_matrix")
        )

    def get_top_strategies_for_market(self, market: str) -> List[Dict[str, Any]]:
        """Returns the champion strategies for a specific world share market."""
        return MarketMemoryMatrix.get_top_strategies_for_market(market)

    def get_regime_memory_stats(self, regime: str = "WILD_MODE") -> Dict[str, Any]:
        """Retrieves learned win rate and performance for a given market regime."""
        self.state = self._load_ledger()
        r_clean = str(regime).upper()
        rpm = self.state.get("regime_performance_matrix", {}).get(r_clean)
        if rpm and rpm.get("sample_size", 0) > 0:
            return rpm

        # Fallback search across recent trade post-mortems
        matching = [
            m for m in self.state.get("recent_trade_post_mortems", [])
            if r_clean in str(m.get("market_regime", "")).upper()
            or r_clean in str(m.get("volatility_state", "")).upper()
            or (r_clean == "WILD_MODE" and m.get("is_wild_mode"))
        ]
        if matching:
            wins = sum(1 for t in matching if float(t.get("pnl", 0.0)) > 0)
            sample = len(matching)
            return {
                "wins": wins,
                "losses": sample - wins,
                "win_rate": round((wins / sample) * 100.0, 1),
                "sample_size": sample,
            }

        return {"wins": 0, "losses": 0, "win_rate": 50.0, "sample_size": 0, "total_r": 0.0}

    def get_supported_markets(self) -> List[str]:
        """Returns list of all supported global share and asset markets."""
        return list(MarketMemoryMatrix.BASE_MARKET_PROFILES.keys())



if __name__ == "__main__":
    evo = EvolutionMemoryAgent()
    print("Testing Evolution Memory Agent...")
    status = evo.get_evolution_summary()
    print(f"Agent Level: {status['agent_level']} ({status['rank']}) | XP: {status['xp']}/{status['xp_next_level']}")
    print(f"Supported Global Share Markets: {len(evo.get_supported_markets())}")



