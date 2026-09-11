"""
Strategy Selection Matrix (Section 14 Framework)
Dynamically matches current market conditions to the optimal quantitative strategy family.
Prevents using trend strategies in chop or mean reversion in parabolic trends.
"""

from typing import Dict, Any, List


class StrategySelectionMatrix:
    """
    Institutional strategy selection router mapping current market regime
    to high-expectancy algorithmic models.
    """

    MATRIX_RULES = {
        "STRONG_UPTREND": {
            "regime_description": "Clear higher highs/lows with ADX > 25 above 200 EMA",
            "recommended_strategies": [
                "DUAL_EMA_TREND",
                "SUPERTREND_MOMENTUM",
                "PULLBACK_EMA_BOUNCE",
                "ICT_2022_MODEL",
                "ORDER_BLOCK_GOLDEN_POCKET"
            ],
            "action_bias": "BUY_PULLBACKS_ONLY",
            "risk_multiplier": 1.0
        },
        "STRONG_DOWNTREND": {
            "regime_description": "Clear lower highs/lows with ADX > 25 below 200 EMA",
            "recommended_strategies": [
                "DUAL_EMA_TREND",
                "BREAKER_BLOCK_FLIP",
                "TURTLE_DONCHIAN_BREAKOUT",
                "ICT_2022_MODEL"
            ],
            "action_bias": "SELL_RALLIES_ONLY",
            "risk_multiplier": 1.0
        },
        "RANGING_CONSOLIDATION": {
            "regime_description": "Price bounded between S&R levels with ADX < 20",
            "recommended_strategies": [
                "BOLLINGER_RSI_MEAN_REVERSION",
                "VWAP_MEAN_REVERSION",
                "STOCHASTIC_RSI_SWING",
                "VOLUME_PROFILE_POC_RETEST"
            ],
            "action_bias": "FADE_EXTREMES",
            "risk_multiplier": 0.8
        },
        "VOLATILITY_SQUEEZE": {
            "regime_description": "Bollinger Bands contracting inside Keltner Channel (Pre-Breakout)",
            "recommended_strategies": [
                "DARVAS_BOX_BREAKOUT",
                "OPENING_RANGE_BREAKOUT",
                "KELTNER_CHANNEL_BREAKOUT",
                "RVOL_SURGE_MOMENTUM"
            ],
            "action_bias": "PREPARE_BREAKOUT_DIRECTION",
            "risk_multiplier": 1.0
        },
        "INSTITUTIONAL_KILLZONE": {
            "regime_description": "Active London Open (07:00-10:00 UTC) or NY Open (12:00-15:00 UTC)",
            "recommended_strategies": [
                "ICT_SILVER_BULLET",
                "ICT_2022_MODEL",
                "TURTLE_SOUP_SWEEP",
                "BREAKER_BLOCK_FLIP"
            ],
            "action_bias": "TRADE_SMART_MONEY_LIQUIDITY",
            "risk_multiplier": 1.0
        },
        "CHOPPY_ERRATIC": {
            "regime_description": "Low volume, irregular whipsaws with no structure",
            "recommended_strategies": [],
            "action_bias": "STAY_IN_CASH",
            "risk_multiplier": 0.0
        }
    }

    @classmethod
    def determine_regime_and_strategies(
        cls,
        market_structure: str,
        adx_value: float,
        is_killzone: bool,
        is_squeeze: bool,
        volatility_state: str
    ) -> Dict[str, Any]:
        """
        Evaluates technical regime and outputs strategy shortlist.
        """
        struct_upper = market_structure.upper()
        if is_killzone:
            regime = "INSTITUTIONAL_KILLZONE"
        elif is_squeeze:
            regime = "VOLATILITY_SQUEEZE"
        elif any(k in struct_upper for k in ["UPTREND", "BULLISH", "MARKUP"]) and adx_value >= 18.0:
            regime = "STRONG_UPTREND"
        elif any(k in struct_upper for k in ["DOWNTREND", "BEARISH", "MARKDOWN"]) and adx_value >= 18.0:
            regime = "STRONG_DOWNTREND"
        elif any(k in struct_upper for k in ["RANGE", "CONSOLIDATION", "NEUTRAL"]) or adx_value < 22.0:
            regime = "RANGING_CONSOLIDATION"
        elif "TRENDING" in struct_upper:
            regime = "STRONG_UPTREND" if adx_value >= 20.0 else "RANGING_CONSOLIDATION"
        else:
            regime = "RANGING_CONSOLIDATION"

        config = cls.MATRIX_RULES.get(regime, cls.MATRIX_RULES["RANGING_CONSOLIDATION"])

        return {
            "regime": regime,
            "description": config["regime_description"],
            "action_bias": config["action_bias"],
            "risk_multiplier": config["risk_multiplier"],
            "eligible_strategies": config["recommended_strategies"]
        }
