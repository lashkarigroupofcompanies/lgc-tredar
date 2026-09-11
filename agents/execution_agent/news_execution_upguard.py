"""
News Execution UpGuard & Flash Catalyst Interceptor Engine
50-Year Master Trader Execution Engine - Real-Time Crisis Defense

Provides instant, split-second protective intervention when high-impact macro or geopolitical
news breaks during market hours:
1. Wipes out / cancels resting limit orders to prevent toxic adverse selection and fill slippage.
2. Defends active positions (moves profitable trades to Breakeven instantly, triggers emergency early exits on catastrophic contrary catalysts).
3. Alerts CEO Supreme King Agent and Risk Management Shield in real time.
"""

import logging
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger("NewsExecutionUpGuard")


class NewsExecutionUpGuard:
    """
    Real-Time UpGuard & Flash Catalyst Interceptor.
    Directly bridges News Intelligence with Execution Sniper for instant risk defense.
    """

    CRITICAL_CATALYSTS = [
        "CENTRAL_BANK_RATES",
        "GEOPOLITICAL_CONFLICT",
        "INFLATION_CPI",
        "REGULATORY_CRACKDOWN",
        "BANKING_CRISIS",
        "SOVEREIGN_DEBT",
        "ENERGY_SUPPLY_SHOCK"
    ]

    @classmethod
    def evaluate_breaking_news_threat(cls, news_alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates the severity and directional pressure of a breaking news event.
        """
        if not news_alert:
            return {
                "is_high_threat": False,
                "threat_score": 0.0,
                "threat_level": "ROUTINE",
                "directional_pressure": "NEUTRAL",
                "catalyst_category": "NONE"
            }

        macro_bias = str(news_alert.get("macro_bias", "NEUTRAL")).upper()
        precedent = news_alert.get("historical_precedent") or {}
        win_prob = float(precedent.get("historical_win_prob", 50.0))
        cat = str(precedent.get("dominant_catalyst", "ROUTINE_FLOW")).upper()
        hist_bias = str(precedent.get("historical_bias", macro_bias)).upper()

        # Assess Threat Score (0 - 100)
        threat_score = 20.0
        if macro_bias in ["BEARISH", "CRASH_RISK", "WAR_CONFLICT"]:
            threat_score += 35.0
        elif macro_bias in ["BULLISH", "SURPRISE_STIMULUS"]:
            threat_score += 25.0

        if cat in cls.CRITICAL_CATALYSTS:
            threat_score += 25.0

        if win_prob >= 75.0:
            threat_score += 20.0
        elif win_prob >= 65.0:
            threat_score += 10.0

        threat_score = min(threat_score, 100.0)

        threat_level = "ROUTINE"
        if threat_score >= 80.0:
            threat_level = "CRITICAL"
        elif threat_score >= 65.0:
            threat_level = "HIGH"
        elif threat_score >= 45.0:
            threat_level = "ELEVATED"

        is_high_threat = threat_score >= 65.0

        return {
            "is_high_threat": is_high_threat,
            "threat_score": round(threat_score, 1),
            "threat_level": threat_level,
            "directional_pressure": hist_bias if hist_bias != "NEUTRAL" else macro_bias,
            "catalyst_category": cat,
            "historical_win_prob": win_prob
        }

    @classmethod
    def determine_defensive_actions(
        cls,
        threat_assessment: Dict[str, Any],
        open_positions: List[Dict[str, Any]],
        has_pending_orders: bool = False
    ) -> Dict[str, Any]:
        """
        Determines concrete real-time defensive execution actions based on news threat:
        - Cancel resting limit orders to prevent getting filled into a falling knife.
        - Tighten profitable positions to Breakeven.
        - Emergency early exit for contrary positions during critical catalysts.
        """
        is_threat = threat_assessment.get("is_high_threat", False)
        threat_level = threat_assessment.get("threat_level", "ROUTINE")
        dir_pressure = threat_assessment.get("directional_pressure", "NEUTRAL")
        cat = threat_assessment.get("catalyst_category", "NONE")

        actions_taken: List[str] = []
        position_actions: Dict[str, Dict[str, Any]] = {}
        cancel_pending = False

        # Rule 1: Flash News Wipes Pending Limit Orders
        if is_threat and has_pending_orders:
            cancel_pending = True
            actions_taken.append("CANCEL_ALL_PENDING_ORDERS")
            logger.warning(
                f"[NewsUpGuard] 🚨 HIGH THREAT CATALYST ({cat} | {threat_level})! "
                "Triggering immediate cancellation of all resting limit orders."
            )

        # Rule 2: Evaluate Open Positions Against News Catalyst
        for pos in open_positions:
            pos_id = str(pos.get("trade_id") or pos.get("symbol") or "UNKNOWN")
            symbol_str = str(pos.get("symbol") or "UNKNOWN")
            pos_dir = str(pos.get("direction", "LONG")).upper()
            unrealized_r = float(pos.get("unrealized_r") or 0.0)
            current_sl = float(pos.get("stop_loss") or 0.0)
            entry_p = float(pos.get("entry_price") or 0.0)

            is_contrary = (
                (pos_dir == "LONG" and dir_pressure in ["BEARISH", "CRASH_RISK"]) or
                (pos_dir == "SHORT" and dir_pressure in ["BULLISH", "SURPRISE_STIMULUS"])
            )

            if is_threat and is_contrary:
                # If trade is well in profit, lock Breakeven so normal wicks don't cut winning position
                if unrealized_r >= 0.3:
                    position_actions[pos_id] = {
                        "action": "TIGHTEN_STOP_LOSS_TO_BREAKEVEN",
                        "new_stop_loss": entry_p,
                        "reason": f"News UpGuard: Contrary macro catalyst ({cat}). Moving SL to Breakeven to lock zero-risk."
                    }
                    actions_taken.append(f"TIGHTEN_BE_{symbol_str}")
                # If news is CRITICAL or HIGH threat and trade is flat or in loss, execute emergency exit before slippage widens
                elif threat_level in ["CRITICAL", "HIGH"]:
                    position_actions[pos_id] = {
                        "action": "EMERGENCY_EARLY_EXIT",
                        "reason": f"News UpGuard: {threat_level} contrary catalyst ({cat}). Emergency exit to prevent black-swan slippage."
                    }
                    actions_taken.append(f"EMERGENCY_EXIT_{symbol_str}")
                else:
                    position_actions[pos_id] = {
                        "action": "DEFENSIVE_HOLD_TIGHTEN",
                        "reason": f"News UpGuard: Monitoring contrary news pressure ({cat})."
                    }

        interception_active = len(actions_taken) > 0

        return {
            "interception_active": interception_active,
            "threat_assessment": threat_assessment,
            "cancel_pending_orders": cancel_pending,
            "position_actions": position_actions,
            "actions_summary": actions_taken,
            "ceo_alert_priority": "CRITICAL" if threat_level == "CRITICAL" else ("HIGH" if is_threat else "NORMAL"),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
