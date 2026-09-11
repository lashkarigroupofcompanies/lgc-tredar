"""
Naruto Shadow Clone Jutsu Multi-Market Engine
Allows multiple trades to execute concurrently across different world share markets
(or the same market) using isolated tactical clone squads.

Key Mechanics:
1. Clone Spawning (Kage Bunshin no Jutsu): Creates an isolated clone squad with its own Short-Term Working Memory.
2. Independent Tactical Execution: Each clone fights in its assigned market without cross-contaminating signals.
3. The Merge Jutsu (Clone Dispersal & Reabsorption):
   When a clone finishes its trade, all acquired experiences, forensic counterfactuals,
   and newly induced negative constraints are merged into the Central Mem0 Long-Term Brain!
4. Supreme Oversight: The CEO King Agent sees through every clone's eyes simultaneously and can kill/recall any clone at will.
"""

import sys
import os
import time
import logging
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared_brain.live_trade_working_memory import LiveTradeWorkingMemory
from shared_brain.omni_calculator import OmniCalculator
from agents.evolution_memory.mem0_memory_engine import Mem0MemoryEngine
from agents.evolution_memory.agent import EvolutionMemoryAgent

logger = logging.getLogger("ShadowCloneManager")


class ShadowCloneSquad:
    """
    An isolated tactical clone unit assigned to a specific market & asset.
    Possesses its own Short-Term Working Memory and its own personal OmniCalculator.
    """

    def __init__(
        self,
        clone_id: str,
        market: str,
        symbol: str,
        strategy_name: str,
        allocated_capital: float = 20000.0,
        mem0_engine: Optional[Mem0MemoryEngine] = None
    ):
        self.clone_id = clone_id
        self.market = market.upper()
        self.symbol = symbol.upper()
        self.strategy_name = strategy_name
        self.allocated_capital = allocated_capital
        self.mem0 = mem0_engine or Mem0MemoryEngine()
        self.created_at = time.strftime("%Y-%m-%d %H:%M:%S")

        # Personal Dedicated Quantitative Calculator for this Clone Squad
        self.calc = OmniCalculator(owner=f"CLONE_{self.clone_id}")

        # 100% Isolated Short-Term Working Memory for this clone
        self.live_memory = LiveTradeWorkingMemory(is_clone=True)

        # Tactical State
        self.status = "SPAWNED"  # SPAWNED | ACTIVE | HOLDING | MERGING | DISPERSED
        self.active_position: Optional[Dict[str, Any]] = None
        self.closed_trade_record: Optional[Dict[str, Any]] = None

        logger.info(f"[ShadowCloneSquad] 🥷 Spawned Clone Squad [{self.clone_id}] for {self.market}:{self.symbol} with ${self.allocated_capital:,.2f}")

    def activate_clone_trade(
        self,
        trade_id: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        target_price: float,
        units: float,
        dollar_risk: float
    ):
        """Activates trade inside this clone's isolated short-term memory."""
        self.status = "ACTIVE"
        self.active_position = {
            "trade_id": trade_id,
            "clone_id": self.clone_id,
            "market": self.market,
            "symbol": self.symbol,
            "direction": direction,
            "strategy_name": self.strategy_name,
            "entry_price": entry_price,
            "current_price": entry_price,
            "stop_loss": stop_loss,
            "target_price": target_price,
            "units": units,
            "dollar_risk": dollar_risk,
            "bars_held": 0,
            "unrealized_pnl": 0.0,
            "unrealized_r": 0.0,
            "sl_state": "ORIGINAL",
            "entry_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Initialize the clone's dedicated short-term memory
        self.live_memory.activate_trade({
            "trade_id": trade_id,
            "market": self.market,
            "symbol": self.symbol,
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "initial_units": units,
            "dollar_risk": dollar_risk
        })

        self.live_memory.post_inter_agent_message(
            from_agent=f"Clone-{self.clone_id}",
            to_agent="CEOAgent",
            message=f"🥷 Clone Squad deployed: [{direction} {self.symbol} in {self.market}] at ${entry_price:,.2f}.",
            priority="HIGH"
        )

    def tick_clone(
        self,
        current_price: float,
        high: float,
        low: float,
        rejection_wick: bool = False,
        micro_choch: bool = False
    ) -> Dict[str, Any]:
        """Ticks the clone's active position on new incoming candle."""
        if self.status != "ACTIVE" or not self.active_position:
            return {"status": self.status, "action": "NO_ACTIVE_POSITION"}

        pos = self.active_position
        pos["bars_held"] += 1
        pos["current_price"] = current_price

        # Calculate PnL & R-Multiple
        direction = pos["direction"]
        entry = pos["entry_price"]
        sl = pos["stop_loss"]
        units = pos["units"]
        risk_per_unit = abs(entry - sl) if abs(entry - sl) > 0 else (entry * 0.01)

        if direction == "LONG":
            pos["unrealized_pnl"] = (current_price - entry) * units
            pos["unrealized_r"] = (current_price - entry) / risk_per_unit
        else:
            pos["unrealized_pnl"] = (entry - current_price) * units
            pos["unrealized_r"] = (entry - current_price) / risk_per_unit

        # Trailing Stop Defense
        if pos["unrealized_r"] >= 1.5 and pos["sl_state"] == "ORIGINAL":
            pos["sl_state"] = "BREAKEVEN"
            pos["stop_loss"] = entry
            self.live_memory.post_risk_live_update(
                risk_stance="BREAKEVEN_LOCKED",
                trailing_stop_action="LOCK_BE",
                be_locked=True,
                notes="Protected capital: Stop Loss locked to Break-Even."
            )
            self.live_memory.post_inter_agent_message(
                from_agent=f"Clone-{self.clone_id}",
                to_agent="RiskShield",
                message=f"Clone reached +{pos['unrealized_r']:.2f}R! SL moved to Break-Even at ${entry:,.2f}.",
                priority="CRITICAL"
            )

        # Update clone's isolated short-term memory
        self.live_memory.update_live_position_tick(
            current_price=current_price,
            bars_held=pos["bars_held"],
            unrealized_pnl=pos["unrealized_pnl"],
            unrealized_r=pos["unrealized_r"],
            stop_loss=pos["stop_loss"],
            sl_state=pos["sl_state"],
            mae_price=low if direction == "LONG" else high,
            mfe_price=high if direction == "LONG" else low
        )

        if rejection_wick or micro_choch:
            self.live_memory.post_analytical_live_update(
                rejection_wick=rejection_wick,
                micro_choch=micro_choch,
                volume_surge=False,
                structure_state="MICRO_CHIPS_WARNING",
                notes=f"Adverse structure detected on {pos['symbol']}. Tightening guard."
            )

        # Check exit triggers
        exit_action = None
        if direction == "LONG" and current_price <= pos["stop_loss"]:
            exit_action = "STOP_LOSS"
        elif direction == "SHORT" and current_price >= pos["stop_loss"]:
            exit_action = "STOP_LOSS"
        elif direction == "LONG" and current_price >= pos["target_price"]:
            exit_action = "TAKE_PROFIT"
        elif direction == "SHORT" and current_price <= pos["target_price"]:
            exit_action = "TAKE_PROFIT"

        return {
            "status": self.status,
            "clone_id": self.clone_id,
            "symbol": pos["symbol"],
            "unrealized_pnl": pos["unrealized_pnl"],
            "unrealized_r": pos["unrealized_r"],
            "bars_held": pos["bars_held"],
            "exit_action": exit_action
        }

    def merge_jutsu(self, exit_reason: str, exit_price: float) -> Dict[str, Any]:
        """
        Naruto Shadow Clone Merge Jutsu:
        When the clone's trade finishes, it disperses and transmits ALL acquired experience,
        lessons, and forensic data back into the Central Mem0 Brain and Evolution Memory!
        """
        if not self.active_position:
            return {"status": "NO_POSITION_TO_MERGE"}

        self.status = "MERGING"
        pos = self.active_position

        # Compute final realized metrics
        direction = pos["direction"]
        entry = pos["entry_price"]
        sl = pos["stop_loss"]
        units = pos["units"]
        risk_per_unit = abs(entry - sl) if abs(entry - sl) > 0 else (entry * 0.01)

        realized_pnl = (exit_price - entry) * units if direction == "LONG" else (entry - exit_price) * units
        r_multiple = (exit_price - entry) / risk_per_unit if direction == "LONG" else (entry - exit_price) / risk_per_unit

        closed_record = {
            "trade_id": pos["trade_id"],
            "clone_id": self.clone_id,
            "market": self.market,
            "symbol": self.symbol,
            "strategy": self.strategy_name,
            "strategy_name": self.strategy_name,
            "direction": direction,
            "entry_price": entry,
            "exit_price": exit_price,
            "realized_pnl": round(realized_pnl, 2),
            "r_multiple": round(r_multiple, 2),
            "bars_held": pos["bars_held"],
            "exit_reason": exit_reason,
            "exit_type": "STOP_LOSS" if r_multiple <= 0 else "TAKE_PROFIT",
            "closed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # 1. Close Clone's isolated live memory
        self.live_memory.close_and_archive_trade(closed_record)

        # 2. MERGE INTO CENTRAL MEM0 LONG-TERM BRAIN!
        logger.info(f"[ShadowCloneSquad] 🌀 MERGE JUTSU ACTIVATED for [{self.clone_id}]: Transferring trade experience to Central Mem0...")
        self.mem0.record_episodic_trade(closed_record)

        # 3. Disperse Clone
        self.closed_trade_record = closed_record
        self.active_position = None
        self.status = "DISPERSED"

        logger.info(f"[ShadowCloneSquad] ✨ Clone [{self.clone_id}] merged & dispersed successfully. Experience consolidated.")
        return closed_record

    def get_clone_snapshot(self) -> Dict[str, Any]:
        """Provides instant telemetry of this clone for the CEO and UI."""
        return {
            "clone_id": self.clone_id,
            "market": self.market,
            "symbol": self.symbol,
            "strategy_name": self.strategy_name,
            "status": self.status,
            "created_at": self.created_at,
            "active_position": self.active_position,
            "live_memory_snapshot": self.live_memory.get_live_trade_snapshot(),
            "closed_record": self.closed_trade_record
        }


class ShadowCloneManager:
    """
    Supreme Commander of Shadow Clones.
    Maintains multiple concurrent clone squads across global markets,
    coordinates parallel ticks, and manages the Merge Jutsu pipeline.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ShadowCloneManager, cls).__new__(cls)
            cls._instance._init_manager(*args, **kwargs)
        return cls._instance

    def _init_manager(self, max_concurrent_clones: Optional[int] = 100):
        self.max_concurrent_clones = max_concurrent_clones
        self.active_clones: Dict[str, ShadowCloneSquad] = {}
        self.dispersed_clone_history: List[Dict[str, Any]] = []
        self.mem0 = Mem0MemoryEngine()
        self.clone_counter: int = 0
        self.calc = OmniCalculator(owner="ShadowCloneManager")
        logger.info(f"[ShadowCloneManager] 🥷 Shadow Clone Jutsu Manager initialized. Scalable concurrent clones capacity: {self.max_concurrent_clones or 'UNLIMITED'}")

    def spawn_clone_squad(
        self,
        market: str,
        symbol: str,
        strategy_name: str,
        allocated_capital: float = 20000.0
    ) -> Optional[ShadowCloneSquad]:
        """Spawns a new independent Shadow Clone Squad with its own personal OmniCalculator."""
        if self.max_concurrent_clones is not None and len(self.active_clones) >= self.max_concurrent_clones:
            logger.warning(f"[ShadowCloneManager] Max concurrent clone limit ({self.max_concurrent_clones}) reached. Cannot spawn new clone.")
            return None

        self.clone_counter += 1
        clone_id = f"CLONE_{market[:3]}_{symbol}_{self.clone_counter}"
        clone = ShadowCloneSquad(
            clone_id=clone_id,
            market=market,
            symbol=symbol,
            strategy_name=strategy_name,
            allocated_capital=allocated_capital,
            mem0_engine=self.mem0
        )
        self.active_clones[clone_id] = clone
        return clone

    def tick_all_active_clones(self, market_data_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ticks all concurrent clones across multiple markets.
        market_data_map example: { 'CRYPTO:BTC': {'price': 66000, 'high': 66200, 'low': 65800} }
        """
        results = []
        clones_to_merge = []

        for clone_id, clone in list(self.active_clones.items()):
            key = f"{clone.market}:{clone.symbol}"
            data = market_data_map.get(key)
            if not data:
                continue

            res = clone.tick_clone(
                current_price=data.get("price", 0.0),
                high=data.get("high", 0.0),
                low=data.get("low", 0.0),
                rejection_wick=data.get("rejection_wick", False),
                micro_choch=data.get("micro_choch", False)
            )
            results.append(res)

            if res.get("exit_action"):
                clones_to_merge.append((clone_id, res["exit_action"], data.get("price", 0.0)))

        # Execute Merge Jutsu on completed clones
        for clone_id, exit_reason, exit_price in clones_to_merge:
            clone = self.active_clones[clone_id]
            merged = clone.merge_jutsu(exit_reason=exit_reason, exit_price=exit_price)
            self.dispersed_clone_history.append(merged)
            del self.active_clones[clone_id]

        return results

    def kill_clone(self, clone_id: str, reason: str = "CEO_KILL_COMMAND") -> Optional[Dict[str, Any]]:
        """Emergency termination of a specific clone."""
        if clone_id in self.active_clones:
            clone = self.active_clones[clone_id]
            logger.warning(f"[ShadowCloneManager] 🗡️ CEO killed clone [{clone_id}]: {reason}")
            last_price = clone.active_position.get("current_price", 0.0) if clone.active_position else 0.0
            merged = clone.merge_jutsu(exit_reason=f"EMERGENCY_KILL: {reason}", exit_price=last_price)
            self.dispersed_clone_history.append(merged)
            del self.active_clones[clone_id]
            return merged
        return None

    def kill_all_clones(self, reason: str = "CEO_GLOBAL_KILL_SWITCH"):
        """Emergency recall/dispersal of all active clones."""
        logger.warning(f"[ShadowCloneManager] 🛑 CEO issued KILL_ALL_CLONES: {reason}")
        for clone_id in list(self.active_clones.keys()):
            self.kill_clone(clone_id, reason)

    def get_manager_snapshot(self) -> Dict[str, Any]:
        """Provides full clone fleet telemetry for CEO and UI."""
        return {
            "active_clones_count": len(self.active_clones),
            "max_concurrent_clones": self.max_concurrent_clones,
            "active_clones": [c.get_clone_snapshot() for c in self.active_clones.values()],
            "dispersed_history_count": len(self.dispersed_clone_history),
            "recent_merged_clones": self.dispersed_clone_history[-5:]
        }


if __name__ == "__main__":
    mgr = ShadowCloneManager(max_concurrent_clones=5)
    print("Testing Naruto Shadow Clone Jutsu Manager...")
    snap = mgr.get_manager_snapshot()
    print(f"Shadow Clone Fleet Online - Active: {snap['active_clones_count']}/{snap['max_concurrent_clones']}")

