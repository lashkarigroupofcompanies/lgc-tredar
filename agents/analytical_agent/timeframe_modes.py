"""
Multi-Timeframe Trading Modes & Horizon Engines
Provides distinct technical evaluations for:
1. SCALP (1m - 5m Intraday momentum)
2. SWING (15m - 4h Key level reversals)
3. POSITIONAL (1d - 1w Trend following & Golden Cross)
4. OPTIONS_REGIME (Volatility squeeze, Gamma moves)
"""

from typing import Dict, Any


class TimeframeModeSelector:
    """
    Tailors strategy rules based on selected trading style.
    """

    MODES = {
        "INTRADAY_SCALP": {
            "default_timeframe": "5m",
            "fast_ema": 9,
            "slow_ema": 21,
            "target_rr": 1.5,
            "description": "High-velocity momentum scalping targeting EMA crossovers and volume bursts."
        },
        "SWING_TRADING": {
            "default_timeframe": "1h",
            "fast_ema": 21,
            "slow_ema": 50,
            "target_rr": 2.5,
            "description": "Institutional swing trading targeting Order Blocks, FVGs, and Liquidity Sweeps."
        },
        "POSITIONAL_INVESTING": {
            "default_timeframe": "1d",
            "fast_ema": 50,
            "slow_ema": 200,
            "target_rr": 3.5,
            "description": "Macro trend riding targeting 200-day EMA bounces and Golden/Death crosses."
        },
        "OPTIONS_TRADING": {
            "default_timeframe": "15m",
            "volatility_target": "ATR_EXPANSION",
            "target_rr": 2.0,
            "description": "Options directional delta plays on Bollinger squeeze breakouts."
        }
    }

    @classmethod
    def evaluate_mode_alignment(cls, mode: str, indicators: Dict[str, Any], smc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determines trade setup validity for the given mode.
        """
        config = cls.MODES.get(mode.upper(), cls.MODES["SWING_TRADING"])
        ind_bias = indicators.get("indicator_bias", "NEUTRAL")
        smc_bias = smc.get("smc_bias", "NEUTRAL")

        # Confluence check between Traditional Indicators & Institutional SMC
        confluence = "NEUTRAL"
        confidence = 0.50

        if "BUY" in ind_bias and ("BULLISH" in smc_bias or "STRONG" in smc_bias):
            confluence = "HIGH_PROBABILITY_LONG"
            confidence = 0.88
        elif "SELL" in ind_bias and ("BEARISH" in smc_bias or "STRONG" in smc_bias):
            confluence = "HIGH_PROBABILITY_SHORT"
            confidence = 0.88
        elif "BUY" in ind_bias or "BULLISH" in smc_bias:
            confluence = "MODERATE_BULLISH"
            confidence = 0.68
        elif "SELL" in ind_bias or "BEARISH" in smc_bias:
            confluence = "MODERATE_BEARISH"
            confidence = 0.68

        return {
            "trading_mode": mode.upper(),
            "timeframe_used": config["default_timeframe"],
            "setup_confluence": confluence,
            "confidence_score": confidence,
            "target_risk_reward": config["target_rr"],
            "strategy_style": config["description"]
        }
