"""
Master Technical Chart Analyst Agent — 15-Section Comprehensive Institutional Suite
Fuses:
- Section 1: Market Structure (HH/HL, LL/LH, BOS, MSB / CHoCH, Wyckoff Phases)
- Section 2: Candlestick Context & 25+ Formations (Pin Bars, Absorption, Engulfing, Morning Star)
- Section 3 & 4: Support/Resistance, PDH/PDL, PWH/PWL, Supply & Demand Zones (DBR, RBD)
- Section 5 & 6: Classical Chart Patterns (Double Top/Bottom, H&S, Flags, Triangles)
- Section 7: Fibonacci OTE (0.618 - 0.786), Golden Ratio, Extensions (1.272, 1.618)
- Section 8: ICT Smart Money (BSL/SSL Pools, FVG 50% CE, Breaker Blocks, Turtle Soup)
- Section 9 & 15: Multi-Timeframe (MTF) & Session Killzones (Asian, London, NY Open, AMD)
- Section 10 & 11: Volume Profile (POC/VAH/VAL), VWAP, 150+ Indicators, ADX/DMI, Regular & Hidden Divergences
- Section 12, 13 & 14: Structural SL/TP, Fakeout vs Real Breakout validation, 1:2.5+ Target
- Unified through NVIDIA NIM LLM Brain (Llama 3.3 70B / DeepSeek R1).
"""

import sys
import os
import logging
import pandas as pd
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from shared_brain.llm_brain import LLMBrain
from agents.analytical_agent.market_feed import MarketFeedEngine
from agents.analytical_agent.technical_indicators import TechnicalIndicators
from agents.analytical_agent.smc_patterns import SmartMoneyConcepts
from agents.analytical_agent.candlestick_patterns import CandlestickPatternRecognizer
from agents.analytical_agent.price_action_patterns import PriceActionEngine
from agents.analytical_agent.key_levels_and_fib import KeyLevelsAndFibEngine
from agents.analytical_agent.ict_smart_money_engine import ICTSmartMoneyEngine
from agents.analytical_agent.comprehensive_indicators import ComprehensiveIndicators
from agents.analytical_agent.divergence_engine import DivergenceEngine
from agents.analytical_agent.timeframe_modes import TimeframeModeSelector
from agents.analytical_agent.historical_pattern_matcher import HistoricalPatternMatcher
from agents.analytical_agent.market_screener import MultiChartScreener
from agents.analytical_agent.institutional_trap_detector import InstitutionalTrapDetector
from agents.analytical_agent.fractal_htf_engine import FractalHTFEngine
from shared_brain.omni_calculator import OmniCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AnalyticalAgent")


class MarketAnalyticalAgent:
    """
    Complete 20-30 Year Experienced Institutional Market Analytical Brain.
    Evaluates 15 layers of technical, volume, SMC, price action analysis,
    and institutional liquidity traps (Depth 2/3) simultaneously.
    """

    def __init__(self):
        self.feed = MarketFeedEngine()
        self.brain = LLMBrain()
        self.calc = OmniCalculator(owner="AnalyticalAgent")
        self.screener = MultiChartScreener()
        self.trap_detector = InstitutionalTrapDetector()
        self.latest_analysis: Dict[str, Any] = {}

    def screen_and_select_best_chart(self, market: str, news_bias: str = "NEUTRAL", timeframe: str = "15m", mode: str = "CONSERVATIVE_SAFE") -> Dict[str, Any]:
        """Scans multiple company/asset charts across the market and selects the best chart for the selected mode."""
        return self.screener.select_best_and_safest_chart(self.feed, market, news_bias=news_bias, timeframe=timeframe, mode=mode)

    def analyze_asset(self, market_type: str, symbol: str, timeframe: str = "15m", mode: str = "SWING_TRADING", df_override: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Executes complete 15-Section Multi-Layered Technical Quant Scan.
        """
        logger.info(f"[AnalyticalAgent] Running 15-Section Deep Scan for {symbol} ({market_type}) on {timeframe}...")
        df = df_override if df_override is not None else self.feed.get_market_data(market_type, symbol, interval=timeframe)

        if df.empty or len(df) < 20:
            logger.warning(f"[AnalyticalAgent] Insufficient candle data for {symbol}.")
            return {"symbol": symbol, "status": "DATA_UNAVAILABLE", "verdict": "NEUTRAL", "confidence": 0.0}

        current_price = float(df["close"].iloc[-1])

        # 1. Market Structure & Classical Patterns (Section 1, 5, 6)
        price_action = PriceActionEngine.analyze_price_action(df)
        structure = price_action["market_structure"]

        # 2. Key Levels, S&D Zones & Fibonacci OTE (Section 3, 4, 7)
        key_levels = KeyLevelsAndFibEngine.get_timeframe_key_levels(df)
        sd_zones = KeyLevelsAndFibEngine.identify_supply_demand_zones(df)
        is_uptrend = "UPTREND" in structure.get("trend", "")
        fibs = KeyLevelsAndFibEngine.calculate_fibonacci_levels(key_levels.get("pdl", current_price * 0.98), key_levels.get("pdh", current_price * 1.02), is_uptrend=is_uptrend)

        # 3. ICT Smart Money, Liquidity Pools & Killzones (Section 8, 15)
        ict_data = ICTSmartMoneyEngine.analyze_ict_suite(df)

        # 4. Candlestick Patterns & Rejections (Section 2)
        candlestick_intel = CandlestickPatternRecognizer.get_candlestick_verdict(df)

        # 5. Comprehensive Indicators & Volume Profile (Section 10, 11)
        comp_indicators = ComprehensiveIndicators.analyze_full_indicator_suite(df)
        base_indicators = TechnicalIndicators.get_latest_indicators(df)

        # 6. Momentum & Divergences (Section 11)
        divergence = DivergenceEngine.get_divergence_verdict(df)

        # 7. Timeframe Mode Alignment (Section 9)
        smc_summary = SmartMoneyConcepts.analyze_smc_structure(df)
        mode_alignment = TimeframeModeSelector.evaluate_mode_alignment(mode, base_indicators, smc_summary)

        # 8. Structural SL/TP Calculation (Section 13)
        atr = base_indicators.get("atr", current_price * 0.01)
        last_swing_low = structure.get("last_swing_low", current_price - atr * 1.5)
        last_swing_high = structure.get("last_swing_high", current_price + atr * 1.5)

        is_long = "BUY" in mode_alignment["setup_confluence"] or is_uptrend or "BULLISH" in divergence.get("bias", "")
        if is_long:
            sl_price = round(min(last_swing_low - (atr * 0.5), current_price - (atr * 1.5)), 2)
            tp_price = round(current_price + (abs(current_price - sl_price) * 2.5), 2)
            signal_action = "BUY" if "BULLISH" in mode_alignment["setup_confluence"] or "REVERSAL_UP" in divergence.get("bias", "") else "WAIT"
        else:
            sl_price = round(max(last_swing_high + (atr * 0.5), current_price + (atr * 1.5)), 2)
            tp_price = round(current_price - (abs(sl_price - current_price) * 2.5), 2)
            signal_action = "SELL" if "BEARISH" in mode_alignment["setup_confluence"] or "REVERSAL_DOWN" in divergence.get("bias", "") else "WAIT"

        # 9. Master Synthesis for NVIDIA LLM Brain
        full_technical_report = (
            f"=== 15-SECTION INSTITUTIONAL CHART REPORT FOR {symbol} ({market_type}) ===\n"
            f"Price: {current_price} | Timeframe: {timeframe} | Active Session: {ict_data.get('session_context', {}).get('active_killzone')}\n"
            f"1. Market Structure: {structure.get('trend')} ({structure.get('structure')}) | MSB: {structure.get('msb_signal')}\n"
            f"2. Chart Pattern: {price_action.get('primary_chart_pattern')} | Candlestick: {candlestick_intel.get('candlestick_verdict')} ({candlestick_intel.get('bias')})\n"
            f"3. Key Levels: PDH={key_levels.get('pdh')} | PDL={key_levels.get('pdl')} | VWAP={comp_indicators.get('vwap')}\n"
            f"4. Volume Profile POC: {comp_indicators.get('volume_profile', {}).get('poc')} | Volume Divergence: {comp_indicators.get('obv_divergence')}\n"
            f"5. ICT Liquidity Targets: BSL (Above)={ict_data.get('bsl_target_above')} | SSL (Below)={ict_data.get('ssl_target_below')}\n"
            f"6. Fibonacci OTE (0.618 - 0.786): {fibs.get('ote_zone_high')} to {fibs.get('ote_zone_low')}\n"
            f"7. Momentum Divergence: {divergence.get('divergence_signal')} ({divergence.get('bias')})\n"
            f"8. Indicators: EMA 9/21: {base_indicators.get('ema_9')}/{base_indicators.get('ema_21')} | Supertrend: {base_indicators.get('supertrend')} | RSI: {base_indicators.get('rsi')} | ADX: {comp_indicators.get('adx_trend_strength')}\n"
            f"Setup Confluence: {mode_alignment['setup_confluence']} (Confidence: {mode_alignment['confidence_score']})"
        )

        system_instruction = (
            "You are a 25-year Wall Street Veteran Technical Quant Trader.\n"
            "Review the 15-section technical analysis report.\n"
            "Output a crisp 2-sentence institutional synthesis stating:\n"
            "1. Core price action driver (Structure + Liquidity + Divergence)\n"
            "2. High-conviction execution action (BUY, SELL, or WAIT) with strict invalidation."
        )

        llm_thought = self.brain.complete(full_technical_report, system_prompt=system_instruction)

        # Empirical Historical Pattern Scan across past candles
        active_pat = price_action.get("primary_chart_pattern") or candlestick_intel.get("candlestick_verdict", "ENGULFING")
        pattern_edge = HistoricalPatternMatcher.analyze_pattern_historical_edge(
            df=df,
            pattern_name=active_pat,
            market=market_type,
            expected_direction="BULLISH" if signal_action == "BUY" else ("BEARISH" if signal_action == "SELL" else "BULLISH"),
            forward_bars=10
        )

        # 10. Depth 2/3 Institutional Trap & Liquidity Sweep Audit
        proposed_dir = "LONG" if signal_action == "BUY" else ("SHORT" if signal_action == "SELL" else "LONG")
        trap_audit = self.trap_detector.audit_trade_proposal_against_traps(
            df=df,
            market=market_type,
            symbol=symbol,
            direction=proposed_dir
        )

        # 11. Multi-Timeframe (HTF) Fractal Trend Lock & TTM Volatility Squeeze
        df_htf = pd.DataFrame()
        try:
            # Fetch 1H or 4H higher timeframe candles
            df_htf = self.feed.get_market_data(market_type, symbol, interval="1h")
        except Exception:
            pass

        fractal_eval = FractalHTFEngine.evaluate_fractal_alignment(
            df_primary=df,
            df_htf=df_htf,
            proposed_direction=proposed_dir
        )

        # If trap detector vetoes trade, prevent suicide entries into retail traps
        if signal_action in ["BUY", "SELL"] and trap_audit.get("recommended_action") == "VETO_TRADE":
            logger.warning(f"[AnalyticalAgent] 🛑 Trap Detector VETO: Downgrading {signal_action} signal to WAIT due to {trap_audit.get('veto_reason')}")
            signal_action = "WAIT"

        # If HTF trend directly collides with proposed trade, lock out counter-trend suicide trades
        elif signal_action in ["BUY", "SELL"] and fractal_eval.get("htf_collision"):
            logger.warning(f"[AnalyticalAgent] 🛑 Fractal HTF Collision VETO: Downgrading {signal_action} signal to WAIT due to {fractal_eval.get('veto_reason')}")
            signal_action = "WAIT"

        result = {
            "symbol": symbol,
            "market": market_type,
            "timeframe": timeframe,
            "current_price": current_price,
            "signal": signal_action,
            "trap_analysis": trap_audit,
            "fractal_alignment": fractal_eval,
            "market_structure": structure.get("trend"),
            "structure_details": structure.get("structure"),
            "chart_pattern": price_action.get("primary_chart_pattern"),
            "candlestick_pattern": candlestick_intel.get("candlestick_verdict"),
            "candlestick_bias": candlestick_intel.get("bias"),
            "historical_pattern_edge": pattern_edge,
            "divergence_signal": divergence.get("divergence_signal"),
            "ict_bsl_target": ict_data.get("bsl_target_above"),
            "ict_ssl_target": ict_data.get("ssl_target_below"),
            "session_killzone": ict_data.get("session_context", {}).get("active_killzone"),
            "power_of_3_phase": ict_data.get("session_context", {}).get("power_of_3_phase"),
            "volume_poc": comp_indicators.get("volume_profile", {}).get("poc"),
            "vwap": comp_indicators.get("vwap"),
            "adx_trend": comp_indicators.get("adx_trend_strength"),
            "fib_ote_zone": f"{fibs.get('ote_zone_high')} - {fibs.get('ote_zone_low')}",
            "suggested_entry": current_price,
            "suggested_sl": sl_price,
            "suggested_tp": tp_price,
            "risk_reward": "1:2.5",
            "confluence": mode_alignment["setup_confluence"],
            "confidence": mode_alignment["confidence_score"],
            "llm_chart_analysis": llm_thought.strip(),
            "full_technical_snapshot": {
                "key_levels": key_levels,
                "fibonacci": fibs,
                "supply_demand_zones": sd_zones,
                "ict": ict_data,
                "indicators": base_indicators,
                "volume_profile": comp_indicators.get("volume_profile")
            }
        }

        self.latest_analysis = result
        return result


if __name__ == "__main__":
    agent = MarketAnalyticalAgent()
    print("Testing 15-Section Market Analytical Agent on BTC...")
    res = agent.analyze_asset("CRYPTO", "BTC", timeframe="15m", mode="SWING_TRADING")
    print(f"\n========================================================")
    print(f"  ASSET: {res['symbol']} | PRICE: ${res['current_price']} | SIGNAL: {res['signal']}")
    print(f"========================================================")
    print(f"Market Structure: {res['market_structure']} ({res['structure_details']})")
    print(f"Chart Pattern: {res['chart_pattern']} | Candlestick: {res['candlestick_pattern']}")
    print(f"ICT Liquidity: BSL=${res['ict_bsl_target']} | SSL=${res['ict_ssl_target']}")
    print(f"Active Killzone: {res['session_killzone']} (Phase: {res['power_of_3_phase']})")
    print(f"VWAP: ${res['vwap']} | Volume POC: ${res['volume_poc']} | ADX: {res['adx_trend']}")
    print(f"Fib OTE Zone (0.618 - 0.786): {res['fib_ote_zone']}")
    print(f"Divergence: {res['divergence_signal']}")
    print(f"Trade Execution: Entry: ${res['suggested_entry']} | SL: ${res['suggested_sl']} | TP: ${res['suggested_tp']} (RR: {res['risk_reward']})")
    print(f"\nLLM Veteran Synthesis:\n{res['llm_chart_analysis']}")
