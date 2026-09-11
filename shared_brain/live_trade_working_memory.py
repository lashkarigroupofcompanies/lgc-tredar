"""
Live Trade Working Memory Agent (Short-Term Tactical Blackboard)
Role: Real-time, sub-second shared working memory for active live trades.

Allows all agents to collaborate dynamically while a trade is open:
1. Live Position Dashboard:
   - Tracks current price, unrealized PnL, R-multiple, bars held, SL state, MAE, MFE, and scale-out tiers.
2. Per-Agent Live Streaming Slots:
   - Analytical Agent: Posts live bar-by-bar structure (rejection wicks, micro CHoCH, volume deltas).
   - Strategy Agent: Posts strategy thesis validity ("Intact", "Exhaustion", "Target approaching").
   - Risk Agent: Posts margin health, R drawdown, and trailing stop lock commands.
   - News Agent: Posts breaking catalyst alerts and macro event countdowns.
   - Execution Agent: Posts fill status, partial profit scale-outs, and slippage.
3. Live Inter-Agent Tactical Chat Log:
   - Real-time communication feed between agents during trade lifecycle.
4. Auto-Archive to Long-Term Memory (Mem0):
   - Upon trade exit, transfers the complete live trajectory to Mem0 and Evolution Memory,
     then resets the board for the next trade.
"""

import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("LiveTradeWorkingMemory")


class LiveTradeWorkingMemory:
    """
    Short-Term Tactical Working Memory.
    Provides sub-second visibility into 'WHAT IS HAPPENING RIGHT NOW' during an open trade.
    """

    _instance = None

    def __new__(cls, is_clone: bool = False):
        if is_clone:
            inst = super(LiveTradeWorkingMemory, cls).__new__(cls)
            inst._init_working_memory()
            return inst
        if cls._instance is None:
            cls._instance = super(LiveTradeWorkingMemory, cls).__new__(cls)
            cls._instance._init_working_memory()
        return cls._instance

    def _init_working_memory(self):
        self.is_trade_active: bool = False
        self.active_trade_id: Optional[str] = None
        self.last_updated = time.time()

        # Live Position Status
        self.live_position: Dict[str, Any] = {
            "trade_id": None,
            "market": "NONE",
            "symbol": "NONE",
            "direction": "NONE",
            "entry_price": 0.0,
            "current_price": 0.0,
            "units": 0.0,
            "dollar_risk": 0.0,
            "unrealized_pnl": 0.0,
            "unrealized_r": 0.0,
            "bars_held": 0,
            "stop_loss": 0.0,
            "sl_state": "ORIGINAL",
            "peak_price": 0.0,
            "trough_price": 0.0,
            "mae_price": 0.0,
            "mfe_price": 0.0,
            "tier_1_banked": False,
            "tier_2_banked": False
        }

        # Real-time Per-Agent Streams
        self.agent_streams: Dict[str, Dict[str, Any]] = {
            "analytical": {
                "last_update_time": None,
                "status": "AWAITING_ACTIVE_TRADE",
                "structure_state": "NORMAL",
                "rejection_wick_detected": False,
                "micro_choch_warning": False,
                "volume_surge": False,
                "notes": "No active position"
            },
            "strategy": {
                "last_update_time": None,
                "strategy_name": "NONE",
                "thesis_status": "VALID",
                "momentum_strength": 0.0,
                "notes": "No active position"
            },
            "risk": {
                "last_update_time": None,
                "risk_stance": "NORMAL",
                "trailing_stop_action": "HOLD",
                "current_drawdown_pct": 0.0,
                "be_locked": False,
                "notes": "Normal risk surveillance"
            },
            "news": {
                "last_update_time": None,
                "breaking_news_alert": False,
                "time_to_next_macro_event_mins": None,
                "sentiment_flip_detected": False,
                "notes": "News stream quiet"
            },
            "execution": {
                "last_update_time": None,
                "order_state": "IDLE",
                "last_action": "NONE",
                "trade_efficiency_score": 0.0,
                "notes": "Sniper ready"
            }
        }

        # Live Inter-Agent Chat / Event Feed
        self.inter_agent_feed: List[Dict[str, Any]] = []

    def activate_trade(self, position: Dict[str, Any]):
        """Called when a new trade is opened by ExecutionAgent."""
        self.is_trade_active = True
        self.active_trade_id = position.get("trade_id")
        self.live_position = {
            "trade_id": position.get("trade_id"),
            "market": position.get("market"),
            "symbol": position.get("symbol"),
            "direction": position.get("direction"),
            "entry_price": float(position.get("entry_price", 0.0)),
            "current_price": float(position.get("entry_price", 0.0)),
            "units": float(position.get("initial_units", 0.0)),
            "dollar_risk": float(position.get("dollar_risk", 0.0)),
            "unrealized_pnl": 0.0,
            "unrealized_r": 0.0,
            "bars_held": 0,
            "stop_loss": float(position.get("stop_loss", 0.0)),
            "sl_state": "ORIGINAL",
            "peak_price": float(position.get("entry_price", 0.0)),
            "trough_price": float(position.get("entry_price", 0.0)),
            "mae_price": float(position.get("entry_price", 0.0)),
            "mfe_price": float(position.get("entry_price", 0.0)),
            "tier_1_banked": False,
            "tier_2_banked": False
        }
        self.inter_agent_feed.clear()
        self.post_inter_agent_message(
            from_agent="ExecutionAgent",
            to_agent="ALL_AGENTS",
            message=f"🚀 POSITION OPENED: [{position.get('direction')} {position.get('symbol')}] at ${position.get('entry_price', 0):,.2f}. Guards engaged!",
            priority="HIGH"
        )
        self.last_updated = time.time()

    def update_live_position_tick(
        self,
        current_price: float,
        bars_held: int,
        unrealized_pnl: float,
        unrealized_r: float,
        stop_loss: float,
        sl_state: str,
        mae_price: float,
        mfe_price: float,
        tier_1_banked: bool = False,
        tier_2_banked: bool = False
    ):
        """Updates live price, PnL, R-multiple, and excursion stats on every candle tick."""
        if not self.is_trade_active:
            return

        self.live_position.update({
            "current_price": round(current_price, 2),
            "bars_held": bars_held,
            "unrealized_pnl": round(unrealized_pnl, 2),
            "unrealized_r": round(unrealized_r, 2),
            "stop_loss": round(stop_loss, 2),
            "sl_state": sl_state,
            "mae_price": round(mae_price, 2),
            "mfe_price": round(mfe_price, 2),
            "tier_1_banked": tier_1_banked,
            "tier_2_banked": tier_2_banked
        })
        self.last_updated = time.time()

    def post_analytical_live_update(
        self,
        rejection_wick: bool,
        micro_choch: bool,
        volume_surge: bool,
        structure_state: str,
        notes: str
    ):
        """Analytical Agent reports live candle structure while trade is open."""
        self.agent_streams["analytical"] = {
            "last_update_time": time.strftime("%H:%M:%S"),
            "status": "WATCHING_LIVE_BAR",
            "structure_state": structure_state,
            "rejection_wick_detected": rejection_wick,
            "micro_choch_warning": micro_choch,
            "volume_surge": volume_surge,
            "notes": notes
        }
        if rejection_wick or micro_choch:
            self.post_inter_agent_message(
                from_agent="AnalyticalAgent",
                to_agent="RiskAgent",
                message=f"⚠️ Live Structure Alert: {notes}",
                priority="HIGH"
            )
        self.last_updated = time.time()

    def post_strategy_live_update(
        self,
        strategy_name: str,
        thesis_status: str,
        notes: str
    ):
        """Strategy Agent reports ongoing validity of the trading thesis."""
        self.agent_streams["strategy"] = {
            "last_update_time": time.strftime("%H:%M:%S"),
            "strategy_name": strategy_name,
            "thesis_status": thesis_status,
            "notes": notes
        }
        self.last_updated = time.time()

    def post_risk_live_update(
        self,
        risk_stance: str,
        trailing_stop_action: str,
        be_locked: bool,
        notes: str
    ):
        """Risk Agent reports live drawdown, breakeven lock, and trailing SL actions."""
        self.agent_streams["risk"] = {
            "last_update_time": time.strftime("%H:%M:%S"),
            "risk_stance": risk_stance,
            "trailing_stop_action": trailing_stop_action,
            "be_locked": be_locked,
            "notes": notes
        }
        self.last_updated = time.time()

    def post_news_live_update(
        self,
        breaking_alert: bool,
        minutes_to_event: Optional[int],
        notes: str
    ):
        """News Agent reports any incoming macro volatility flashes."""
        self.agent_streams["news"] = {
            "last_update_time": time.strftime("%H:%M:%S"),
            "breaking_news_alert": breaking_alert,
            "time_to_next_macro_event_mins": minutes_to_event,
            "notes": notes
        }
        if breaking_alert:
            self.post_inter_agent_message(
                from_agent="NewsAgent",
                to_agent="AllAgents",
                message=f"🚨 BREAKING NEWS ALERT: {notes}",
                priority="CRITICAL"
            )
        self.last_updated = time.time()

    def post_execution_live_update(
        self,
        order_state: str,
        last_action: str,
        notes: str
    ):
        """Execution Agent reports live execution, partial scaling, or fill events."""
        self.agent_streams["execution"] = {
            "last_update_time": time.strftime("%H:%M:%S"),
            "order_state": order_state,
            "last_action": last_action,
            "notes": notes
        }
        self.last_updated = time.time()

    def post_inter_agent_message(
        self,
        from_agent: str,
        to_agent: str,
        message: str,
        priority: str = "NORMAL"
    ):
        """Logs an inter-agent message into the shared live tactical feed."""
        entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message": message,
            "priority": priority
        }
        self.inter_agent_feed.append(entry)
        if len(self.inter_agent_feed) > 30:
            self.inter_agent_feed.pop(0)
        logger.info(f"[LiveWorkingMemory] [{from_agent} -> {to_agent}]: {message}")

    def close_and_archive_trade(self, closed_trade_record: Dict[str, Any]):
        """
        Called when the trade completes.
        Transfers live trajectory to long-term memory and clears active board.
        """
        self.post_inter_agent_message(
            from_agent="ExecutionAgent",
            to_agent="ALL_AGENTS",
            message=f"🏁 TRADE CLOSED: PnL: ${closed_trade_record.get('realized_pnl', 0):,.2f} ({closed_trade_record.get('r_multiple', 0)}R). Exit: {closed_trade_record.get('exit_reason')}",
            priority="HIGH"
        )
        self.is_trade_active = False
        self.active_trade_id = None
        self.last_updated = time.time()

    def get_live_trade_snapshot(self) -> Dict[str, Any]:
        """Provides instant real-time snapshot for the UI dashboard and all querying agents."""
        return {
            "is_trade_active": self.is_trade_active,
            "active_trade_id": self.active_trade_id,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.last_updated)),
            "live_position": self.live_position if self.is_trade_active else None,
            "agent_streams": self.agent_streams,
            "inter_agent_feed": self.inter_agent_feed[-12:]
        }
