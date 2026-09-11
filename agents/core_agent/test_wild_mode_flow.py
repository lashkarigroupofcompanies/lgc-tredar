"""
Verification Test for Wild Mode Engine:
Tests the autonomous trading pipeline in both:
1. CONSERVATIVE_SAFE Mode (Strict safety, calm charts, 15m scan, 1.5R breakeven)
2. WILD_MODE (Explosive momentum universe, high ATR reward, news fuel requirement, 5m scan, 0.75% max risk clamp, 1.0R fast breakeven lock)
"""
import sys
import os
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from typing import Dict, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.core_agent.agent import CoreTradingAgent
from agents.analytical_agent.agent import MarketAnalyticalAgent

def run_screener_comparison():
    print("=" * 80)
    print("🔥 STEP 1: COMPARING CONSERVATIVE VS. WILD MODE SCREENER")
    print("=" * 80)
    analytical_agent = MarketAnalyticalAgent()

    # 1. Conservative Mode on US_STOCKS
    print("\n--- [CONSERVATIVE_SAFE Mode on US_STOCKS] ---")
    safe_result = analytical_agent.screen_and_select_best_chart(
        market="US_STOCKS",
        news_bias="BULLISH",
        timeframe="15m",
        mode="CONSERVATIVE_SAFE"
    )
    all_safe = safe_result.get("all_screened_charts", [])
    print(f"Total charts evaluated: {len(all_safe)}")
    print(f"Accepted safe charts: {safe_result.get('qualified_count')}")
    print(f"Rejected unpredictable charts: {safe_result.get('rejected_count')}")
    best_safe = safe_result['best_chart']
    print(f"👑 Top Safe Chart Selected: {best_safe['symbol']} (Score: {best_safe['safety_score']}/100 | Status: {best_safe['status']})")
    print(f"   ATR%: {best_safe.get('atr_pct', 0.0):.2f}% | Volatility Status: {best_safe.get('volatility_status')}")

    # 2. Wild Mode on US_STOCKS
    print("\n--- [WILD_MODE on US_STOCKS] (High Volatility Intraday Alpha) ---")
    wild_result = analytical_agent.screen_and_select_best_chart(
        market="US_STOCKS",
        news_bias="BULLISH",
        timeframe="5m",
        mode="WILD_MODE"
    )
    all_wild = wild_result.get("all_screened_charts", [])
    print(f"Total charts evaluated: {len(all_wild)}")
    print(f"Wild tradeable charts: {wild_result.get('qualified_count')}")
    print(f"Rejected charts: {wild_result.get('rejected_count')}")
    best_wild = wild_result['best_chart']
    print(f"🚀 Top Explosive Chart Selected: {best_wild['symbol']} (Score: {best_wild['safety_score']}/100 | Status: {best_wild['status']})")
    print(f"   ATR%: {best_wild.get('atr_pct', 0.0):.2f}% | Volatility Status: {best_wild.get('volatility_status')} | Trend: {best_wild.get('trend_clarity')}")

    # 3. Wild Mode on CRYPTO
    print("\n--- [WILD_MODE on CRYPTO] (High Volatility Intraday Alpha) ---")
    crypto_wild = analytical_agent.screen_and_select_best_chart(
        market="CRYPTO",
        news_bias="BULLISH",
        timeframe="5m",
        mode="WILD_MODE"
    )
    best_crypto = crypto_wild['best_chart']
    print(f"🚀 Top Crypto Wild Chart: {best_crypto['symbol']} (Score: {best_crypto['safety_score']}/100 | Status: {best_crypto['status']})")
    print(f"   ATR%: {best_crypto.get('atr_pct', 0.0):.2f}% | Volatility Status: {best_crypto.get('volatility_status')}")


def run_core_agent_wild_cycle():
    print("\n" + "=" * 80)
    print("🔥 STEP 2: RUNNING AUTONOMOUS CORE AGENT CYCLE IN WILD MODE")
    print("=" * 80)
    agent = CoreTradingAgent()
    agent.set_market("US_STOCKS")

    # Engage Wild Mode
    agent.set_trading_mode("WILD_MODE")

    print(f"Agent Trading Mode: {agent.trading_mode}")
    print(f"CEO Mandate: {agent.ceo_agent.active_mandate}")

    # Run single cycle
    cycle_result = agent.run_single_cycle()

    screener_data: Dict[str, Any] = dict(agent.system_state.get("screener_report") or {})
    best_chart: Dict[str, Any] = dict(screener_data.get("best_chart") or {})
    risk_report: Dict[str, Any] = dict(agent.system_state.get("latest_risk_verdict") or {})
    exec_status = cycle_result.get("execution_status", "NO_ACTION")

    risk_pct_raw = risk_report.get("risk_pct")
    risk_pct_val: float = float(risk_pct_raw) if risk_pct_raw is not None else 0.0
    be_raw = risk_report.get("breakeven_trigger_r")
    be_val: float = float(be_raw) if be_raw is not None else 0.0
    hold_raw = risk_report.get("max_hold_bars")
    hold_val: int = int(hold_raw) if hold_raw is not None else 0

    print("\n" + "=" * 80)
    print("🎯 WILD MODE CYCLE AUDIT RESULTS:")
    print("=" * 80)
    print(f"1. Chart Selected: {best_chart.get('symbol', 'N/A')} ({best_chart.get('market', 'N/A')})")
    print(f"   Status: {best_chart.get('status', 'N/A')} | Score: {best_chart.get('safety_score', 0)}/100")
    print(f"   ATR%: {best_chart.get('atr_pct', 0.0):.2f}% | Vol Status: {best_chart.get('volatility_status', 'N/A')}")
    print("2. Risk Management Shield in Wild Mode:")
    print(f"   Decision: {risk_report.get('decision', 'UNKNOWN')}")
    if risk_report.get("decision") == "APPROVED":
        print(f"   Risk % Allocated: {risk_pct_raw}% (Max 0.75% Defense Clamp: {'PASS' if risk_pct_val <= 0.75 else 'FAIL'})")
        print(f"   Breakeven Trigger R: {be_raw}R (Fast Breakeven: {'PASS' if be_val == 1.0 else 'FAIL'})")
        print(f"   Max Hold Bars: {hold_raw} bars")
    else:
        print(f"   Audit Outcome: REJECTED by Risk Shield ({risk_report.get('reason', 'Capital Protection Gate')})")
        print("   (Note: Step 3 performs the side-by-side approved audit testing the 0.75% clamp and 1.0R trigger)")
    print(f"3. Order Execution Status: {exec_status}")

    assert agent.trading_mode == "WILD_MODE", "Trading mode must be WILD_MODE"
    if risk_report.get("decision") == "APPROVED":
        assert risk_pct_val <= 0.75, "Wild mode risk must be clamped to <= 0.75%"
        assert be_val == 1.0, "Wild mode breakeven trigger must be 1.0R"
        assert hold_val == 12, "Wild mode max hold bars must be 12"

    print("\n✅ WILD MODE CYCLE COMPLETED SUCCESSFULLY!")

def run_direct_risk_comparison():
    print("\n" + "=" * 80)
    print("🛡️ STEP 3: DIRECT 15-SECTION RISK AGENT AUDIT (CONSERVATIVE VS WILD MODE)")
    print("=" * 80)
    from agents.risk_agent.agent import RiskManagementAgent
    risk_agent = RiskManagementAgent(account_balance=100000.0)

    proposal_base = {
        "symbol": "TSLA",
        "strategy_name": "SMC_ORDER_BLOCK_RETEST",
        "direction": "LONG",
        "entry_price": 250.0,
        "stop_loss": 245.0,        # 2% stop ($5 risk)
        "take_profit_1": 260.0,    # 2.0R
        "take_profit_2": 270.0,    # 4.0R
        "triple_historical_index": 78.5,
        "setup_score": 8.5,
        "win_rate_estimate": 0.62
    }

    # 1. Conservative Safe Audit
    prop_safe = dict(proposal_base, is_wild_mode=False)
    verdict_safe = risk_agent.evaluate_trade_proposal(prop_safe, open_positions=[])

    # 2. Wild Mode High Defense Audit
    prop_wild = dict(proposal_base, is_wild_mode=True)
    verdict_wild = risk_agent.evaluate_trade_proposal(prop_wild, open_positions=[])

    print(f"--- [CONSERVATIVE MODE RISK AUDIT] ---")
    print(f"Decision: {verdict_safe['decision']} | Risk Tier: {verdict_safe['risk_tier']}")
    print(f"Risk Allocated: {verdict_safe['risk_pct']}% | Dollar Risk: ${verdict_safe['dollar_risk']:,.2f}")
    print(f"Breakeven Trigger R: {verdict_safe['breakeven_trigger_r']}R | Max Hold Bars: {verdict_safe['max_hold_bars']}")

    print(f"\n--- [WILD MODE HIGH-DEFENSE RISK AUDIT] ---")
    print(f"Decision: {verdict_wild['decision']} | Risk Tier: {verdict_wild['risk_tier']}")
    print(f"Risk Allocated: {verdict_wild['risk_pct']}% | Dollar Risk: ${verdict_wild['dollar_risk']:,.2f}")
    print(f"Breakeven Trigger R: {verdict_wild['breakeven_trigger_r']}R | Max Hold Bars: {verdict_wild['max_hold_bars']}")

    # Assertions proving high-defense behavior
    assert verdict_wild["decision"] == "APPROVED"
    assert verdict_wild["risk_pct"] <= 0.75, f"Expected risk <= 0.75%, got {verdict_wild['risk_pct']}%"
    assert verdict_wild["breakeven_trigger_r"] == 1.0, f"Expected BE trigger 1.0R, got {verdict_wild['breakeven_trigger_r']}"
    assert verdict_wild["max_hold_bars"] == 12, f"Expected max hold 12 bars, got {verdict_wild['max_hold_bars']}"
    assert verdict_safe["breakeven_trigger_r"] == 1.5, f"Expected safe BE trigger 1.5R, got {verdict_safe['breakeven_trigger_r']}"

    print("\n✅ RISK AGENT WILD-MODE CLAMP & FAST BREAKEVEN VERIFIED 100% CORRECT!")

if __name__ == "__main__":
    run_screener_comparison()
    run_core_agent_wild_cycle()
    run_direct_risk_comparison()
