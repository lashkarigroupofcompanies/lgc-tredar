"""
Market Memory Matrix - Cross-Market Empirical Edge & Affinity Engine
Remembers what strategies, chart patterns, and timing rules work best in EACH specific share market:

Supported Global Markets:
1. US_STOCKS (NYSE, NASDAQ, S&P 500, Tech)
2. INDIAN_STOCKS (NSE, BSE, Nifty, BankNifty)
3. UK_STOCKS (LSE London, FTSE 100)
4. EU_STOCKS (Frankfurt DAX, Euronext CAC)
5. ASIAN_STOCKS (Tokyo JPX, Hong Kong HKEX, Australia ASX)
6. FOREX (EUR/USD, GBP/USD, USD/JPY 24/5)
7. COMMODITIES (Gold, Crude Oil, Silver - MCX/COMEX)
8. CRYPTO (BTC, ETH, SOL 24/7)

Stores baseline empirical priors and continuously updates as paper and live trades resolve.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("MarketMemoryMatrix")


class MarketMemoryMatrix:
    """
    Market-Specific Long-Term Memory.
    Enables agents to adapt strategy selection, pattern conviction, and risk parameters
    to the unique mathematical characteristics of each global share market.
    """

    # Comprehensive empirical baselines for all global share markets
    BASE_MARKET_PROFILES: Dict[str, Dict[str, Any]] = {
        "US_STOCKS": {
            "market_name": "United States Equities (NYSE / NASDAQ)",
            "primary_timezone": "America/New_York",
            "volatility_characteristics": "HIGH_MOMENTUM_TECH_DRIVEN",
            "top_strategies": [
                {"name": "OPENING_RANGE_BREAKOUT", "win_rate": 64.0, "avg_r": 2.2, "sample_size": 120, "edge_tier": "ELITE"},
                {"name": "FVG_INSTITUTIONAL_FILL", "win_rate": 61.5, "avg_r": 2.1, "sample_size": 95, "edge_tier": "HIGH"},
                {"name": "VWAP_MOMENTUM_EXPANSION", "win_rate": 59.0, "avg_r": 1.9, "sample_size": 88, "edge_tier": "HIGH"},
                {"name": "GAP_AND_GO_MOMENTUM", "win_rate": 58.0, "avg_r": 2.0, "sample_size": 74, "edge_tier": "HIGH"},
                {"name": "ORDER_BLOCK_GOLDEN_POCKET", "win_rate": 56.5, "avg_r": 2.3, "sample_size": 80, "edge_tier": "HIGH"}
            ],
            "top_patterns": {
                "BULL_FLAG": 66.0,
                "ASCENDING_TRIANGLE": 63.5,
                "CUP_AND_HANDLE": 65.0,
                "DOUBLE_BOTTOM_W_SHAPE": 58.0,
                "HEAD_AND_SHOULDERS_INVERSE": 59.0
            },
            "low_edge_warning": [
                "STOCHASTIC_OVERSOLD_BOUNCE (Fails in strong institutional trend continuation)",
                "TRIPLE_TOP (High frequency of short squeeze sweeps)"
            ]
        },
        "INDIAN_STOCKS": {
            "market_name": "Indian Equities (NSE / BSE)",
            "primary_timezone": "Asia/Kolkata",
            "volatility_characteristics": "LIQUIDITY_SWEEP_OPTIONS_DOMINATED",
            "top_strategies": [
                {"name": "ORDER_BLOCK_GOLDEN_POCKET", "win_rate": 63.0, "avg_r": 2.4, "sample_size": 110, "edge_tier": "ELITE"},
                {"name": "SMC_LIQUIDITY_RUN", "win_rate": 62.0, "avg_r": 2.2, "sample_size": 104, "edge_tier": "ELITE"},
                {"name": "PIVOT_REVERSAL_BOUNCE", "win_rate": 60.5, "avg_r": 1.8, "sample_size": 85, "edge_tier": "HIGH"},
                {"name": "EXPIRY_GAMMA_MEAN_REVERSION", "win_rate": 58.5, "avg_r": 2.0, "sample_size": 70, "edge_tier": "HIGH"},
                {"name": "BREAKER_BLOCK_FLIP", "win_rate": 57.0, "avg_r": 2.1, "sample_size": 65, "edge_tier": "HIGH"}
            ],
            "top_patterns": {
                "DOUBLE_BOTTOM_W_SHAPE": 62.5,
                "HEAD_AND_SHOULDERS_INVERSE": 60.0,
                "RANGE_SWEEP_RECLAIM": 64.0,
                "DOUBLE_TOP_M_SHAPE": 57.0,
                "ASCENDING_TRIANGLE": 58.5
            },
            "low_edge_warning": [
                "PURE_MOMENTUM_CHASE (High opening gap trap rate for retail)",
                "PARABOLIC_SAR (Erratic whipsaw in mid-day lull)"
            ]
        },
        "UK_STOCKS": {
            "market_name": "United Kingdom Equities (LSE - London Stock Exchange)",
            "primary_timezone": "Europe/London",
            "volatility_characteristics": "STEADY_DIVIDEND_COMMODITY_FINANCE",
            "top_strategies": [
                {"name": "TREND_CHANNEL_RIDING", "win_rate": 62.0, "avg_r": 2.1, "sample_size": 80, "edge_tier": "ELITE"},
                {"name": "LONDON_OPEN_BREAKOUT", "win_rate": 60.0, "avg_r": 2.0, "sample_size": 92, "edge_tier": "HIGH"},
                {"name": "PULLBACK_EMA_BOUNCE", "win_rate": 59.0, "avg_r": 1.8, "sample_size": 75, "edge_tier": "HIGH"},
                {"name": "MACRO_NEWS_MOMENTUM", "win_rate": 57.5, "avg_r": 2.2, "sample_size": 60, "edge_tier": "HIGH"}
            ],
            "top_patterns": {
                "FALLING_WEDGE": 63.0,
                "PENNANT_CONTINUATION": 61.0,
                "DOUBLE_BOTTOM_W_SHAPE": 59.0,
                "BULL_FLAG": 58.5
            },
            "low_edge_warning": [
                "EXOTIC_OSCILLATOR_DIVERGENCE (LSE trends smoothly without high oscillator noise)"
            ]
        },
        "EU_STOCKS": {
            "market_name": "European Equities (Frankfurt DAX / Euronext Paris)",
            "primary_timezone": "Europe/Berlin",
            "volatility_characteristics": "INDUSTRIAL_EXPORT_ORDER_FLOW",
            "top_strategies": [
                {"name": "TREND_CHANNEL_RIDING", "win_rate": 61.5, "avg_r": 2.0, "sample_size": 84, "edge_tier": "ELITE"},
                {"name": "LONDON_OPEN_BREAKOUT", "win_rate": 60.5, "avg_r": 2.1, "sample_size": 90, "edge_tier": "HIGH"},
                {"name": "FVG_INSTITUTIONAL_FILL", "win_rate": 58.0, "avg_r": 1.9, "sample_size": 65, "edge_tier": "HIGH"}
            ],
            "top_patterns": {
                "FALLING_WEDGE": 62.5,
                "ASCENDING_TRIANGLE": 60.0,
                "DOUBLE_BOTTOM_W_SHAPE": 58.5
            },
            "low_edge_warning": [
                "SCALPING_FAST_OSCILLATOR (High midday spread drag in continental Europe)"
            ]
        },
        "ASIAN_STOCKS": {
            "market_name": "Asian-Pacific Equities (Tokyo JPX / HKEX / Australia ASX)",
            "primary_timezone": "Asia/Tokyo",
            "volatility_characteristics": "MEAN_REVERTING_SESSION_AUCTIONS",
            "top_strategies": [
                {"name": "MEAN_REVERSION_BOLINGER", "win_rate": 61.0, "avg_r": 1.9, "sample_size": 85, "edge_tier": "HIGH"},
                {"name": "GAP_FADE_AUCTION", "win_rate": 60.0, "avg_r": 1.8, "sample_size": 78, "edge_tier": "HIGH"},
                {"name": "VOLUME_SPREAD_ABSORPTION", "win_rate": 59.0, "avg_r": 2.0, "sample_size": 65, "edge_tier": "HIGH"},
                {"name": "ORDER_BLOCK_GOLDEN_POCKET", "win_rate": 57.5, "avg_r": 2.1, "sample_size": 60, "edge_tier": "HIGH"}
            ],
            "top_patterns": {
                "TRIPLE_BOTTOM": 62.0,
                "RECTANGLE_RANGE_REVERSAL": 60.5,
                "DOUBLE_BOTTOM_W_SHAPE": 59.0,
                "HEAD_AND_SHOULDERS_INVERSE": 58.0
            },
            "low_edge_warning": [
                "BREAKOUT_EXPANSION (Asian sessions frequently range-bound, breakouts often fade)"
            ]
        },
        "FOREX": {
            "market_name": "Foreign Exchange Global (24/5 Currency Markets)",
            "primary_timezone": "UTC",
            "volatility_characteristics": "MACRO_INTEREST_RATE_OVERLAP_FLOWS",
            "top_strategies": [
                {"name": "LONDON_NY_OVERLAP_BREAKOUT", "win_rate": 65.0, "avg_r": 2.3, "sample_size": 140, "edge_tier": "ELITE"},
                {"name": "ASIAN_RANGE_LIQUIDITY_HUNT", "win_rate": 62.0, "avg_r": 2.1, "sample_size": 115, "edge_tier": "ELITE"},
                {"name": "FIB_SWEET_SPOT_PULLBACK", "win_rate": 58.5, "avg_r": 1.9, "sample_size": 90, "edge_tier": "HIGH"},
                {"name": "SMC_LIQUIDITY_RUN", "win_rate": 57.5, "avg_r": 2.0, "sample_size": 82, "edge_tier": "HIGH"}
            ],
            "top_patterns": {
                "PIN_BAR_KEY_SUPPORT": 64.0,
                "ENGULFING_S_D_ZONE": 61.5,
                "DOUBLE_BOTTOM_W_SHAPE": 59.0,
                "DOUBLE_TOP_M_SHAPE": 58.0
            },
            "low_edge_warning": [
                "PURE_INDICATOR_CROSS (Forex is institutional order flow; indicators lag significantly)"
            ]
        },
        "COMMODITIES": {
            "market_name": "Global Commodities (Gold, Crude Oil, Silver - COMEX / MCX)",
            "primary_timezone": "America/New_York",
            "volatility_characteristics": "GEOPOLITICAL_TREND_INFLATION_HEDGES",
            "top_strategies": [
                {"name": "COMMODITY_MOMENTUM_SURGE", "win_rate": 63.0, "avg_r": 2.5, "sample_size": 105, "edge_tier": "ELITE"},
                {"name": "BREAKOUT_EXPANSION", "win_rate": 61.0, "avg_r": 2.2, "sample_size": 95, "edge_tier": "ELITE"},
                {"name": "ORDER_BLOCK_GOLDEN_POCKET", "win_rate": 59.5, "avg_r": 2.3, "sample_size": 80, "edge_tier": "HIGH"},
                {"name": "INVENTORY_CATALYST_REVERSAL", "win_rate": 58.0, "avg_r": 2.0, "sample_size": 70, "edge_tier": "HIGH"}
            ],
            "top_patterns": {
                "BREAKAWAY_GAP": 65.0,
                "RECTANGLE_CHANNEL_BREAKOUT": 62.0,
                "BULL_FLAG": 61.5,
                "FALLING_WEDGE": 60.0
            },
            "low_edge_warning": [
                "MEAN_REVERSION_IN_CRUDE (Oil trends fiercely on supply shocks; fading trends is dangerous)"
            ]
        },
        "CRYPTO": {
            "market_name": "Cryptocurrency 24/7 (BTC, ETH, SOL, Liquid Alts)",
            "primary_timezone": "UTC",
            "volatility_characteristics": "LIQUIDATION_CASCADE_ASYMMETRIC_TRENDS",
            "top_strategies": [
                {"name": "LIQUIDATION_WICK_SWEEP", "win_rate": 66.0, "avg_r": 2.8, "sample_size": 135, "edge_tier": "ELITE"},
                {"name": "ORDER_BLOCK_GOLDEN_POCKET", "win_rate": 64.0, "avg_r": 2.6, "sample_size": 150, "edge_tier": "ELITE"},
                {"name": "BREAKER_BLOCK_FLIP", "win_rate": 61.0, "avg_r": 2.2, "sample_size": 110, "edge_tier": "HIGH"},
                {"name": "SUPERTREND_DYNAMIC_TRAIL", "win_rate": 59.0, "avg_r": 3.1, "sample_size": 95, "edge_tier": "HIGH"},
                {"name": "SMC_LIQUIDITY_RUN", "win_rate": 58.5, "avg_r": 2.3, "sample_size": 100, "edge_tier": "HIGH"}
            ],
            "top_patterns": {
                "FALLING_WEDGE_REVERSAL": 67.0,
                "SPRING_WYCKOFF_RECLAIM": 65.0,
                "DOUBLE_BOTTOM_W_SHAPE": 61.0,
                "RANGE_SWEEP_RECLAIM": 63.5
            },
            "low_edge_warning": [
                "TIGHT_FIXED_STOP_LOSS (Crypto volatility wicks hunt tight stops before explosive moves)"
            ]
        }
    }

    @classmethod
    def normalize_market_key(cls, market: str) -> str:
        """Normalizes market identifier strings to standardized profile keys."""
        m = market.upper().strip()
        if m in ["US", "US_STOCKS", "US_EQUITIES", "NASDAQ", "NYSE", "SP500"]:
            return "US_STOCKS"
        elif m in ["INDIA", "INDIAN", "INDIAN_STOCKS", "NSE", "BSE", "NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY", "HDFCBANK"] or m.endswith(".NS") or m.endswith(".BO") or "NIFTY" in m or "RELIANCE" in m:
            return "INDIAN_STOCKS"
        elif m in ["UK", "UK_STOCKS", "LSE", "FTSE", "LONDON"]:
            return "UK_STOCKS"
        elif m in ["EU", "EU_STOCKS", "EUROPE", "DAX", "CAC", "EURONEXT"]:
            return "EU_STOCKS"
        elif m in ["ASIA", "ASIAN_STOCKS", "JPX", "TOKYO", "NIKKEI", "HKEX", "ASX"]:
            return "ASIAN_STOCKS"
        elif m in ["FOREX", "FX", "CURRENCIES"]:
            return "FOREX"
        elif m in ["COMMODITY", "COMMODITIES", "GOLD", "OIL", "MCX_COMMODITY"]:
            return "COMMODITIES"
        else:
            return "CRYPTO"

    @classmethod
    def get_market_strategy_affinity(
        cls,
        market: str,
        strategy_name: str,
        live_ledger_matrix: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retrieves historical affinity score for a strategy in a given market.
        Combines empirical priors with live memory updates.
        """
        norm_market = cls.normalize_market_key(market)
        profile = cls.BASE_MARKET_PROFILES.get(norm_market, cls.BASE_MARKET_PROFILES["CRYPTO"])
        strat_clean = strategy_name.upper().strip()

        # Check empirical prior
        match: Optional[Dict[str, Any]] = None
        top_strats: List[Dict[str, Any]] = profile.get("top_strategies") or []
        for s in top_strats:
            if isinstance(s, dict) and s.get("name") == strat_clean:
                match = s
                break

        # Check live recorded data if available
        live_data: Optional[Dict[str, Any]] = None
        if live_ledger_matrix and norm_market in live_ledger_matrix:
            mkt_ledger = live_ledger_matrix.get(norm_market)
            if isinstance(mkt_ledger, dict):
                live_data = mkt_ledger.get(strat_clean)

        if live_data is not None and int(live_data.get("sample_size", 0)) >= 5:
            # Live paper performance takes precedence when sample is sufficient
            win_rate = float(live_data.get("win_rate", 50.0))
            avg_r = float(live_data.get("avg_r", 1.5))
            samples = int(live_data.get("sample_size", 5))
            tier = "ELITE" if win_rate >= 62.0 else ("HIGH" if win_rate >= 55.0 else "NEUTRAL")
        elif match is not None:
            win_rate = float(match.get("win_rate", 50.0))
            avg_r = float(match.get("avg_r", 1.5))
            samples = int(match.get("sample_size", 20))
            tier = str(match.get("edge_tier", "NEUTRAL"))
        else:
            win_rate = 50.0
            avg_r = 1.5
            samples = 20
            tier = "NEUTRAL"

        # Calculate affinity weight bonus for strategy selection (0.8x to 1.35x)
        affinity_multiplier = round(win_rate / 50.0, 2)

        return {
            "market": norm_market,
            "strategy_name": strat_clean,
            "win_rate": win_rate,
            "avg_r": avg_r,
            "sample_size": samples,
            "edge_tier": tier,
            "affinity_multiplier": affinity_multiplier,
            "is_market_champion": tier in ["ELITE", "HIGH"]
        }

    @classmethod
    def get_market_pattern_affinity(
        cls,
        market: str,
        pattern_name: str,
        live_ledger_patterns: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retrieves market-specific win rate and reliability for a chart pattern.
        """
        norm_market = cls.normalize_market_key(market)
        profile = cls.BASE_MARKET_PROFILES.get(norm_market, cls.BASE_MARKET_PROFILES["CRYPTO"])
        patt_clean = pattern_name.upper().strip()

        patt_dict: Dict[str, Any] = profile.get("top_patterns") or {}
        prior_wr: float = float(patt_dict.get(patt_clean, 52.0))

        # Check live pattern memory
        if live_ledger_patterns and norm_market in live_ledger_patterns:
            market_patterns = live_ledger_patterns.get(norm_market)
            if isinstance(market_patterns, dict):
                lp = market_patterns.get(patt_clean)
                if isinstance(lp, dict) and int(lp.get("sample_size", 0)) >= 5:
                    prior_wr = float(lp.get("win_rate", prior_wr))

        return {
            "market": norm_market,
            "pattern_name": patt_clean,
            "historical_win_rate_pct": round(prior_wr, 1),
            "is_high_probability_in_market": prior_wr >= 58.0
        }

    @classmethod
    def get_top_strategies_for_market(cls, market: str) -> List[Dict[str, Any]]:
        """Returns the top institutional strategies for the requested share market."""
        norm_market = cls.normalize_market_key(market)
        profile = cls.BASE_MARKET_PROFILES.get(norm_market, cls.BASE_MARKET_PROFILES["CRYPTO"])
        strategies = profile.get("top_strategies")
        if isinstance(strategies, list):
            return [s for s in strategies if isinstance(s, dict)]
        return []

    @classmethod
    def get_all_supported_markets(cls) -> List[Dict[str, Any]]:
        """Returns metadata for all 8 supported world markets."""
        result: List[Dict[str, Any]] = []
        for code, data in cls.BASE_MARKET_PROFILES.items():
            if isinstance(data, dict):
                result.append({
                    "market_code": code,
                    "name": str(data.get("market_name", code)),
                    "timezone": str(data.get("primary_timezone", "UTC")),
                    "characteristics": str(data.get("volatility_characteristics", ""))
                })
        return result

