"""
Position Sizing Engine - Section 2 & 10 of Institutional Risk Management Knowledge Base
Implements mathematical sizing models inspired by QuantConnect/Lean, Ralph Vince, and Van Tharp:
- Fixed % Risk per trade (0.5% Conservative, 1.0% Standard, 1.5-2.0% Aggressive)
- ATR-based Volatility Sizing (inversely proportional to ATR velocity)
- Kelly Criterion (Full Kelly, Half-Kelly, Quarter-Kelly)
- Optimal f (Ralph Vince) & Fixed Ratio (Ryan Jones)
- Anti-Martingale scaling (scale up on winning streaks, scale down on drawdowns)
- Volatility Parity & Cash Margin constraints
"""

import math
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("PositionSizingEngine")


class PositionSizingEngine:
    """
    Institutional Position Sizing Engine.
    Position sizing > entry timing in long-term compounding success.
    """

    @classmethod
    def calculate_fixed_fractional_size(
        cls,
        capital: float,
        risk_pct: float,
        entry_price: float,
        stop_loss: float
    ) -> Dict[str, Any]:
        """
        Fixed % Risk Per Trade (Standard institutional method).
        Formula: Position Size = (Capital * Risk%) / (Entry - SL)
        """
        if capital <= 0 or entry_price <= 0:
            return {"units": 0.0, "dollar_risk": 0.0, "error": "Invalid capital or entry price"}

        sl_distance = abs(entry_price - stop_loss)
        if sl_distance <= 0:
            return {"units": 0.0, "dollar_risk": 0.0, "error": "Stop loss equals entry price"}

        dollar_risk = capital * (risk_pct / 100.0)
        units = dollar_risk / sl_distance
        position_value = units * entry_price

        return {
            "method": "FIXED_PERCENT_RISK",
            "risk_pct": risk_pct,
            "dollar_risk": round(dollar_risk, 2),
            "units": round(units, 4),
            "position_value": round(position_value, 2),
            "sl_distance": round(sl_distance, 4),
            "sl_pct": round((sl_distance / entry_price) * 100.0, 2)
        }

    @classmethod
    def calculate_atr_volatility_size(
        cls,
        capital: float,
        risk_pct: float,
        entry_price: float,
        atr_value: float,
        atr_multiplier: float = 2.0
    ) -> Dict[str, Any]:
        """
        Volatility-Based Sizing:
        Position size inversely proportional to ATR.
        High volatility = smaller position; Low volatility = larger position.
        Formula: Size = (Capital * Risk%) / (ATR * Multiplier)
        """
        if atr_value <= 0 or entry_price <= 0:
            return cls.calculate_fixed_fractional_size(capital, risk_pct, entry_price, entry_price * 0.98)

        effective_risk_dist = atr_value * atr_multiplier
        dollar_risk = capital * (risk_pct / 100.0)
        units = dollar_risk / effective_risk_dist
        position_value = units * entry_price

        return {
            "method": "ATR_VOLATILITY_SIZING",
            "atr_value": round(atr_value, 4),
            "atr_multiplier": atr_multiplier,
            "effective_risk_dist": round(effective_risk_dist, 4),
            "dollar_risk": round(dollar_risk, 2),
            "units": round(units, 4),
            "position_value": round(position_value, 2)
        }

    @classmethod
    def calculate_kelly_criterion(
        cls,
        capital: float,
        win_rate: float,       # 0.0 to 1.0 (e.g. 0.55 for 55%)
        avg_win_r: float,      # Average R multiple on wins (e.g. 2.2)
        avg_loss_r: float = 1.0, # Average R multiple on losses (usually 1.0)
        fraction_type: str = "HALF_KELLY" # FULL_KELLY, HALF_KELLY, QUARTER_KELLY
    ) -> Dict[str, Any]:
        """
        Kelly Criterion: Mathematically optimal bet size for geometric growth.
        f* = (b*p - q) / b
        b = avg_win / avg_loss (odds)
        p = win probability
        q = 1 - p (loss probability)
        Note: Full Kelly has massive drawdown swings; institutional desks use Half-Kelly or Quarter-Kelly.
        """
        if win_rate <= 0 or avg_loss_r <= 0:
            return {"kelly_pct": 0.0, "recommended_risk_pct": 0.5, "warning": "Negative edge"}

        p = min(0.95, max(0.05, win_rate))
        q = 1.0 - p
        b = max(0.1, avg_win_r / avg_loss_r)

        full_kelly = (b * p - q) / b

        if full_kelly <= 0:
            return {
                "kelly_pct": 0.0,
                "recommended_risk_pct": 0.0,
                "verdict": "NEGATIVE_EDGE_NO_TRADE",
                "full_kelly": round(full_kelly, 4)
            }

        if fraction_type == "HALF_KELLY":
            applied_kelly = full_kelly * 0.5
        elif fraction_type == "QUARTER_KELLY":
            applied_kelly = full_kelly * 0.25
        else:
            applied_kelly = full_kelly

        # Clamp between 0.25% and 5.0% max risk per trade for institutional flexibility
        clamped_risk_pct = max(0.25, min(5.0, applied_kelly * 100.0))

        return {
            "method": "KELLY_CRITERION",
            "fraction_type": fraction_type,
            "full_kelly_pct": round(full_kelly * 100.0, 2),
            "applied_kelly_pct": round(applied_kelly * 100.0, 2),
            "recommended_risk_pct": round(clamped_risk_pct, 2),
            "win_rate": round(p * 100.0, 1),
            "win_loss_ratio": round(b, 2)
        }

    @classmethod
    def calculate_dynamic_edge_risk_pct(
        cls,
        win_rate: float,
        rr_ratio: float,
        triple_index: float,
        setup_score: float,
        min_risk_pct: float = 0.25,
        max_risk_pct: float = 5.0
    ) -> Dict[str, Any]:
        """
        Calculates mathematically dynamic risk percentage according to empirical edge,
        win rate, and confluence. Completely eliminates arbitrary hardcoded risk caps.
        High edge + high win rate = higher conviction sizing (up to 3-5%).
        Thin edge = lower risk (0.25 - 0.75%).
        Negative expectancy = 0.0% (REJECT).
        """
        p = min(0.95, max(0.05, win_rate))
        q = 1.0 - p
        b = max(0.2, rr_ratio)

        # 1. Classical Kelly Criterion Fraction
        full_kelly = (b * p - q) / b

        if full_kelly <= 0:
            return {
                "dynamic_risk_pct": 0.0,
                "verdict": "NEGATIVE_EDGE_REJECT",
                "reason": f"Negative mathematical expectancy: p={p:.2f}, R:R={b:.2f}, Kelly={full_kelly:.3f}"
            }

        # 2. Confluence Factor (0.0 to 1.0)
        norm_triple = min(1.0, max(0.0, triple_index / 100.0))
        norm_setup = min(1.0, max(0.0, setup_score / 10.0))
        confluence_factor = (norm_triple * 0.6) + (norm_setup * 0.4)

        # 3. Dynamic Base Sizing from Fractional Kelly & Edge
        raw_risk = (full_kelly * 0.12) * confluence_factor * 100.0

        # Dynamic scaling based on edge & win rate
        if p >= 0.68 and confluence_factor >= 0.75:
            # High conviction tier: scales up to 3.0% - 5.0%
            scaled_risk = max(2.5, min(max_risk_pct, raw_risk * 1.5))
            tier = "GRADE_A_PLUS_CONVICTION"
        elif p >= 0.58 and confluence_factor >= 0.60:
            # Strong institutional tier: 1.5% to 2.5%
            scaled_risk = max(1.25, min(3.0, raw_risk * 1.2))
            tier = "GRADE_A_STANDARD_EDGE"
        elif p >= 0.48:
            # Moderate edge tier: 0.75% to 1.5%
            scaled_risk = max(0.75, min(1.5, raw_risk))
            tier = "GRADE_B_MODERATE_EDGE"
        else:
            # Cautious edge tier: 0.25% to 0.75%
            scaled_risk = max(min_risk_pct, min(0.75, raw_risk * 0.8))
            tier = "GRADE_C_CAUTIOUS_EXPLORATORY"

        final_risk = round(max(min_risk_pct, min(max_risk_pct, scaled_risk)), 2)

        return {
            "dynamic_risk_pct": final_risk,
            "tier": tier,
            "full_kelly": round(full_kelly * 100.0, 2),
            "confluence_factor": round(confluence_factor, 2),
            "win_rate_pct": round(p * 100.0, 1),
            "rr_ratio": round(b, 2),
            "verdict": "DYNAMIC_SIZING_APPROVED"
        }

    @classmethod
    def apply_anti_martingale_streak_scaling(
        cls,
        base_risk_pct: float,
        consecutive_wins: int = 0,
        consecutive_losses: int = 0,
        current_drawdown_pct: float = 0.0
    ) -> Dict[str, Any]:
        """
        Section 2 & 6 Anti-Martingale Scaling:
        - Never Martingale (never double down on losses).
        - Scale down aggressively during drawdowns / losing streaks.
        - Scale up moderately during winning streaks only when near equity highs.
        """
        multiplier = 1.0
        reason = "NORMAL_SIZING"

        # Losing streak throttling (Section 6)
        if consecutive_losses >= 5:
            multiplier = 0.50  # 5 consecutive losses -> reduce size 50%
            reason = f"THROTTLED_50PCT ({consecutive_losses} consecutive losses)"
        elif consecutive_losses >= 3:
            multiplier = 0.75  # 3 consecutive losses -> reduce size 25%
            reason = f"THROTTLED_25PCT ({consecutive_losses} consecutive losses)"

        # Drawdown throttling
        if current_drawdown_pct >= 15.0:
            multiplier = min(multiplier, 0.25)
            reason = f"SEVERE_DRAWDOWN_LOCK ({round(current_drawdown_pct, 1)}% DD)"
        elif current_drawdown_pct >= 10.0:
            multiplier = min(multiplier, 0.50)
            reason = f"DRAWDOWN_REDUCTION_50PCT ({round(current_drawdown_pct, 1)}% DD)"

        # Winning streak bonus (Anti-Martingale) - only if no drawdown
        if consecutive_wins >= 3 and current_drawdown_pct < 2.0:
            multiplier = min(1.35, multiplier * 1.20)
            reason = f"WIN_STREAK_MOMENTUM_BOOST (+20% size on {consecutive_wins} wins)"

        final_risk_pct = round(base_risk_pct * multiplier, 2)

        return {
            "base_risk_pct": base_risk_pct,
            "final_risk_pct": max(0.25, min(2.5, final_risk_pct)),
            "multiplier": round(multiplier, 2),
            "reason": reason,
            "consecutive_wins": consecutive_wins,
            "consecutive_losses": consecutive_losses,
            "drawdown_pct": round(current_drawdown_pct, 2)
        }

    @classmethod
    def calculate_adaptive_wild_mode_clamp(
        cls,
        current_candle_tr: float = 0.0,
        baseline_atr: float = 0.0,
        historical_wild_win_rate: float = 50.0,
        historical_wild_sample: int = 0,
        consecutive_wins: int = 0,
        consecutive_losses: int = 0
    ) -> Dict[str, Any]:
        """
        Calculates an adaptive, learning-driven risk clamp for Wild Mode (High Volatility / Expansion).
        Replaces arbitrary static caps with an organic formula based on:
        1. Volatility Expansion Velocity Ratio (TR / Baseline ATR)
        2. Evolution Memory historical win rate in Wild Mode over time
        3. Real-time winning / losing streaks (Anti-Martingale)
        """
        # 1. Expansion Velocity Ratio
        if baseline_atr > 0 and current_candle_tr > 0:
            expansion_ratio = round(current_candle_tr / baseline_atr, 2)
        else:
            expansion_ratio = 2.0  # standard baseline assumption

        # Base clamp from expansion velocity
        if expansion_ratio <= 1.8:
            base_clamp = 1.00  # Healthy expansion, moderate risk
        elif expansion_ratio <= 2.5:
            base_clamp = 0.85  # Standard breakout expansion
        elif expansion_ratio <= 3.5:
            base_clamp = 0.70  # Elevated volatility, clamp tighter
        else:
            base_clamp = 0.50  # Extreme 4x+ volatility shock / tail risk

        # 2. Over-Time Learning Factor from Evolution Memory
        learn_adj = 0.0
        if historical_wild_sample >= 3:
            if historical_wild_win_rate >= 65.0:
                learn_adj = +0.15  # System excels in wild regimes: allow slightly more size
            elif historical_wild_win_rate >= 55.0:
                learn_adj = +0.05
            elif historical_wild_win_rate < 40.0:
                learn_adj = -0.15  # Poor historical edge: protect capital
            elif historical_wild_win_rate < 48.0:
                learn_adj = -0.08

        # 3. Streak / Drawdown Momentum Factor
        streak_adj = 0.0
        if consecutive_wins >= 2:
            streak_adj = +0.05
        elif consecutive_losses >= 2:
            streak_adj = -0.10

        raw_clamp = base_clamp + learn_adj + streak_adj
        final_clamp = round(max(0.30, min(1.25, raw_clamp)), 2)

        reason = (
            f"Expansion: {expansion_ratio}x (Base {base_clamp}%) | "
            f"Learned Win Rate: {historical_wild_win_rate:.1f}% ({historical_wild_sample} samples, Adj {learn_adj:+.2f}%) | "
            f"Streak: +{consecutive_wins}/-{consecutive_losses} (Adj {streak_adj:+.2f}%)"
        )

        return {
            "adaptive_clamp_pct": final_clamp,
            "base_clamp_pct": base_clamp,
            "expansion_ratio": expansion_ratio,
            "learned_win_rate_pct": historical_wild_win_rate,
            "learned_sample_size": historical_wild_sample,
            "learning_adjustment": learn_adj,
            "streak_adjustment": streak_adj,
            "reason": reason
        }
