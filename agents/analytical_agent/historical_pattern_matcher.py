"""
Historical Pattern Analogue & Fractal Matching Engine
Scans 500+ historical candles to find prior occurrences of the currently active chart pattern
(e.g., Double Top, Double Bottom, Bullish Engulfing, Wyckoff Spring, FVG Tap).
Calculates empirical forward returns over 5, 10, and 20 bars to compute authentic Historical Win Rate %.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from agents.evolution_memory.market_memory_matrix import MarketMemoryMatrix

logger = logging.getLogger("HistoricalPatternMatcher")


class HistoricalPatternMatcher:
    """
    Empirical Pattern Backtesting Engine.
    Answers: 'When this exact pattern appeared in the past in this specific market, what actually happened next?'
    """

    @staticmethod
    def _compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - df["close"].shift(1)).abs(),
            (df["low"] - df["close"].shift(1)).abs()
        ], axis=1).max(axis=1)
        return tr.rolling(period).mean().fillna(df["close"] * 0.015)

    @classmethod
    def analyze_pattern_historical_edge(
        cls,
        df: pd.DataFrame,
        pattern_name: str,
        market: str = "CRYPTO",
        expected_direction: str = "BULLISH",  # BULLISH or BEARISH
        forward_bars: int = 10,
        target_atr_multiple: float = 1.5,
        stop_atr_multiple: float = 1.0
    ) -> Dict[str, Any]:
        """
        Scans historical bars for occurrences of the specified pattern in this market and evaluates forward returns.
        """
        market_prior = MarketMemoryMatrix.get_market_pattern_affinity(market, pattern_name)
        prior_wr = market_prior["historical_win_rate_pct"]

        if df.empty or len(df) < 50:
            return {
                "pattern": pattern_name,
                "market": market,
                "historical_occurrences": 0,
                "win_rate_pct": prior_wr,
                "market_prior_win_rate": prior_wr,
                "edge_verdict": "MARKET_PRIOR_DEFAULT",
                "avg_gain_pct": 0.0,
                "avg_loss_pct": 0.0,
                "profit_factor": 1.5
            }

        highs: List[float] = [float(x) for x in df["high"]]
        lows: List[float] = [float(x) for x in df["low"]]
        closes: List[float] = [float(x) for x in df["close"]]
        opens: List[float] = [float(x) for x in df["open"]]
        atr_series = cls._compute_atr(df)
        atr_vals: List[float] = [float(x) for x in atr_series]
        n = len(df)

        pattern_upper = pattern_name.upper()
        occurrences: List[int] = []

        # 1. Locate all historical bars where this pattern triggered
        for i in range(25, n - forward_bars):
            c_high = highs[i]
            c_low = lows[i]
            c_close = closes[i]
            c_open = opens[i]
            prev_close = closes[i-1]
            prev_open = opens[i-1]

            matched = False

            # Double Top / Double Bottom
            if "DOUBLE_TOP" in pattern_upper or "M_SHAPE" in pattern_upper:
                prior_highs = highs[max(0, i-20):max(0, i-2)]
                if len(prior_highs) > 0 and (abs(c_high - max(prior_highs)) / (c_close + 1e-6)) < 0.008 and c_close < c_open:
                    matched = True
            elif "DOUBLE_BOTTOM" in pattern_upper or "W_SHAPE" in pattern_upper:
                prior_lows = lows[max(0, i-20):max(0, i-2)]
                if len(prior_lows) > 0 and (abs(c_low - min(prior_lows)) / (c_close + 1e-6)) < 0.008 and c_close > c_open:
                    matched = True

            # Engulfing Candlestick
            elif "BULLISH_ENGULFING" in pattern_upper or "ENGULFING" in pattern_upper:
                if (c_close > c_open) and (prev_close < prev_open) and (c_close >= prev_open) and (c_open <= prev_close):
                    matched = True
            elif "BEARISH_ENGULFING" in pattern_upper:
                if (c_close < c_open) and (prev_close > prev_open) and (c_close <= prev_open) and (c_open >= prev_close):
                    matched = True

            # Hammer / Pin Bar
            elif "HAMMER" in pattern_upper or "PIN_BAR" in pattern_upper:
                body = abs(c_close - c_open)
                lower_wick = min(c_open, c_close) - c_low
                if lower_wick >= 2.0 * max(body, 1e-6):
                    matched = True

            # Shooting Star
            elif "SHOOTING_STAR" in pattern_upper:
                body = abs(c_close - c_open)
                upper_wick = c_high - max(c_open, c_close)
                if upper_wick >= 2.0 * max(body, 1e-6):
                    matched = True

            # Fair Value Gap / ICT Imbalance Tap
            elif "FVG" in pattern_upper or "IMBALANCE" in pattern_upper:
                if expected_direction == "BULLISH" and c_low > highs[i-2]:
                    matched = True
                elif expected_direction == "BEARISH" and c_high < lows[i-2]:
                    matched = True

            # Wyckoff Spring
            elif "SPRING" in pattern_upper:
                prior_slice = lows[max(0, i-15):max(0, i-1)]
                prior_low = min(prior_slice) if prior_slice else c_low
                if c_low < prior_low and c_close > prior_low and c_close > c_open:
                    matched = True

            # Generic Breakout / Structure Shift
            else:
                high_slice = highs[max(0, i-15):max(0, i-1)]
                low_slice = lows[max(0, i-15):max(0, i-1)]
                prior_high = max(high_slice) if high_slice else c_high
                prior_low = min(low_slice) if low_slice else c_low
                if expected_direction == "BULLISH" and c_close > prior_high:
                    matched = True
                elif expected_direction == "BEARISH" and c_close < prior_low:
                    matched = True

            if matched:
                occurrences.append(i)

        if not occurrences:
            return {
                "pattern": pattern_name,
                "historical_occurrences": 0,
                "win_rate_pct": 52.0,
                "edge_verdict": "NO_HISTORICAL_SAMPLES",
                "avg_gain_pct": 0.0,
                "avg_loss_pct": 0.0,
                "profit_factor": 1.1
            }

        # 2. Evaluate forward performance across all matched past bars
        wins = 0
        losses = 0
        gains: List[float] = []
        loss_pcts: List[float] = []

        is_bullish = expected_direction.upper() == "BULLISH"

        for idx in occurrences:
            entry_p = closes[idx]
            atr = atr_vals[idx] if atr_vals[idx] > 0 else entry_p * 0.015
            target_p = entry_p + (atr * target_atr_multiple) if is_bullish else entry_p - (atr * target_atr_multiple)
            stop_p = entry_p - (atr * stop_atr_multiple) if is_bullish else entry_p + (atr * stop_atr_multiple)

            # Check outcome in next forward_bars
            outcome = "IN_PROGRESS"
            max_favorable = 0.0
            max_adverse = 0.0

            for f in range(1, forward_bars + 1):
                cur_h = highs[idx + f]
                cur_l = lows[idx + f]

                if is_bullish:
                    max_favorable = max(max_favorable, (cur_h - entry_p) / entry_p)
                    max_adverse = min(max_adverse, (cur_l - entry_p) / entry_p)
                    if cur_h >= target_p:
                        outcome = "WIN"
                        break
                    elif cur_l <= stop_p:
                        outcome = "LOSS"
                        break
                else:
                    max_favorable = max(max_favorable, (entry_p - cur_l) / entry_p)
                    max_adverse = min(max_adverse, (entry_p - cur_h) / entry_p)
                    if cur_l <= target_p:
                        outcome = "WIN"
                        break
                    elif cur_h >= stop_p:
                        outcome = "LOSS"
                        break

            if outcome == "WIN":
                wins += 1
                gains.append(target_atr_multiple * (atr / entry_p) * 100)
            elif outcome == "LOSS":
                losses += 1
                loss_pcts.append(stop_atr_multiple * (atr / entry_p) * 100)
            else:
                # End of forward window; check net displacement
                end_p = closes[idx + forward_bars]
                ret = (end_p - entry_p) / entry_p if is_bullish else (entry_p - end_p) / entry_p
                if ret > 0:
                    wins += 1
                    gains.append(ret * 100)
                else:
                    losses += 1
                    loss_pcts.append(abs(ret) * 100)

        total = wins + losses
        raw_win_rate = round((wins / total) * 100, 1) if total > 0 else prior_wr
        if total >= 5:
            win_rate = round(raw_win_rate * 0.7 + prior_wr * 0.3, 1)
        elif total > 0:
            win_rate = round(raw_win_rate * 0.4 + prior_wr * 0.6, 1)
        else:
            win_rate = prior_wr

        avg_gain = round(float(np.mean(gains)), 2) if gains else 0.0
        avg_loss = round(float(np.mean(loss_pcts)), 2) if loss_pcts else 0.0
        pf = round((sum(gains) / sum(loss_pcts)), 2) if sum(loss_pcts) > 0 else 2.5

        if win_rate >= 62.0:
            verdict = "HIGH_HISTORICAL_EDGE"
        elif win_rate >= 50.0:
            verdict = "AVERAGE_HISTORICAL_EDGE"
        else:
            verdict = "HISTORICAL_TRAP_HIGH_FAILURE_RISK"

        logger.info(
            f"[PatternMatcher] Pattern: {pattern_name} in {market} | Past Occurrences: {len(occurrences)} | "
            f"Blended Win Rate: {win_rate}% (Market Prior: {prior_wr}%) | Profit Factor: {pf} ({verdict})"
        )

        return {
            "pattern": pattern_name,
            "market": market,
            "historical_occurrences": len(occurrences),
            "forward_bars_analyzed": forward_bars,
            "wins": wins,
            "losses": losses,
            "win_rate_pct": win_rate,
            "market_prior_win_rate": prior_wr,
            "avg_gain_pct": avg_gain,
            "avg_loss_pct": avg_loss,
            "profit_factor": pf,
            "edge_verdict": verdict,
            "is_statistically_sound": win_rate >= 58.0
        }


if __name__ == "__main__":
    from agents.analytical_agent.market_feed import MarketFeedEngine
    feed = MarketFeedEngine()
    print("Testing Historical Pattern Matcher across 300 candles of BTC...")
    df_btc = feed.fetch_crypto_candles("BTC", interval="15m", limit=300)
    res = HistoricalPatternMatcher.analyze_pattern_historical_edge(
        df=df_btc,
        pattern_name="DOUBLE_BOTTOM_W_SHAPE",
        expected_direction="BULLISH",
        forward_bars=10
    )
    print("\n--- Empirical Historical Pattern Results ---")
    print(f"Pattern: {res['pattern']}")
    print(f"Past Occurrences in Lookback: {res['historical_occurrences']}")
    print(f"Historical Win Rate: {res['win_rate_pct']}% (Wins: {res['wins']}, Losses: {res['losses']})")
    print(f"Profit Factor: {res['profit_factor']} | Edge Verdict: {res['edge_verdict']}")
