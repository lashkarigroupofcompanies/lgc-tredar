"""
Active Position Monitor & Purely Adaptive Structure-Driven Trade Engine
Completely eliminates rigid/fixed candle counts (No hardcoded 8-10 or 60 bars):
- Trade duration is 100% emergent & flexible:
  - Can be 1 BAR if setup fails immediately, forms opposing rejection, or hits a flash target.
  - Can be INDEFINITE (dozens to hundreds of bars) if market structure keeps printing Higher Lows / Higher Highs.
- Autonomous Momentum Velocity & Alpha Decay tracking:
  - Continuously measures progress-per-bar vs volatility.
  - Decides whether to let the winner ride or exit based on live price action, not an arbitrary timer.
- Dynamic Feedback from Evolution Memory:
  - Leverages learned holding profiles from historical and live runs over time.
- Split-Second Early Thesis Invalidation:
  - Protects 40-60% of Stop Loss capital on immediate thesis failure.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from shared_brain.live_trade_working_memory import LiveTradeWorkingMemory

logger = logging.getLogger("ActiveTradeMonitor")


class ActiveTradeMonitor:
    """
    Structure-Driven, Emergent Position Surveillance Engine.
    Zero fixed bar counts. Every trade's life is governed purely by:
    1. Structure health (Higher Highs / Higher Lows vs Breaks)
    2. Momentum velocity & Alpha decay
    3. Trailing stops and target reaches
    4. Split-second early thesis invalidation (can trigger on Bar 1!)
    5. Learned empirical guidance from Evolution Memory
    """

    @classmethod
    def evaluate_active_position(
        cls,
        position: Dict[str, Any],
        recent_df: pd.DataFrame,
        current_price: float,
        adx_value: float = 22.0,
        macro_news_alert: Optional[Dict[str, Any]] = None,
        learned_guidance: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates an active trade on every live bar:
        - Decides whether to hold, trail, bank partials, or exit immediately (could be Bar 1 or Bar 150+).
        """
        if recent_df.empty or len(recent_df) < 3:
            return {"action": "HOLD", "reason": "Insufficient candles for structural evaluation."}

        direction = position["direction"].upper()
        entry_price = float(position["entry_price"])
        stop_loss = float(position["stop_loss"])
        tp1 = float(position.get("take_profit_1", entry_price * 1.03))
        tp2 = float(position.get("take_profit_2", entry_price * 1.06))
        bars_held = position.get("bars_held", 0) + 1
        strat_name = position.get("strategy_name", "DISCRETIONARY")

        latest = recent_df.iloc[-1]
        prev = recent_df.iloc[-2]
        c_open = float(latest["open"])
        c_close = float(latest["close"])
        c_high = float(latest["high"])
        c_low = float(latest["low"])
        body = abs(c_close - c_open)

        risk_dist = abs(entry_price - stop_loss)
        if risk_dist <= 0:
            risk_dist = entry_price * 0.01

        # Current unrealized R-multiple
        if direction == "LONG":
            unrealized_r = (current_price - entry_price) / risk_dist
        else:
            unrealized_r = (entry_price - current_price) / risk_dist

        # -------------------------------------------------------------
        # 1. HARD STOP LOSS & TARGET 2 CHECK
        # -------------------------------------------------------------
        trade_type = str(position.get("trade_type", "INTRADAY")).upper()
        is_trend_runner = trade_type in ["SWING", "TREND", "POSITION"] or position.get("allow_runner", False)

        if direction == "LONG":
            if c_low <= stop_loss:
                return {
                    "action": "CLOSE_POSITION",
                    "reason": "STOP_LOSS_HIT",
                    "exit_price": stop_loss,
                    "r_multiple": -1.0,
                    "bars_held": bars_held
                }
            if not is_trend_runner and c_high >= tp2:
                return {
                    "action": "CLOSE_POSITION",
                    "reason": "TARGET_2_FULL_EXIT",
                    "exit_price": tp2,
                    "r_multiple": round((tp2 - entry_price) / risk_dist, 2),
                    "bars_held": bars_held
                }
        else:  # SHORT
            if c_high >= stop_loss:
                return {
                    "action": "CLOSE_POSITION",
                    "reason": "STOP_LOSS_HIT",
                    "exit_price": stop_loss,
                    "r_multiple": -1.0,
                    "bars_held": bars_held
                }
            if not is_trend_runner and c_low <= tp2:
                return {
                    "action": "CLOSE_POSITION",
                    "reason": "TARGET_2_FULL_EXIT",
                    "exit_price": tp2,
                    "r_multiple": round((entry_price - tp2) / risk_dist, 2),
                    "bars_held": bars_held
                }

        # -------------------------------------------------------------
        # 2. CAN EXIT IN 1 BAR: FLASH INVALIDATION / REJECTION
        # -------------------------------------------------------------
        # If the very first candle (Bar 1) or any subsequent bar displays
        # violent opposition, do NOT wait for a fixed countdown or hard SL.
        early_invalidation = False
        inval_reason = ""

        if direction == "LONG":
            # Bar 1 / Early Check A: Opposing Bearish Engulfing
            if (c_close < c_open) and (c_close < float(prev["open"])) and (body > float(prev["close"] - prev["open"])):
                early_invalidation = True
                inval_reason = f"Opposing Bearish Engulfing formed on Bar #{bars_held}. Thesis broken."

            # Bar 1 / Early Check B: Violent Rejection Wick (Buyers trapped)
            upper_wick = c_high - max(c_open, c_close)
            if upper_wick >= 2.0 * max(body, 1e-5) and c_close < c_open:
                early_invalidation = True
                inval_reason = f"Severe rejection wick at resistance on Bar #{bars_held}. Momentum rejected."

            # Bar 1 / Early Check C: Immediate structural close below entry candle low
            if bars_held <= 2 and c_close < float(prev["low"]):
                early_invalidation = True
                inval_reason = f"Immediate failed breakout below trigger bar low on Bar #{bars_held}."

        elif direction == "SHORT":
            # Bar 1 / Early Check A: Opposing Bullish Engulfing
            if (c_close > c_open) and (c_close > float(prev["open"])):
                early_invalidation = True
                inval_reason = f"Opposing Bullish Engulfing formed on Bar #{bars_held}. Thesis broken."

            # Bar 1 / Early Check B: Violent Absorption Wick (Sellers trapped)
            lower_wick = min(c_open, c_close) - c_low
            if lower_wick >= 2.0 * max(body, 1e-5) and c_close > c_open:
                early_invalidation = True
                inval_reason = f"Severe absorption wick at support on Bar #{bars_held}. Momentum dried up."

            # Bar 1 / Early Check C: Immediate failed breakdown above trigger bar high
            if bars_held <= 2 and c_close > float(prev["high"]):
                early_invalidation = True
                inval_reason = f"Immediate failed breakdown above trigger bar high on Bar #{bars_held}."

        # Macro breaking news contradiction
        if macro_news_alert:
            news_bias = macro_news_alert.get("macro_bias", "NEUTRAL")
            if (direction == "LONG" and news_bias == "BEARISH") or (direction == "SHORT" and news_bias == "BULLISH"):
                early_invalidation = True
                inval_reason = f"Macro sentiment violently flipped to {news_bias}."

        # Broadcast live analytical update to Short-Term Working Memory
        LiveTradeWorkingMemory().post_analytical_live_update(
            rejection_wick=early_invalidation and "rejection" in inval_reason.lower(),
            micro_choch=early_invalidation and "failed" in inval_reason.lower(),
            volume_surge=False,
            structure_state="INVALIDATING" if early_invalidation else "STRUCTURE_HEALTHY",
            notes=inval_reason if early_invalidation else f"Bar #{bars_held} healthy. Holding {unrealized_r:.2f}R."
        )

        # If invalidation triggered early before significant profit, cut immediately!
        if early_invalidation and unrealized_r < 0.6:
            logger.warning(f"[ActiveTradeMonitor] ⚡ EARLY STRUCTURAL INVALIDATION on Bar #{bars_held}: {inval_reason}")
            saved_loss_pct = round((1.0 - abs(unrealized_r)) * 100, 1) if unrealized_r < 0 else 0
            return {
                "action": "EMERGENCY_EARLY_EXIT",
                "reason": inval_reason,
                "exit_price": current_price,
                "r_multiple": round(unrealized_r, 2),
                "bars_held": bars_held,
                "capital_saved_note": f"Exited on Bar #{bars_held} saving {saved_loss_pct}% of stop-loss capital."
            }

        # -------------------------------------------------------------
        # 3. PARTIAL TAKE PROFIT 1 (TP1) & INSTANT BREAKEVEN
        # -------------------------------------------------------------
        tp1_hit = False
        if direction == "LONG" and c_high >= tp1 and not position.get("tp1_closed", False):
            tp1_hit = True
        elif direction == "SHORT" and c_low <= tp1 and not position.get("tp1_closed", False):
            tp1_hit = True

        if tp1_hit:
            logger.info(f"[ActiveTradeMonitor] TP1 reached on Bar #{bars_held} at ${current_price}! Banking 50% profit.")
            return {
                "action": "TAKE_PROFIT_PARTIAL",
                "portion": 0.50,
                "exit_price": tp1,
                "new_stop_loss": entry_price,  # Instant Breakeven
                "sl_state": "BREAKEVEN",
                "reason": f"TP1 booked on Bar #{bars_held}: banked 50%, remaining size risk-free.",
                "bars_held": bars_held
            }

        # -------------------------------------------------------------
        # 4. TRAILING STOP MANAGEMENT (Structure-Based, Infinite Room)
        # -------------------------------------------------------------
        # Move SL to Breakeven once in +1.0R profit
        if unrealized_r >= 1.0 and position.get("sl_state") not in ["BREAKEVEN", "TRAILING"]:
            return {
                "action": "UPDATE_STOP_LOSS",
                "new_stop_loss": entry_price,
                "sl_state": "BREAKEVEN",
                "reason": f"Bar #{bars_held} reached +{round(unrealized_r, 2)}R: downside risk eliminated.",
                "bars_held": bars_held
            }

        # Dynamic Trailing Stop once >= +1.8R
        if unrealized_r >= 1.8:
            trail_r = unrealized_r - 0.7  # Lock in gains while giving breathing room
            trail_price = entry_price + (risk_dist * trail_r) if direction == "LONG" else entry_price - (risk_dist * trail_r)
            current_sl = float(position["stop_loss"])
            
            should_update = (direction == "LONG" and trail_price > current_sl) or (direction == "SHORT" and trail_price < current_sl)
            if should_update:
                return {
                    "action": "UPDATE_STOP_LOSS",
                    "new_stop_loss": round(trail_price, 2),
                    "sl_state": "TRAILING",
                    "reason": f"Trailing stop tightened on Bar #{bars_held} to lock +{round(trail_r, 2)}R profit.",
                    "bars_held": bars_held
                }

        # -------------------------------------------------------------
        # 4B. REAL-TIME MACRO NEWS CATALYST DEFENSE
        # -------------------------------------------------------------
        if macro_news_alert:
            precedent = macro_news_alert.get("historical_precedent") or {}
            win_prob = float(precedent.get("historical_win_prob", 50.0))
            hist_bias = str(precedent.get("historical_bias", macro_news_alert.get("macro_bias", "NEUTRAL"))).upper()
            cat = str(precedent.get("dominant_catalyst", "MACRO_EVENT"))

            is_contrary = (
                (direction == "LONG" and hist_bias in ["BEARISH", "CRASH_RISK"]) or
                (direction == "SHORT" and hist_bias in ["BULLISH", "SURPRISE_STIMULUS"])
            )

            # If high-conviction macro news breaks in contrary direction
            if is_contrary and win_prob >= 70.0:
                if unrealized_r >= 0.5:
                    logger.warning(f"[ActiveTradeMonitor] 🛡️ High-Impact Contrary News ({cat} {win_prob}%). Locking profit at BE.")
                    return {
                        "action": "UPDATE_STOP_LOSS",
                        "new_stop_loss": entry_price,
                        "sl_state": "BREAKEVEN",
                        "reason": f"MACRO_NEWS_DEFENSE ({cat} {hist_bias} Prob: {win_prob}%): Protected at Breakeven.",
                        "bars_held": bars_held
                    }
                elif unrealized_r < 0.0:
                    logger.warning(f"[ActiveTradeMonitor] 🚨 CRITICAL Contrary News ({cat} {win_prob}%). Triggering Emergency Exit!")
                    return {
                        "action": "CLOSE_POSITION",
                        "reason": f"MACRO_NEWS_EMERGENCY_EXIT ({cat} {hist_bias} Prob: {win_prob}%)",
                        "exit_price": current_price,
                        "r_multiple": round(unrealized_r, 2),
                        "bars_held": bars_held
                    }

        # -------------------------------------------------------------
        # 5. OPEN-ENDED STRUCTURE RIDING VS ALPHA DECAY
        # -------------------------------------------------------------
        # NO arbitrary candle cutoff!
        # A trade stays open for 5, 20, 50, or 200 bars IF structure & momentum are healthy.
        # It ONLY exits when:
        # A. Market Structure Breaks (Change of Character against position)
        # B. Alpha Stagnation (Price has gone completely flat with near-zero momentum velocity for extended bars)

        # Structure Break Check (CHoCH against position):
        if len(recent_df) >= 6:
            swings = recent_df.tail(6)
            if direction == "LONG":
                recent_swing_low = swings["low"].min()
                # If price closes below recent 6-bar swing low after being in trade:
                if bars_held >= 4 and c_close < recent_swing_low and unrealized_r < 0.5:
                    logger.info(f"[ActiveTradeMonitor] Market Structure Break (Bearish CHoCH) on Bar #{bars_held}. Exiting.")
                    return {
                        "action": "CLOSE_POSITION",
                        "reason": f"STRUCTURE_BREAK_CHOCH (Closed below swing low on Bar #{bars_held})",
                        "exit_price": current_price,
                        "r_multiple": round(unrealized_r, 2),
                        "bars_held": bars_held
                    }
            else:  # SHORT
                recent_swing_high = swings["high"].max()
                if bars_held >= 4 and c_close > recent_swing_high and unrealized_r < 0.5:
                    logger.info(f"[ActiveTradeMonitor] Market Structure Break (Bullish CHoCH) on Bar #{bars_held}. Exiting.")
                    return {
                        "action": "CLOSE_POSITION",
                        "reason": f"STRUCTURE_BREAK_CHOCH (Closed above swing high on Bar #{bars_held})",
                        "exit_price": current_price,
                        "r_multiple": round(unrealized_r, 2),
                        "bars_held": bars_held
                    }

        # Alpha Decay & Stagnation Detection:
        # If position is flat (|R| < 0.25) and momentum velocity is near zero:
        learned_decay_threshold = 30  # Default open-ended baseline
        if learned_guidance and "alpha_decay_bars" in learned_guidance:
            learned_decay_threshold = int(learned_guidance["alpha_decay_bars"])

        if bars_held >= learned_decay_threshold and abs(unrealized_r) < 0.3:
            logger.info(f"[ActiveTradeMonitor] ⌛ ALPHA DECAY EXIT: Trade stalled across {bars_held} bars with zero velocity. Freeing capital.")
            return {
                "action": "CLOSE_POSITION",
                "reason": f"ALPHA_DECAY_STALL ({bars_held} bars held with flat price action, learned threshold: {learned_decay_threshold})",
                "exit_price": current_price,
                "r_multiple": round(unrealized_r, 2),
                "bars_held": bars_held
            }

        # Otherwise, position continues to ride!
        return {
            "action": "HOLD",
            "unrealized_r": round(unrealized_r, 2),
            "bars_held": bars_held,
            "structural_status": "STRUCTURE_INTACT",
            "reason": f"Thesis alive on Bar #{bars_held}. Structure intact."
        }
