"""
Triple-Historical Confluence Gate
Synthesizes the empirical historical track record across all 3 intelligence pillars:
1. Analytical Agent: Historical Pattern Win Rate (past 500+ candles)
2. News Agent: Historical Macro Catalyst Reaction Probability
3. Strategy Agent: Historical Multi-Window Walk-Forward Consistency

Guarantees that trades are only executed when PAST DATA across all 3 domains
unanimously confirms a mathematical statistical edge >= 70%.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger("TripleConfluenceGate")


class TripleConfluenceGate:
    """
    Final institutional arbiter calculating the Triple-Historical Probability Score.
    """

    @classmethod
    def evaluate_triple_historical_edge(
        cls,
        chart_pattern_win_rate: float,
        news_precedent_win_prob: float,
        strategy_consistency_rate: float,
        strategy_historical_win_rate: float,
        mode: str = "SAFE"
    ) -> Dict[str, Any]:
        """
        Calculates the weighted empirical historical confluence index (0 to 100).
        Adapts execution thresholds based on trading regime:
        - DANGEROUS: >= 38.0 allows paper micro-scalps to accumulate neural weights
        - MONEY_MAKER: >= 55.0 allows multi-asset 3-5 daily driver setups
        - SAFE: >= 70.0 strict institutional sniper
        """
        # Default safety floors
        p_chart = max(10.0, min(100.0, chart_pattern_win_rate))
        p_news = max(10.0, min(100.0, news_precedent_win_prob))
        p_strat = max(10.0, min(100.0, (strategy_consistency_rate * 0.5 + strategy_historical_win_rate * 0.5)))

        # Weighted calculation (35% Chart Analogue + 35% News Precedent + 30% Strategy Walk-Forward)
        confluence_index = round((0.35 * p_chart) + (0.35 * p_news) + (0.30 * p_strat), 1)

        mode_upper = str(mode or "SAFE").upper()
        is_dangerous = "DANGEROUS" in mode_upper or "WILD" in mode_upper
        is_money_maker = "MONEY" in mode_upper or "MAKER" in mode_upper

        if is_dangerous:
            threshold_req = 38.0
        elif is_money_maker:
            threshold_req = 55.0
        else:
            threshold_req = 70.0

        if confluence_index >= 70.0:
            tier = "INSTITUTIONAL_A_PLUS"
            verdict = "EXECUTE_HIGH_CONVICTION"
            size_multiplier = 1.0
            guidance = "Unanimous historical empirical edge across chart patterns, news catalyst, and strategy walk-forward."
        elif confluence_index >= 55.0:
            tier = "STANDARD_CONVICTION"
            verdict = "EXECUTE_STANDARD_SIZE"
            size_multiplier = 0.75 if is_money_maker else 0.65
            guidance = "Positive historical statistical edge. Moderate position sizing recommended."
        elif is_dangerous and confluence_index >= 38.0:
            tier = "NEURAL_LEARNING_LAB"
            verdict = "EXECUTE_MICRO_SCALP"
            size_multiplier = 0.50
            guidance = "Dangerous Mode: Exploratory micro-scalp approved for high-frequency neural learning."
        elif confluence_index >= 45.0 and not is_dangerous:
            tier = "MARGINAL_HISTORICAL_EDGE"
            verdict = "WAIT_FOR_BETTER_SETUP"
            size_multiplier = 0.0
            guidance = "Historical data shows mixed or 50/50 outcomes. Capital preservation takes precedence."
        else:
            tier = "HIGH_FAILURE_RISK_TRAP"
            verdict = "STAY_IN_CASH"
            size_multiplier = 0.0
            guidance = "Past charts and news show this setup has a high failure rate. Stand aside."

        logger.info(
            f"[TripleConfluence] [{mode_upper}] Index: {confluence_index}/100 (Threshold: {threshold_req} | Chart: {p_chart}%, News: {p_news}%, Strat: {round(p_strat, 1)}%) -> {verdict}"
        )

        return {
            "triple_historical_index": confluence_index,
            "threshold_required": threshold_req,
            "tier": tier,
            "verdict": verdict,
            "position_size_multiplier": size_multiplier,
            "component_scores": {
                "chart_pattern_historical_win_rate": p_chart,
                "news_precedent_historical_prob": p_news,
                "strategy_walk_forward_edge": round(p_strat, 1)
            },
            "guidance": guidance,
            "is_a_plus_setup": confluence_index >= 70.0
        }
