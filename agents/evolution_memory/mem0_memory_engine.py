"""
Mem0 Institutional Long-Term Memory Engine
Inspired by the mem0ai/mem0 open-source agent memory architecture.

Features:
1. Multi-Layer Memory Taxonomy:
   - Episodic Memory: Individual trade post-mortems, forensic replays from Sump Agent, win/loss executions.
   - Semantic Knowledge Store: Generalized trading principles, negative constraints, and regime heuristics.
   - Cross-Market Empirical Memory: Strategy and chart pattern edges across all 8 global share markets.
   - Negative Constraints / Hard Rules: "Never chase in mid-day lull", "Never add to losers", etc.
2. Intelligent Query & Retrieval:
   - Search by market, strategy, regime, or natural language query (keyword + token matching).
   - Agent-specific contextual memory preparation:
     - For Strategy Agent: Recalls champion strategies and trap warnings for the current regime/market.
     - For Analytical Agent: Recalls pattern failure rates and historical traps.
     - For Risk Agent: Recalls drawdowns and historical volatility spikes.
     - For Execution Agent: Recalls slippage and exit timing mistakes.
3. Universal Cross-Agent Sharing:
   - Shared single source of persistent truth across all agents.
   - Persists safely to disk in JSON format with auto-recovery.
"""

import os
import json
import time
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("Mem0MemoryEngine")

MEM0_STORE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "mem0_knowledge_store.json"))


class Mem0MemoryEngine:
    """
    Mem0-style Long-Term Agentic Memory Hub.
    Stores lessons, negative constraints, and trade experiences for cross-agent retrieval.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Mem0MemoryEngine, cls).__new__(cls)
            cls._instance._init_engine(*args, **kwargs)
        return cls._instance

    def _init_engine(self, store_path: str = MEM0_STORE_PATH):
        self.store_path = store_path
        self.memory_store = self._load_store()

    def _load_store(self) -> Dict[str, Any]:
        """Loads persistent Mem0 store from disk or creates default institutional knowledge base."""
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"[Mem0] Could not read memory store ({e}). Initializing fresh store.")

        # Baseline institutional knowledge seed
        default_store = {
            "version": "1.0",
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_memories": 0,
            "semantic_memories": [
                {
                    "id": "sem_1",
                    "category": "EXECUTION_PHILOSOPHY",
                    "content": "Entry is important but exit is everything. Amateurs focus on entry, masters focus on exit.",
                    "tags": ["exit", "mindset", "discipline"],
                    "confidence": 1.0
                },
                {
                    "id": "sem_2",
                    "category": "ANTI_CHASE_RULE",
                    "content": "Never chase price if it has drifted >0.5% away from optimal entry zone. If missed, next setup will come.",
                    "tags": ["chase", "fomo", "entry", "discipline"],
                    "confidence": 1.0
                },
                {
                    "id": "sem_3",
                    "category": "ANTI_MARTINGALE_RULE",
                    "content": "Never add to a losing position. Only add to winners after confirmed Break of Structure (BOS).",
                    "tags": ["pyramiding", "risk", "averaging_down"],
                    "confidence": 1.0
                },
                {
                    "id": "sem_4",
                    "category": "BREAKEVEN_RULE",
                    "content": "Move stop loss to breakeven after +1.0R move in your favor. Never let a winner become a loser.",
                    "tags": ["breakeven", "stop_loss", "trade_management"],
                    "confidence": 1.0
                },
                {
                    "id": "sem_5",
                    "category": "INTRADAY_TIME_RULE",
                    "content": "In Indian markets, avoid entries between 9:15-9:30 AM (opening volatility) and square off by 3:00 PM IST.",
                    "tags": ["timing", "indian_stocks", "sessions"],
                    "confidence": 1.0
                }
            ],
            "episodic_trade_records": [],
            "regime_lessons": {},
            "negative_constraints": [
                "Do NOT enter momentum breakout during midday lull (11:30-13:00) - low volume trap.",
                "Do NOT use tight stops in Crypto during liquidation wicks; use structure stops.",
                "Do NOT add size when in unrealized drawdown.",
                "Do NOT trade without hard stop loss order entered immediately after fill."
            ]
        }
        default_store["total_memories"] = len(default_store["semantic_memories"]) + len(default_store["negative_constraints"])
        self._save_store(default_store)
        return default_store

    def _save_store(self, data: Optional[Dict[str, Any]] = None):
        """Saves memory store to disk safely."""
        if data is None:
            data = self.memory_store
        data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"[Mem0] Error saving memory store: {e}")

    def add_memory(
        self,
        content: str,
        category: str = "LESSON",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Adds a new generalized semantic memory or rule learned from trading.
        """
        mem_id = f"mem_{int(time.time() * 1000)}"
        memory_entry = {
            "id": mem_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "category": category.upper(),
            "content": content,
            "tags": [t.lower() for t in (tags or [])],
            "metadata": metadata or {},
            "confidence": 0.95
        }

        self.memory_store["semantic_memories"].append(memory_entry)
        self.memory_store["total_memories"] += 1
        self._save_store()
        logger.info(f"[Mem0] 🧠 New Long-Term Memory Added: [{category}] {content[:80]}...")
        return memory_entry

    def record_episodic_trade(self, trade_summary: Dict[str, Any]):
        """
        Records full episodic post-mortem and forensic learnings from a completed trade.
        """
        pnl = float(trade_summary.get("realized_pnl", 0.0))
        r_mult = float(trade_summary.get("r_multiple", 0.0))
        strat = trade_summary.get("strategy_name") or trade_summary.get("strategy") or "UNKNOWN"
        market = trade_summary.get("market", "CRYPTO")
        symbol = trade_summary.get("symbol", "UNKNOWN")
        exit_reason = trade_summary.get("exit_reason", "")
        sump_forensics = trade_summary.get("sump_forensics") or {}

        record = {
            "trade_id": trade_summary.get("trade_id", str(time.time())),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "market": market,
            "symbol": symbol,
            "strategy": strat,
            "pnl": pnl,
            "r_multiple": r_mult,
            "bars_held": trade_summary.get("bars_held", 0),
            "exit_reason": exit_reason,
            "counterfactual_verdict": sump_forensics.get("forensic_verdict"),
            "what_if_held": sump_forensics.get("what_if_held_longer", {}).get("verdict"),
            "alternative_strategy_replay": sump_forensics.get("alternative_strategy_replay", {}).get("verdict")
        }

        self.memory_store["episodic_trade_records"].append(record)
        if len(self.memory_store["episodic_trade_records"]) > 100:
            self.memory_store["episodic_trade_records"].pop(0)

        # If trade suffered a loss, induce a negative constraint automatically to prevent repeating mistake
        if r_mult <= -0.5 or pnl < 0.0:
            constraint = f"Careful with '{strat}' in {market} on {symbol}: suffered loss ({exit_reason})."
            if constraint not in self.memory_store["negative_constraints"]:
                self.memory_store["negative_constraints"].append(constraint)

        self._save_store()

    def search_memories(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant semantic memories based on keyword / tag similarity.
        """
        tokens = set(re.findall(r"\w+", query.lower()))
        results = []

        for mem in self.memory_store.get("semantic_memories", []):
            if category and mem.get("category") != category.upper():
                continue

            content_tokens = set(re.findall(r"\w+", mem["content"].lower()))
            tag_tokens = set(mem.get("tags", []))
            match_score = len(tokens.intersection(content_tokens)) * 2 + len(tokens.intersection(tag_tokens)) * 3

            if match_score > 0:
                results.append((match_score, mem))

        # Sort by match score
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:limit]]

    def get_context_for_agent(
        self,
        agent_name: str,
        market: str,
        symbol: str,
        strategy_name: Optional[str] = None,
        market_regime: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assembles curated memory context specifically tailored for the calling agent.
        """
        agent_upper = agent_name.upper()
        relevant_memories = self.search_memories(f"{market} {symbol} {strategy_name or ''} {market_regime or ''}", limit=4)
        negative_rules = self.memory_store.get("negative_constraints", [])[:4]

        # Recent relevant episodic trades in this market/symbol
        recent_trades = [
            t for t in self.memory_store.get("episodic_trade_records", [])[-20:]
            if t.get("market") == market or t.get("symbol") == symbol
        ][-3:]

        return {
            "agent": agent_upper,
            "target_market": market,
            "target_symbol": symbol,
            "curated_memories": relevant_memories,
            "negative_constraints": negative_rules,
            "recent_episodic_precedents": recent_trades,
            "memory_guidance": f"Mem0 context loaded: {len(relevant_memories)} principles, {len(negative_rules)} constraints."
        }

    def get_all_negative_constraints(self) -> List[str]:
        """Returns all induced negative rules to avoid repeating past mistakes."""
        return self.memory_store.get("negative_constraints", [])
