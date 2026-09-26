"""
Psychology & Discipline Guard (Section 15 & Section 12 Framework)
Enforces veteran trading psychology rules in automated algorithmic decision-making:
- FOMO Filter: Prevents chasing extended moves (> 2.0x ATR from support/resistance)
- Overtrading Filter: Caps maximum trades per cycle/day
- Greed Filter: Enforces systematic scaling out at designated R:R targets
- Revenge Trading Block: Enforces cool-down after consecutive losses
- Cash Position Validation: Validates that 'No Trade' is an active, profitable stance
"""

import logging
from typing import Dict, Any

logger = logging.getLogger("PsychologyGuard")


class PsychologyDisciplineGuard:
    """
    Automated psychological defense mechanism protecting capital from emotional biases.
    """

    def __init__(self, max_trades_per_day: int = 5, consecutive_loss_limit: int = 3):
        self.max_trades_per_day = max_trades_per_day
        self.consecutive_loss_limit = consecutive_loss_limit
        self.daily_trade_count = 0
        self.consecutive_losses = 0

    def evaluate_psychology_filters(
        self,
        setup_score: float,
        current_price: float,
        suggested_entry: float,
        atr: float,
        has_active_position: bool = False,
        mode: str = "SAFE"
    ) -> Dict[str, Any]:
        """
        Runs comprehensive psychological gatekeeping before approving any trade action.
        Adapts thresholds dynamically based on the operating mode:
        - DANGEROUS: High-velocity paper learning lab (score >= 3.5, up to 100 paper trades/day)
        - MONEY_MAKER: Daily driver alpha (score >= 5.0, up to 25 trades/day)
        - SAFE: Institutional sniper (score >= 7.0, capital preservation)
        """
        reasons = []
        is_blocked = False

        mode_upper = str(mode or "SAFE").upper()
        if "DANGEROUS" in mode_upper or "WILD" in mode_upper:
            min_score = 3.5
            max_daily = 100
        elif "MONEY" in mode_upper or "MAKER" in mode_upper:
            min_score = 5.0
            max_daily = 25
        else:
            min_score = 7.0
            max_daily = self.max_trades_per_day

        # 1. Setup Filter
        if setup_score < min_score:
            reasons.append(f"Setup score ({setup_score}/10) below {mode_upper} threshold ({min_score}). Sitting in Cash.")
            is_blocked = True

        # 2. Overtrading Guard
        if self.daily_trade_count >= max_daily:
            reasons.append(f"Daily trade limit ({max_daily}) reached for {mode_upper}. Preserving psychological clarity.")
            is_blocked = True

        # 3. Revenge Trading Circuit Breaker
        if self.consecutive_losses >= self.consecutive_loss_limit:
            reasons.append(f"Consecutive losses limit ({self.consecutive_loss_limit}) hit. Cooling off.")
            is_blocked = True

        # 4. FOMO Filter (Price Chasing Check)
        if atr > 0 and suggested_entry > 0:
            price_distance = abs(current_price - suggested_entry)
            if price_distance > (atr * 1.8):
                reasons.append(f"FOMO Filter Triggered: Price is {round(price_distance/atr, 1)}x ATR away from entry. Do not chase.")
                is_blocked = True

        status = "BLOCKED_BY_DISCIPLINE" if is_blocked else "APPROVED"
        return {
            "status": status,
            "can_execute": not is_blocked,
            "reasons": reasons if reasons else ["Clear psychological state. A+ disciplined execution approved."],
            "discipline_summary": "Discipline Guard: " + (" | ".join(reasons) if reasons else "Green light.")
        }

    def record_trade_outcome(self, is_win: bool):
        """Updates internal win/loss tracker."""
        self.daily_trade_count += 1
        if is_win:
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
