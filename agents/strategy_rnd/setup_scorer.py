"""
Trade Setup Scoring System (Section 16 Institutional Quantitative Matrix)
Scores any candidate trade setup strictly out of 10 points:
- HTF Trend Alignment: 0-2 pts
- Key Level Quality (S&R/Demand/Supply/OB): 0-2 pts
- Chart Pattern Clarity: 0-1 pt
- Indicator Confluence: 0-1 pt
- Candlestick Confirmation: 0-1 pt
- Risk-to-Reward Ratio (min 1:2): 0-1 pt
- Session / Killzone Timing: 0-1 pt
- Volume Confirmation (RVOL > 1.2): 0-1 pt

Threshold Rules:
Score >= 7: A+ Setup -> Take Trade
Score 5-6: Wait for more confirmation
Score < 5: Skip (Preserve Capital)
"""

from typing import Dict, Any


class TradeSetupScorer:
    """
    Objective 10-point scoring engine enforcing institutional discipline
    and filtering out low-conviction or emotional setups.
    """

    @staticmethod
    def score_setup(
        trend_aligned: bool,
        trend_strength: str = "STRONG",  # STRONG, MODERATE, WEAK
        at_key_level: bool = False,
        level_type: str = "MAJOR",        # MAJOR, MINOR, NONE
        has_chart_pattern: bool = False,
        has_indicator_confluence: bool = False,
        has_candlestick_confirm: bool = False,
        risk_reward_ratio: float = 2.0,
        in_killzone_session: bool = False,
        has_volume_confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates setup score out of 10 points with granular point breakdown.
        """
        breakdown = {}
        total_score = 0.0

        # 1. Trend Alignment (0 - 2 pts)
        if trend_aligned:
            if trend_strength == "STRONG":
                trend_pts = 2.0
            elif trend_strength == "MODERATE":
                trend_pts = 1.5
            else:
                trend_pts = 1.0
        else:
            trend_pts = 0.0
        breakdown["trend_alignment_pts"] = trend_pts
        total_score += trend_pts

        # 2. Key Level Quality (0 - 2 pts)
        if at_key_level:
            if level_type == "MAJOR":
                level_pts = 2.0
            elif level_type == "MODERATE":
                level_pts = 1.5
            else:
                level_pts = 1.0
        else:
            level_pts = 0.0
        breakdown["key_level_pts"] = level_pts
        total_score += level_pts

        # 3. Chart Pattern Clarity (0 - 1 pt)
        pattern_pts = 1.0 if has_chart_pattern else 0.0
        breakdown["chart_pattern_pts"] = pattern_pts
        total_score += pattern_pts

        # 4. Indicator Confluence (0 - 1 pt)
        indicator_pts = 1.0 if has_indicator_confluence else 0.0
        breakdown["indicator_confluence_pts"] = indicator_pts
        total_score += indicator_pts

        # 5. Candlestick Confirmation (0 - 1 pt)
        candle_pts = 1.0 if has_candlestick_confirm else 0.0
        breakdown["candlestick_confirm_pts"] = candle_pts
        total_score += candle_pts

        # 6. Risk-to-Reward Ratio (min 1:2) (0 - 1 pt)
        if risk_reward_ratio >= 2.0:
            rr_pts = 1.0
        elif risk_reward_ratio >= 1.5:
            rr_pts = 0.5
        else:
            rr_pts = 0.0
        breakdown["risk_reward_pts"] = rr_pts
        total_score += rr_pts

        # 7. Session Timing / Killzone (0 - 1 pt)
        session_pts = 1.0 if in_killzone_session else 0.0
        breakdown["session_timing_pts"] = session_pts
        total_score += session_pts

        # 8. Volume Confirmation (0 - 1 pt)
        vol_pts = 1.0 if has_volume_confirm else 0.0
        breakdown["volume_confirm_pts"] = vol_pts
        total_score += vol_pts

        # Final Verdict & Tier
        total_score = round(total_score, 1)
        if total_score >= 7.0:
            verdict = "TAKE_TRADE_A_PLUS"
            recommendation = "A+ Institutional Grade Setup. High statistical probability. Execute with full confidence."
        elif total_score >= 5.0:
            verdict = "WAIT_FOR_CONFIRMATION"
            recommendation = "Setup developing (Score 5-6). Awaiting additional confluence before committing risk."
        else:
            verdict = "SKIP_SETUP"
            recommendation = "Low edge setup (Score < 5). Sitting in cash is a valid, capital-preserving position."

        return {
            "total_score": total_score,
            "max_score": 10.0,
            "score_percentage": round((total_score / 10.0) * 100, 1),
            "verdict": verdict,
            "recommendation": recommendation,
            "breakdown": breakdown
        }
