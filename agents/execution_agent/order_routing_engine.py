"""
Order Routing Engine - 50-Year Master Trader Execution Engine
Section 3: Entry Execution System & Section 6: Order Types Master Knowledge

Enforces:
1. Four Order Types:
   - LIMIT: Placed at proximal/distal edge of zone before price arrives (zero emotion, optimal fill).
   - MARKET: Guaranteed fill, reserved for confirmed momentum post-candle close on liquid pairs.
   - STOP_LIMIT: Breakout entry (Stop price + 0.1-0.2% limit buffer to avoid runaway slippage).
   - STOP_MARKET: Hard guaranteed exit trigger for stop-losses.
2. Five Timing Models:
   - CANDLE_CLOSE: Waits for candle to close across key level (avoids false breakouts).
   - WICK_REJECTION: Enters on zone rejection wick + pin bar confirmation.
   - PATTERN_COMPLETION: Enters on engulfing, inside-bar break, or neckline break.
   - RETEST: Enters on post-breakout pullback retest (highest probability).
   - AGGRESSIVE: Limits placed inside zone before full confirmation (best price, smaller size).
3. 8-Tier Entry Trigger Hierarchy (Priority Order):
   1. HTF Bias Confirmed (Daily/4H trend alignment)
   2. Price at Key Level (S&R, S&D zone, Fibonacci 0.618, FVG)
   3. Session Timing Aligned (Killzone or Prime session)
   4. Liquidity Swept (Stop hunt completed)
   5. Displacement Candle (Strong impulse move away from zone)
   6. Candlestick Confirmation Pattern (Engulfing, Pin bar, Hammer)
   7. LTF Structure Shift (CHoCH / BOS on 5M/15M)
   8. Structural SL Defined & R:R >= 1:2
   Scoring:
     8/8 = PERFECT SETUP (100% conviction)
     6-7 = HIGH QUALITY (Standard execution)
     4-5 = ACCEPTABLE (Reduced size / conservative)
     < 4 = SKIP / REJECT (No structural edge)
4. Anti-Chase Protection:
   - Blocks entry if price has moved >0.5% away from optimal level (FOMO prevention).
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("OrderRoutingEngine")


class OrderRoutingEngine:
    """
    Precision Order Router & 8-Tier Entry Trigger Evaluator.
    Guarantees sniper execution quality and eliminates emotional chasing.
    """

    MAX_CHASE_DEVIATION_PCT = 0.5  # 0.5% max drift from optimal entry level

    @classmethod
    def evaluate_entry_trigger_hierarchy(
        cls,
        htf_bias_aligned: bool,
        price_at_key_level: bool,
        session_timing_ok: bool,
        liquidity_swept: bool,
        displacement_candle: bool,
        candlestick_pattern_confirmed: bool,
        ltf_structure_shift: bool,
        sl_defined_and_rr_valid: bool = True,
        sl_and_rr_valid: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Evaluates the 8-Tier Entry Trigger Hierarchy.
        Returns total score (0-8), rating, and execution clearance.
        """
        if sl_and_rr_valid is not None:
            sl_defined_and_rr_valid = sl_and_rr_valid

        tier_checks = {
            "tier_1_htf_bias": htf_bias_aligned,
            "tier_2_key_level": price_at_key_level,
            "tier_3_session_timing": session_timing_ok,
            "tier_4_liquidity_swept": liquidity_swept,
            "tier_5_displacement_candle": displacement_candle,
            "tier_6_candlestick_pattern": candlestick_pattern_confirmed,
            "tier_7_ltf_structure_shift": ltf_structure_shift,
            "tier_8_sl_and_rr_valid": sl_defined_and_rr_valid
        }

        score = sum(1 for passed in tier_checks.values() if passed)

        if score == 8:
            rating = "PERFECT_SETUP"
            can_enter = True
            action = "AGGRESSIVE_SNIPER_ENTRY"
        elif score >= 6:
            rating = "HIGH_QUALITY"
            can_enter = True
            action = "STANDARD_EXECUTION"
        elif score >= 4:
            rating = "ACCEPTABLE"
            can_enter = True
            action = "CONSERVATIVE_REDUCED_SIZE"
        else:
            rating = "SUBPAR_NO_EDGE"
            can_enter = False
            action = "SKIP_SETUP"

        return {
            "score": score,
            "max_score": 8,
            "score_pct": round(score / 8.0 * 100.0, 1),
            "rating": rating,
            "can_enter": can_enter,
            "action": action,
            "tier_checks": tier_checks
        }

    @classmethod
    def validate_anti_chase(
        cls,
        direction: str,
        intended_price: float,
        current_market_price: float
    ) -> Dict[str, Any]:
        """
        Prevents chasing price after the move has already left the zone (Section 3 rule).
        """
        if intended_price <= 0.0 or current_market_price <= 0.0:
            return {"chasing": False, "deviation_pct": 0.0}

        dev_pct = abs(current_market_price - intended_price) / intended_price * 100.0
        
        # Check if price moved away adversely from our entry
        if direction.upper() == "LONG" and current_market_price > intended_price:
            if dev_pct > cls.MAX_CHASE_DEVIATION_PCT:
                return {
                    "chasing": True,
                    "deviation_pct": round(dev_pct, 2),
                    "reason": f"Price drifted {dev_pct:.2f}% above optimal entry. Chasing forbidden."
                }
        elif direction.upper() == "SHORT" and current_market_price < intended_price:
            if dev_pct > cls.MAX_CHASE_DEVIATION_PCT:
                return {
                    "chasing": True,
                    "deviation_pct": round(dev_pct, 2),
                    "reason": f"Price drifted {dev_pct:.2f}% below optimal entry. Chasing forbidden."
                }

        return {"chasing": False, "deviation_pct": round(dev_pct, 2), "reason": "Price within acceptable entry zone."}

    @classmethod
    def select_order_type(
        cls,
        market: str,
        timing_method: str,
        volatility_state: str = "NORMAL",
        is_breakout: bool = False
    ) -> Dict[str, Any]:
        """
        Selects optimal order routing mechanism (Section 3 & Section 6):
        - Limit Order for key levels and S/D zones
        - Stop-Limit for confirmed breakouts
        - Market Order only for momentum candle close on liquid assets
        """
        timing_upper = timing_method.upper()

        if is_breakout:
            # Stop-Limit prevents flash gaps
            return {
                "order_type": "STOP_LIMIT",
                "buffer_pct": 0.0015,  # 0.15% buffer
                "rationale": "Breakout trade: Stop-Limit order set with 0.15% limit buffer to avoid runaway slippage."
            }

        if timing_upper in ["RETEST", "AGGRESSIVE", "WICK_REJECTION"]:
            return {
                "order_type": "LIMIT",
                "buffer_pct": 0.0,
                "rationale": "Zone retest/limit: Limit order placed at proximal edge for zero slippage."
            }

        if timing_upper == "CANDLE_CLOSE":
            # Liquid assets can use Market on candle close
            if market.upper() in ["CRYPTO", "US_STOCKS", "INDIAN_STOCKS"]:
                return {
                    "order_type": "MARKET",
                    "buffer_pct": 0.0,
                    "rationale": "Candle close confirmation: Immediate market execution with pre-set SL bracket."
                }

        return {
            "order_type": "LIMIT",
            "buffer_pct": 0.0,
            "rationale": "Default institutional precision limit order."
        }
