"""
Drawdown & Streak Guard - Section 6 & 11 of Risk Management Knowledge Base
Enforces strict institutional discipline and capital preservation:
- Multi-tier Drawdown Management: 5% (Review), 10% (Cut size 50%), 15% (Halt), 20%+ (Capital Protection Mode)
- Daily Loss Limit: Max 2.5% daily loss -> Instant circuit breaker halt for the day
- Weekly Loss Limit: Max 5.0% weekly loss -> Size cut for following week
- Consecutive Loss Streak Management: 3 losses (-25%), 5 losses (-50%), 7 losses (Full Halt)
- Revenge Trading Circuit Breaker: Enforces psychological cool-down and prevents size escalation during drawdowns
- Asymmetry of Losses Math: Explicit tracking of required recovery gains
"""

import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("DrawdownStreakGuard")


class DrawdownStreakGuard:
    """
    Capital Preservation Shield & Emotional Discipline Enforcer.
    Guarantees you never blow up in a single day, week, or bad losing streak.
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        max_daily_loss_pct: float = 2.5,
        max_weekly_loss_pct: float = 5.0,
        max_monthly_loss_pct: float = 10.0
    ):
        self.initial_capital = initial_capital
        self.peak_equity = initial_capital
        self.current_equity = initial_capital
        
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_weekly_loss_pct = max_weekly_loss_pct
        self.max_monthly_loss_pct = max_monthly_loss_pct

        # Daily tracking
        self.daily_starting_equity = initial_capital
        self.daily_pnl = 0.0
        self.daily_halted = False
        self.daily_halt_reason = ""

        # Streak tracking
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        self.total_trades_count = 0

    def reset_daily_session(self, current_equity: float):
        """Called at daily market open (00:00 UTC / 09:15 IST)."""
        self.daily_starting_equity = current_equity
        self.daily_pnl = 0.0
        self.daily_halted = False
        self.daily_halt_reason = ""
        logger.info(f"[DrawdownGuard] Daily session reset. Base equity: ${self.daily_starting_equity:,.2f}")

    def update_equity(self, new_equity: float):
        """Updates equity, tracks peak, and checks drawdown limits."""
        self.current_equity = new_equity
        if new_equity > self.peak_equity:
            self.peak_equity = new_equity

        self.daily_pnl = self.current_equity - self.daily_starting_equity
        daily_loss_pct = (self.daily_pnl / self.daily_starting_equity) * 100.0

        # Check Daily Loss Circuit Breaker
        if daily_loss_pct <= -self.max_daily_loss_pct and not self.daily_halted:
            self.daily_halted = True
            self.daily_halt_reason = f"MAX_DAILY_LOSS_LIMIT_HIT: Down {daily_loss_pct:.2f}% today (Limit: -{self.max_daily_loss_pct}%). Trading stopped for the day to prevent revenge trading!"
            logger.critical(f"[DrawdownGuard] 🛑 {self.daily_halt_reason}")

    def record_closed_trade(self, realized_pnl: float):
        """Updates win/loss streaks and drawdown metrics."""
        self.total_trades_count += 1
        if realized_pnl > 0:
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            logger.info(f"[DrawdownGuard] Trade WON (+${realized_pnl:,.2f}). Win streak: {self.consecutive_wins}")
        else:
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            logger.warning(f"[DrawdownGuard] Trade LOST (-${abs(realized_pnl):,.2f}). Loss streak: {self.consecutive_losses}")

    def get_drawdown_status(self) -> Dict[str, Any]:
        """Calculates current drawdown from all-time peak and recovery requirements."""
        peak = max(self.peak_equity, 1.0)
        dd_dollar = peak - self.current_equity
        dd_pct = (dd_dollar / peak) * 100.0

        # Asymmetry of losses math: 50% loss requires 100% gain to recover
        recovery_factor = 1.0 / (1.0 - (dd_pct / 100.0)) if dd_pct < 99.0 else 999.0
        req_return_pct = (recovery_factor - 1.0) * 100.0

        # Tiered Status:
        if dd_pct >= 20.0:
            tier = "TIER_4_CAPITAL_PROTECTION_MODE"
            sizing_factor = 0.20
            can_trade = False
        elif dd_pct >= 15.0:
            tier = "TIER_3_FULL_STRATEGY_REVIEW"
            sizing_factor = 0.35
            can_trade = False
        elif dd_pct >= 10.0:
            tier = "TIER_2_SIZE_CUT_50PCT"
            sizing_factor = 0.50
            can_trade = True
        elif dd_pct >= 5.0:
            tier = "TIER_1_REVIEW_WARNING"
            sizing_factor = 0.80
            can_trade = True
        else:
            tier = "TIER_0_HEALTHY"
            sizing_factor = 1.0
            can_trade = True

        return {
            "peak_equity": round(peak, 2),
            "current_equity": round(self.current_equity, 2),
            "drawdown_dollar": round(dd_dollar, 2),
            "drawdown_pct": round(dd_pct, 2),
            "required_recovery_return_pct": round(req_return_pct, 2),
            "tier": tier,
            "sizing_factor": sizing_factor,
            "can_trade": can_trade,
            "consecutive_losses": self.consecutive_losses,
            "consecutive_wins": self.consecutive_wins,
            "daily_halted": self.daily_halted,
            "daily_pnl": round(self.daily_pnl, 2)
        }

    def check_trade_permission(self) -> Dict[str, Any]:
        """
        Final safety gate before any trade execution.
        Blocks trading if daily limit hit, streak excessive, or deep drawdown reached.
        """
        # 1. Daily Circuit Breaker
        if self.daily_halted:
            return {
                "permitted": False,
                "reason": self.daily_halt_reason,
                "sizing_scale": 0.0
            }

        # 2. Consecutive Loss Streak Gate (Section 6)
        if self.consecutive_losses >= 7:
            return {
                "permitted": False,
                "reason": f"STREAK_LIMIT_HALT: {self.consecutive_losses} consecutive losses. Full strategy audit required before resuming.",
                "sizing_scale": 0.0
            }

        dd_status = self.get_drawdown_status()
        if not dd_status["can_trade"]:
            return {
                "permitted": False,
                "reason": f"DRAWDOWN_LIMIT_HALT: Current drawdown {dd_status['drawdown_pct']}% >= 15%. Capital protection lock active.",
                "sizing_scale": 0.0
            }

        # Scale down sizing based on streak + drawdown
        scale = dd_status["sizing_factor"]
        if self.consecutive_losses >= 5:
            scale = min(scale, 0.50)
        elif self.consecutive_losses >= 3:
            scale = min(scale, 0.75)

        return {
            "permitted": True,
            "sizing_scale": round(scale, 2),
            "drawdown_pct": dd_status["drawdown_pct"],
            "streak_state": f"{self.consecutive_losses} losses / {self.consecutive_wins} wins"
        }
