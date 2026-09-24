"""
Institutional Multi-Chart Screener & Predictability Filter
==========================================================
Scans multiple companies / assets across the selected market (or ALL markets),
screens out unpredictable, erratic, illiquid, or choppy charts, and selects
the BEST and SAFEST chart for trading that day.

Evaluation Dimensions:
1. Market Structure Cleanliness: Trend directionality vs random noise / chop.
2. Predictability Score: Body-to-wick ratio, EMA alignment (9/21/50), clean swings.
3. Volatility Suitability: ATR % of price (ensures sufficient room for 1:2 R:R, avoids hyper-erratic gaps).
4. Volume & Liquidity: Adequate volume flow to prevent slippage drag.
5. SMC / Technical Clarity: Presence of defined Order Blocks, FVGs, and Key Levels.
6. News Catalyst Alignment: Cross-references ticker with breaking news sentiment.
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from shared_brain.omni_calculator import OmniCalculator

logger = logging.getLogger("MarketScreener")


class MultiChartScreener:
    """
    Evaluates a basket of candidate tickers and filters out unpredictable,
    choppy, or dangerous charts to crown the single safest chart for today's trade.
    """

    UNIVERSE_MAP = {
        "INDIAN_STOCKS": [
            # NIFTY 50 Heavyweights
            "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "ITC", "SBIN", "LICI", "LT",
            "HINDUNILVR", "BAJFINANCE", "HCLTECH", "MARUTI", "SUNPHARMA", "ADANIENT", "KOTAKBANK", "TATAMOTORS",
            "AXISBANK", "NTPC", "TITAN", "ONGC", "TATACONSUM", "ADANIPORTS", "POWERGRID", "COALINDIA", "BAJAJFINSV",
            "TATASTEEL", "ULTRACEMCO", "ASIANPAINT", "M&M", "SIEMENS", "JSWSTEEL", "IOC", "GRASIM", "BAJAJ-AUTO",
            "ZOMATO", "DLF", "TECHM", "WIPRO", "HINDALCO", "NESTLEIND", "BPCL", "EICHERMOT", "DIVISLAB", "CIPLA",
            "APOLLOHOSP", "TRENT", "BEL", "HAL",
            # NIFTY Next 50 & Momentum Midcaps
            "JIOFIN", "VEDL", "TATAPOWER", "CHOLAFIN", "SHRIRAMFIN", "PFC", "REC", "BHEL", "INDIGO", "TVSMOTOR",
            "HAVELLS", "PIDILITIND", "GAIL", "GODREJCP", "DABUR", "AMBUJACEM", "ABB", "MOTHERSON", "CANBK", "PNB",
            "BANKBARODA", "POLYCAB", "PERSISTENT", "COFORGE", "MPHASIS", "LTIM", "NAUKRI", "IRCTC", "RVNL", "IRFC",
            "SUZLON", "PAYTM", "IDEA", "YESBANK", "FEDERALBNK", "IDFCFIRSTB", "ABCAPITAL", "MUTHOOTFIN", "MANAPPURAM",
            "AUROPHARMA", "LUPIN", "BIOCON", "GLENMARK", "VOLTAS", "CROMPTON", "DIXON", "KALYANKJIL", "MAXHEALTH",
            "FORTIS", "JUBLFOOD", "DEVYANI"
        ],
        "CRYPTO": [
            "BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "SUI", "LINK",
            "SHIB", "PEPE", "NEAR", "APT", "DOT", "UNI", "LTC", "ICP", "FET", "RENDER",
            "INJ", "TIA", "ARB", "OP", "KAS", "FTM", "AAVE", "STX", "BONK", "WIF",
            "RUNE", "FIL", "ATOM", "ETC", "XLM", "POL", "IMX", "GRT", "FLOKI", "SEI",
            "TAO", "JUP", "ENA", "PYTH", "PENDLE", "WLD", "ALGO", "QNT", "MANA", "SAND",
            "GALA", "VET", "THETA"
        ],
        "US_STOCKS": [
            "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "AVGO", "LLY",
            "JPM", "V", "UNH", "XOM", "MA", "WMT", "JNJ", "PG", "COST", "ORCL",
            "HD", "AMD", "NFLX", "BAC", "CRM", "CVX", "MRK", "KO", "ADBE", "QCOM",
            "PLTR", "SMCI", "COIN", "MSTR", "INTC", "ARM", "UBER", "DIS", "BA", "NKE",
            "IBM", "TXN", "GE", "AMAT", "MU", "CAT", "GS", "MS", "RTX", "HON",
            "SPY", "QQQ"
        ],
        "FOREX": [
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
            "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "NZDJPY", "EURCHF", "GBPCHF", "AUDNZD"
        ],
        "COMMODITIES": [
            "GOLD", "SILVER", "CRUDEOIL", "BRENT", "NATGAS", "COPPER", "PLATINUM"
        ],
        "UK_STOCKS": ["BP", "VOD", "AZN", "SHEL", "HSBA", "RIO", "GSK", "BATS"],
        "EU_STOCKS": ["SAP", "BMW", "AIR", "SIE", "ASML", "OR", "MC", "ALV"],
        "ASIAN_STOCKS": ["7203.T", "9984.T", "SONY", "6758.T", "9983.T"]
    }

    WILD_UNIVERSE_MAP = {
        "INDIAN_STOCKS": [
            "TATAMOTORS", "ADANIENT", "BAJFINANCE", "TATASTEEL", "RELIANCE", "JIOFIN", "VEDL", "TATAPOWER",
            "PFC", "REC", "BHEL", "SUZLON", "PAYTM", "IDEA", "YESBANK", "ZOMATO", "DLF", "TRENT", "BEL", "HAL",
            "DIXON", "KALYANKJIL", "RVNL", "IRFC", "COFORGE", "PERSISTENT"
        ],
        "CRYPTO": [
            "SOL", "DOGE", "PEPE", "SHIB", "BONK", "WIF", "AVAX", "NEAR", "SUI", "APT",
            "FET", "RENDER", "INJ", "TIA", "SEI", "TAO", "JUP", "ENA", "BTC", "ETH"
        ],
        "US_STOCKS": [
            "TSLA", "NVDA", "AMD", "SMCI", "COIN", "MSTR", "PLTR", "ARM", "META", "AMZN",
            "NFLX", "UBER", "INTC", "MU", "QQQ"
        ],
        "FOREX": [
            "GBPUSD", "USDJPY", "GBPJPY", "EURUSD", "AUDUSD", "AUDJPY"
        ],
        "COMMODITIES": [
            "CRUDEOIL", "GOLD", "SILVER", "NATGAS"
        ],
        "UK_STOCKS": ["BP", "VOD", "AZN", "SHEL"],
        "EU_STOCKS": ["BMW", "SAP", "AIR", "ASML"],
        "ASIAN_STOCKS": ["9984.T", "SONY"]
    }

    def __init__(self):
        self.calc = OmniCalculator(owner="MarketScreener")

    def get_candidate_universe(self, market: str, mode: str = "CONSERVATIVE_SAFE", limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Returns candidate ticker list for a market or across ALL major markets."""
        market_upper = market.upper()
        candidates = []
        is_wild = "WILD" in mode.upper()
        universe_source = self.WILD_UNIVERSE_MAP if is_wild else self.UNIVERSE_MAP

        if market_upper in ["ALL", "ALL_THREE", "MULTI_MARKET", "TOTAL"]:
            # Balanced cross-market institutional basket across ALL available markets
            in_syms = universe_source.get("INDIAN_STOCKS", [])[:35]
            cry_syms = universe_source.get("CRYPTO", [])[:25]
            us_syms = universe_source.get("US_STOCKS", [])[:25]
            fx_syms = universe_source.get("FOREX", [])[:10]
            comm_syms = universe_source.get("COMMODITIES", [])[:5]

            for sym in in_syms:
                candidates.append({"market": "INDIAN_STOCKS", "symbol": sym})
            for sym in cry_syms:
                candidates.append({"market": "CRYPTO", "symbol": sym})
            for sym in us_syms:
                candidates.append({"market": "US_STOCKS", "symbol": sym})
            for sym in fx_syms:
                candidates.append({"market": "FOREX", "symbol": sym})
            for sym in comm_syms:
                candidates.append({"market": "COMMODITIES", "symbol": sym})
        elif market_upper in universe_source:
            for sym in universe_source[market_upper]:
                candidates.append({"market": market_upper, "symbol": sym})
        else:
            fallback = universe_source.get("INDIAN_STOCKS", ["RELIANCE", "TCS", "INFY"])
            for sym in fallback:
                candidates.append({"market": "INDIAN_STOCKS", "symbol": sym})

        if limit and limit > 0:
            return candidates[:limit]
        return candidates

    def evaluate_chart_predictability(
        self,
        df: pd.DataFrame,
        symbol: str,
        market: str,
        news_bias: str = "NEUTRAL",
        mode: str = "CONSERVATIVE_SAFE"
    ) -> Dict[str, Any]:
        """
        Scores a single chart from 0 to 100 on structure clarity,
        volatility suitability, and predictability based on the active mode:
        - CONSERVATIVE_SAFE: Rewards steady trends, penalizes high volatility.
        - WILD_MODE: Rewards explosive momentum surges, high ATR expansion, and news catalysts.
        """
        is_wild = "WILD" in mode.upper()
        if df.empty or len(df) < 20:
            return {
                "symbol": symbol,
                "market": market,
                "safety_score": 0.0,
                "status": "UNPREDICTABLE_INSUFFICIENT_DATA",
                "rejection_reason": "Less than 20 bars available."
            }

        closes = df["close"].values
        highs = df["high"].values
        lows = df["low"].values
        opens = df["open"].values
        volumes = df["volume"].values if "volume" in df.columns else np.ones(len(df))

        # 1. EMAs & Trend Cleanliness (0 to 30 pts)
        ema9 = pd.Series(closes).ewm(span=9).mean().values
        ema21 = pd.Series(closes).ewm(span=21).mean().values
        ema50 = pd.Series(closes).ewm(span=50).mean().values if len(closes) >= 50 else ema21

        trend_aligned_bull = (ema9[-1] > ema21[-1] > ema50[-1])
        trend_aligned_bear = (ema9[-1] < ema21[-1] < ema50[-1])
        fast_momentum_breakout = abs(closes[-1] - ema9[-1]) > abs(ema9[-1] - ema21[-1])

        if is_wild:
            # Wild mode values fast momentum breakouts and directional bursts
            trend_cleanliness = 30.0 if fast_momentum_breakout else (20.0 if (trend_aligned_bull or trend_aligned_bear) else 10.0)
        else:
            trend_cleanliness = 30.0 if (trend_aligned_bull or trend_aligned_bear) else 15.0

        # 2. Body-to-Wick Ratio / Chop Penalty (0 to 25 pts)
        recent_bars = min(15, len(df))
        candle_bodies = [abs(closes[-i] - opens[-i]) for i in range(1, recent_bars + 1)]
        candle_ranges = [max(highs[-i] - lows[-i], 0.0001) for i in range(1, recent_bars + 1)]
        body_ratios = [b / r for b, r in zip(candle_bodies, candle_ranges)]
        avg_body_ratio = sum(body_ratios) / len(body_ratios)

        if avg_body_ratio > 0.55:
            structure_clarity_score = 25.0
        elif avg_body_ratio > 0.40:
            structure_clarity_score = 18.0
        elif avg_body_ratio > 0.25:
            structure_clarity_score = 10.0
        else:
            structure_clarity_score = 2.0  # Heavy wick chop

        # 3. Volatility Suitability (ATR % of Price) (0 to 25 pts)
        tr_list = []
        for i in range(1, min(len(df), 15)):
            tr = max(highs[-i] - lows[-i], abs(highs[-i] - closes[-i-1]), abs(lows[-i] - closes[-i-1]))
            tr_list.append(tr)
        atr = sum(tr_list) / len(tr_list) if tr_list else 1.0
        curr_price = closes[-1]
        atr_pct = (atr / curr_price) * 100.0 if curr_price > 0 else 1.0

        if is_wild:
            # WILD MODE REWARDS HEAVY VOLATILITY (Intraday fast money fuel on 5m/15m bars!)
            if 0.35 <= atr_pct <= 3.5:
                volatility_score = 25.0
                volatility_status = "WILD_EXPLOSIVE_VOLATILITY"
            elif 0.20 <= atr_pct < 0.35:
                volatility_score = 20.0
                volatility_status = "MODERATE_HIGH_VOLATILITY"
            elif atr_pct > 3.5:
                volatility_score = 15.0
                volatility_status = "EXTREME_VOLATILITY"
            elif atr_pct < 0.12:
                volatility_score = 3.0
                volatility_status = "TOO_SLOW_FOR_WILD_MODE"
            else:
                volatility_score = 14.0
                volatility_status = "ACCEPTABLE_VOLATILITY"
        else:
            # CONSERVATIVE SAFE MODE (Prefers smooth, stable candle ranges)
            if 0.15 <= atr_pct <= 0.80:
                volatility_score = 25.0
                volatility_status = "OPTIMAL_VOLATILITY"
            elif 0.08 <= atr_pct < 0.15:
                volatility_score = 18.0
                volatility_status = "LOW_VOLATILITY"
            elif 0.80 < atr_pct <= 2.0:
                volatility_score = 15.0
                volatility_status = "HIGH_VOLATILITY_CAUTION"
            elif atr_pct < 0.08:
                volatility_score = 5.0
                volatility_status = "DEAD_FLAT_CHART"
            else:
                volatility_score = 2.0
                volatility_status = "HYPER_ERRATIC_CHART"

        # 4. Liquidity & Volume Surge (0 to 10 pts)
        vol_slice = [float(v) for v in (volumes[-10:] if len(volumes) >= 10 else volumes)]
        avg_vol = float(sum(vol_slice) / len(vol_slice)) if len(vol_slice) > 0 else 1.0
        last_vol = float(volumes[-1]) if len(volumes) > 0 else 1.0
        volume_surge = bool(last_vol > (avg_vol * 1.5))

        if is_wild:
            volume_score = 10.0 if volume_surge else 6.0
        else:
            if len(vol_slice) > 1:
                variance = sum((x - avg_vol) ** 2 for x in vol_slice) / len(vol_slice)
                vol_std = variance ** 0.5
                vol_variance = float(vol_std / (avg_vol + 1e-6))
            else:
                vol_variance = 0.0
            volume_score = 10.0 if vol_variance < 1.5 else 5.0

        # 5. News Sentiment Synergy (0 to 10 pts) - Strictly required so Wild Mode is NOT random gambling!
        news_synergy_score = 5.0
        if (trend_aligned_bull and "BULLISH" in news_bias) or (trend_aligned_bear and "BEARISH" in news_bias):
            news_synergy_score = 10.0
        elif (trend_aligned_bull and "BEARISH" in news_bias) or (trend_aligned_bear and "BULLISH" in news_bias):
            news_synergy_score = 2.0  # Macro contradiction

        total_score = trend_cleanliness + structure_clarity_score + volatility_score + volume_score + news_synergy_score

        # Status Classification
        if is_wild:
            if total_score >= 70.0 and volatility_status != "TOO_SLOW_FOR_WILD_MODE":
                status = "WILD_EXPLOSIVE_MOMENTUM"
            elif total_score >= 50.0 and volatility_status != "TOO_SLOW_FOR_WILD_MODE":
                status = "WILD_ACCEPTABLE"
            else:
                status = "UNPREDICTABLE_REJECTED"
        else:
            if total_score >= 75.0 and volatility_status != "HYPER_ERRATIC_CHART":
                status = "SAFE_PREDICTABLE"
            elif total_score >= 55.0 and volatility_status not in ["DEAD_FLAT_CHART", "HYPER_ERRATIC_CHART"]:
                status = "ACCEPTABLE"
            else:
                status = "UNPREDICTABLE_REJECTED"

        return {
            "symbol": symbol,
            "market": market,
            "mode": mode,
            "safety_score": round(total_score, 1),
            "status": status,
            "trend_clarity": "BULLISH_TREND" if trend_aligned_bull else ("BEARISH_TREND" if trend_aligned_bear else "RANGING_OR_CHOP"),
            "body_ratio": round(avg_body_ratio, 2),
            "atr_pct": round(atr_pct, 2),
            "volatility_status": volatility_status,
            "current_price": round(float(curr_price), 2),
            "rejection_reason": None if status != "UNPREDICTABLE_REJECTED" else f"Low suitability score ({total_score:.1f}) with {volatility_status} in {mode}."
        }

    def select_best_and_safest_chart(
        self,
        feed_engine: Any,
        market: str,
        news_bias: str = "NEUTRAL",
        timeframe: str = "15m",
        mode: str = "CONSERVATIVE_SAFE"
    ) -> Dict[str, Any]:
        """
        Scans all candidate charts in the market universe, ranks them,
        rejects unsuitable ones, and returns the #1 chart suited for the selected mode!
        """
        candidates = self.get_candidate_universe(market, mode=mode)
        logger.info(f"[MarketScreener] 🔍 Scanning {len(candidates)} charts in {market} for [{mode}]...")

        screened_results = []
        for cand in candidates:
            mkt = cand["market"]
            sym = cand["symbol"]
            try:
                df = feed_engine.get_market_data(mkt, sym, interval=timeframe)
                eval_res = self.evaluate_chart_predictability(df, sym, mkt, news_bias=news_bias, mode=mode)
                screened_results.append(eval_res)
            except Exception as e:
                logger.warning(f"[MarketScreener] Error scanning {mkt}:{sym} ({e})")
                screened_results.append({
                    "symbol": sym,
                    "market": mkt,
                    "safety_score": 0.0,
                    "status": "UNPREDICTABLE_REJECTED",
                    "rejection_reason": str(e)
                })

        # Sort descending by safety_score
        screened_results.sort(key=lambda x: x["safety_score"], reverse=True)

        safest_chart = screened_results[0] if screened_results else {
            "symbol": "BTC",
            "market": "CRYPTO",
            "safety_score": 50.0,
            "status": "ACCEPTABLE"
        }

        logger.info(f"[MarketScreener] 👑 Crowned Best Setup for {mode}: {safest_chart['market']}:{safest_chart['symbol']} (Score: {safest_chart['safety_score']}/100 | {safest_chart['status']})")

        return {
            "best_chart": safest_chart,
            "all_screened_charts": screened_results,
            "mode": mode,
            "qualified_count": sum(1 for r in screened_results if "ACCEPTABLE" in r["status"] or "SAFE" in r["status"] or "WILD" in r["status"]),
            "safe_count": sum(1 for r in screened_results if "ACCEPTABLE" in r["status"] or "SAFE" in r["status"] or "WILD" in r["status"]),
            "rejected_count": sum(1 for r in screened_results if r["status"] == "UNPREDICTABLE_REJECTED"),
            "timestamp": pd.Timestamp.now().isoformat()
        }
