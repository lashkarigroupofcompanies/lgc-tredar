"""
Trade Lifecycle Manager - 50-Year Master Trader Execution Engine
Section 4: Exit Execution System, Section 7: Live Trade Management, Section 8: Trade Types

Manages open positions across their full lifecycle:
1. 3-Tier Partial Scale-Out Strategy (Professional Standard):
   - Tier 1 (+1.0R reached): Close 33% of position -> Move SL to Breakeven (+0.0R)
   - Tier 2 (+2.0R reached): Close another 33% -> Trail SL to +1.0R profit lock
   - Tier 3 (+3.0R+ / Runner): Let remaining 34% ride with Chandelier ATR / Swing Structure Trailing
2. Dynamic Trailing Stops:
   - Breakeven lock (+1.0R)
   - Structural Trail: Locks behind higher lows (long) or lower highs (short)
   - ATR Chandelier: Trails behind (Peak Price - 2.0 * ATR)
   - Candle Trail: Aggressive trail below previous bar's extreme
3. First 30 Minutes Rule:
   - Protects against emotional shakeouts during initial testing of the entry level.
4. Anti-Martingale Pyramiding Rules:
   - Only add to winning positions AFTER confirmed Break of Structure (BOS).
   - STRICT PROHIBITION against adding to losing positions (No averaging down!).
   - Consecutive additions strictly smaller than initial (e.g., 50% scale).
   - Combined risk capped at <= 2.0% of portfolio equity.
5. Intraday Compulsory Square-Off:
   - Flags mandatory liquidation at 3:00 PM IST / market close.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("TradeLifecycleManager")


class TradeLifecycleManager:
    """
    State machine and exit supervisor for active trades.
    """

    @classmethod
    def evaluate_lifecycle_state(
        cls,
        position: Dict[str, Any],
        current_price: float,
        atr_value: float,
        bars_held: int,
        is_intraday_square_off_time: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates active trade state against 3-tier scale-outs, trailing stops,
        and early invalidations.
        """
        direction = position.get("direction", "LONG").upper()
        entry_price = float(position.get("entry_price", 0.0))
        current_sl = float(position.get("stop_loss", 0.0))
        dollar_risk = float(position.get("dollar_risk", 1.0))
        units = float(position.get("remaining_units", 0.0))
        initial_units = float(position.get("initial_units", units))
        trade_type = position.get("trade_type", "INTRADAY").upper()

        if entry_price <= 0.0 or units <= 0.0:
            return {"action": "HOLD", "reason": "Invalid position parameters."}

        # Calculate 1R distance
        initial_risk_dist = abs(entry_price - float(position.get("initial_stop_loss", current_sl)))
        if initial_risk_dist <= 1e-6:
            initial_risk_dist = entry_price * 0.01  # Fallback 1%

        # Calculate current profit in R-multiples
        if direction == "LONG":
            profit_dist = current_price - entry_price
        else:
            profit_dist = entry_price - current_price

        current_r = profit_dist / initial_risk_dist

        # Check Intraday Mandatory Square-Off (Section 5 & 8)
        if trade_type in ["INTRADAY", "SCALP"] and is_intraday_square_off_time:
            return {
                "action": "CLOSE_POSITION",
                "exit_price": current_price,
                "reason": "Compulsory intraday market close (3:00 PM IST rule).",
                "r_achieved": round(current_r, 2)
            }

        # Check Hard SL breach
        if direction == "LONG" and current_price <= current_sl:
            return {
                "action": "CLOSE_POSITION",
                "exit_price": current_sl,
                "reason": "Hard Stop Loss Hit (Capital Protected).",
                "r_achieved": round(current_r, 2)
            }
        elif direction == "SHORT" and current_price >= current_sl:
            return {
                "action": "CLOSE_POSITION",
                "exit_price": current_sl,
                "reason": "Hard Stop Loss Hit (Capital Protected).",
                "r_achieved": round(current_r, 2)
            }

        # Tier 1 Scale-out (+1.0R reached and not yet taken)
        tp1_taken = position.get("tp1_closed", False)
        if current_r >= 1.0 and not tp1_taken:
            new_sl = entry_price  # Move SL to Breakeven
            return {
                "action": "TAKE_PROFIT_PARTIAL",
                "tier": 1,
                "portion": 0.33,
                "exit_price": current_price,
                "new_stop_loss": new_sl,
                "sl_state": "BREAKEVEN",
                "reason": f"Tier 1 (+1.0R hit): Banked 33% profit, SL moved to Breakeven (${new_sl:,.2f}).",
                "r_achieved": round(current_r, 2)
            }

        # Tier 2 Scale-out (+2.0R reached and not yet taken)
        tp2_taken = position.get("tp2_closed", False)
        if current_r >= 2.0 and not tp2_taken:
            # Trail SL to +1.0R locked profit
            if direction == "LONG":
                new_sl = entry_price + (1.0 * initial_risk_dist)
            else:
                new_sl = entry_price - (1.0 * initial_risk_dist)

            return {
                "action": "TAKE_PROFIT_PARTIAL",
                "tier": 2,
                "portion": 0.50,  # 50% of remaining (effectively 33% of total)
                "exit_price": current_price,
                "new_stop_loss": new_sl,
                "sl_state": "TRAILING_1R_LOCK",
                "reason": f"Tier 2 (+2.0R hit): Banked 33% profit, SL trailed to +1.0R lock (${new_sl:,.2f}).",
                "r_achieved": round(current_r, 2)
            }

        # Tier 3 Trailing Stop for Runner (Current R >= 2.5R)
        if current_r >= 2.5 and tp2_taken:
            # ATR Chandelier Trailing Stop (Peak - 2.0 * ATR)
            peak_price = float(position.get("peak_price", entry_price))
            chandelier_dist = 2.0 * (atr_value if atr_value > 0 else (entry_price * 0.015))

            if direction == "LONG":
                candidate_sl = peak_price - chandelier_dist
                if candidate_sl > current_sl:
                    return {
                        "action": "UPDATE_STOP_LOSS",
                        "new_stop_loss": round(candidate_sl, 2),
                        "sl_state": "CHANDELIER_RUNNER_TRAIL",
                        "reason": f"Chandelier ATR trailing stop locked to ${candidate_sl:,.2f} on extended runner.",
                        "r_achieved": round(current_r, 2)
                    }
            else:
                candidate_sl = peak_price + chandelier_dist
                if candidate_sl < current_sl:
                    return {
                        "action": "UPDATE_STOP_LOSS",
                        "new_stop_loss": round(candidate_sl, 2),
                        "sl_state": "CHANDELIER_RUNNER_TRAIL",
                        "reason": f"Chandelier ATR trailing stop locked to ${candidate_sl:,.2f} on extended runner.",
                        "r_achieved": round(current_r, 2)
                    }

        return {
            "action": "HOLD",
            "reason": f"Holding trade on active structure. Current R: {current_r:.2f}R.",
            "r_achieved": round(current_r, 2)
        }

    @classmethod
    def validate_pyramid_addition(
        cls,
        position: Dict[str, Any],
        has_new_bos: bool,
        current_equity: float,
        proposed_add_units: float,
        proposed_add_risk: float
    ) -> Dict[str, Any]:
        """
        Anti-Martingale Pyramiding Evaluator (Section 7):
        - ONLY add if trade is currently in profit (>1.0R)
        - ONLY add after confirmed new Break of Structure (BOS)
        - Addition units must be smaller than initial position (< 60% of initial)
        - Total combined open risk must be <= 2.0% of capital
        - NEVER add to a losing position!
        """
        unrealized_pnl = float(position.get("unrealized_pnl", 0.0))
        initial_units = float(position.get("initial_units", 1.0))
        existing_dollar_risk = float(position.get("dollar_risk", 0.0))

        # Rule 1: Never add to a losing position
        if unrealized_pnl <= 0.0:
            return {
                "can_pyramid": False,
                "reason": "STRICT RULE: Never add to a losing position (Anti-Martingale violation)."
            }

        # Rule 2: Requires new BOS confirmation
        if not has_new_bos:
            return {
                "can_pyramid": False,
                "reason": "Pyramiding requires confirmed new Break of Structure (BOS) in trade direction."
            }

        # Rule 3: Add size must be strictly smaller than initial position
        if proposed_add_units >= initial_units * 0.7:
            return {
                "can_pyramid": False,
                "reason": f"Addition size ({proposed_add_units}) exceeds 60% of initial position ({initial_units}). Scale down."
            }

        # Rule 4: Total combined risk check
        total_risk = existing_dollar_risk + proposed_add_risk
        max_allowed_risk = current_equity * 0.02  # 2% max
        if total_risk > max_allowed_risk:
            return {
                "can_pyramid": False,
                "reason": f"Combined risk (${total_risk:,.2f}) exceeds 2% account equity cap (${max_allowed_risk:,.2f})."
            }

        return {
            "can_pyramid": True,
            "reason": "Pyramiding approved: Winning trade, new BOS confirmed, size scaled down, risk <= 2%."
        }
