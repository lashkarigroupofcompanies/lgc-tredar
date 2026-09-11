"""
Comprehensive Test Suite for OmniCalculator
===========================================
Validates:
1. Universal Percentage Engine (pct_change, pct_of, pct_value, cagr, compound, etc.)
2. Risk & Position Sizing Engine (units, R-multiple, R:R milestones, breakeven, liquidation, Kelly, RoR)
3. Quantitative & Statistical Engine (expectancy, profit factor, sharpe, sortino, max drawdown, VaR)
4. Technical & Market Geometry (Fibonacci levels, ATR stops, Camarilla/Standard pivots, FVG)
5. Safe Sandboxed Math Expression Evaluator (arbitrary math expressions, zero-division handling, syntax security)
6. Swarm Multi-Agent & Tactical Clone Concurrency (concurrent execution across agents and shadow clones)
"""

import sys
import os
import threading
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared_brain.omni_calculator import OmniCalculator
from shared_brain.shadow_clone_manager import ShadowCloneManager, ShadowCloneSquad
from agents.ceo_agent.agent import CEOAgent
from agents.core_agent.agent import CoreTradingAgent
from agents.risk_agent.agent import RiskManagementAgent
from agents.analytical_agent.agent import MarketAnalyticalAgent
from agents.strategy_rnd.agent import StrategyRndAgent
from agents.execution_agent.agent import ExecutionAgent
from agents.news_agent.agent import NewsIntelligenceAgent
from agents.evolution_memory.agent import EvolutionMemoryAgent


def test_percentages():
    print("\n--- 1. Testing Universal Percentage Engine ---")
    calc = OmniCalculator("TEST_PERCENTAGES")

    # Percentage change
    chg1 = calc.pct_change(100.0, 125.0)
    assert chg1 == 25.0, f"Expected 25.0, got {chg1}"
    chg2 = calc.pct_change(150.0, 120.0)
    assert chg2 == -20.0, f"Expected -20.0, got {chg2}"
    chg_zero = calc.pct_change(0.0, 50.0)
    assert chg_zero == 0.0, f"Zero division failed: {chg_zero}"

    # Percentage of
    p_of = calc.pct_of(25.0, 200.0)
    assert p_of == 12.5, f"Expected 12.5, got {p_of}"

    # Percentage value
    val = calc.pct_value(100000.0, 1.5)
    assert val == 1500.0, f"Expected 1500.0, got {val}"

    # Percentage difference
    diff = calc.pct_diff(100.0, 110.0)
    assert 9.5 < diff < 9.6, f"Expected ~9.52, got {diff}"

    # Percentage add & subtract
    p_add = calc.pct_add(100.0, 10.0)
    assert p_add == 110.0, f"Expected 110.0, got {p_add}"
    p_sub = calc.pct_subtract(100.0, 10.0)
    assert p_sub == 90.0, f"Expected 90.0, got {p_sub}"

    # Compound Growth & CAGR
    comp = calc.compound_growth(10000.0, 10.0, 3)
    assert comp == 13310.0, f"Expected 13310.0, got {comp}"
    cagr_val = calc.cagr(10000.0, 13310.0, 3)
    assert abs(cagr_val - 10.0) < 0.01, f"Expected 10.0%, got {cagr_val}"

    # Discount & Premium
    prem = calc.discount_premium_pct(105.0, 100.0)
    assert prem["status"] == "PREMIUM" and prem["pct"] == 5.0
    disc = calc.discount_premium_pct(92.0, 100.0)
    assert disc["status"] == "DISCOUNT" and disc["pct"] == 8.0

    # Net after drag
    drag = calc.net_after_drag(gross_pnl=1000.0, position_value=10000.0, fee_pct=0.1, slippage_pct=0.05)
    assert drag["total_drag"] == 15.0 and drag["net_pnl"] == 985.0

    print("✅ Percentage Engine passed all checks!")


def test_risk_and_sizing():
    print("\n--- 2. Testing Risk, Sizing & Trade Geometry ---")
    calc = OmniCalculator("TEST_RISK")

    # Position Size
    # Balance: $100,000, Risk: 1%, Entry: 150, Stop: 145 -> Risk Cash: $1000, Risk/Unit: $5 -> Units: 200
    pos = calc.position_size(account_balance=100000.0, risk_pct=1.0, entry_price=150.0, stop_loss_price=145.0)
    assert pos["risk_cash"] == 1000.0, f"Expected $1000 risk cash, got {pos['risk_cash']}"
    assert pos["units"] == 200.0, f"Expected 200 units, got {pos['units']}"
    assert pos["position_value"] == 30000.0, f"Expected $30,000 pos value, got {pos['position_value']}"

    # R-Multiple
    r_long = calc.r_multiple(entry=100.0, exit_price=120.0, stop_loss=90.0, direction="LONG")
    assert r_long == 2.0, f"Expected 2.0R, got {r_long}"
    r_loss = calc.r_multiple(entry=100.0, exit_price=90.0, stop_loss=90.0, direction="LONG")
    assert r_loss == -1.0, f"Expected -1.0R, got {r_loss}"
    r_short = calc.r_multiple(entry=100.0, exit_price=80.0, stop_loss=110.0, direction="SHORT")
    assert r_short == 2.0, f"Expected 2.0R on short, got {r_short}"

    # Targets from R:R
    targets = calc.targets_from_rr(entry=100.0, stop_loss=95.0, rr_ratios=[1.0, 2.0, 3.0], direction="LONG")
    assert targets["1.0R"] == 105.0 and targets["2.0R"] == 110.0 and targets["3.0R"] == 115.0

    # Breakeven with fees
    be = calc.breakeven_price(entry=100.0, units=50.0, total_commissions=10.0, direction="LONG")
    assert be == 100.2, f"Expected 100.2, got {be}"

    # Liquidation Price
    # Long at 100 with 10x leverage -> bankruptcy ~90.5 with 0.5% maint margin
    liq = calc.liquidation_price(entry=100.0, leverage=10.0, direction="LONG", maintenance_margin_pct=0.5)
    assert 90.0 <= liq <= 91.0, f"Expected ~90.5, got {liq}"

    # Kelly Criterion
    # Win rate 60%, Win/Loss ratio 2.0
    # Full Kelly = (0.60 * 3.0 - 1) / 2 = 0.8 / 2 = 0.40 (40%)
    # Half Kelly = 20% capped at 10%
    kelly = calc.kelly_criterion(win_rate_pct=60.0, win_loss_ratio=2.0, fraction="HALF", max_cap_pct=10.0)
    assert kelly["full_kelly_pct"] == 40.0
    assert kelly["recommended_pct"] == 10.0

    # Risk of Ruin
    ror = calc.risk_of_ruin(win_rate_pct=60.0, win_loss_ratio=2.0, risk_per_trade_pct=1.0)
    assert ror < 0.01, f"Expected near zero risk of ruin for strong edge, got {ror}%"

    print("✅ Risk & Sizing Engine passed all checks!")


def test_quant_and_stats():
    print("\n--- 3. Testing Quantitative, Statistical & Portfolio Metrics ---")
    calc = OmniCalculator("TEST_QUANT")

    # Expectancy: 60% win rate, avg win $300, avg loss $100
    # E = (0.6 * 300) - (0.4 * 100) = 180 - 40 = $140
    exp = calc.expectancy(win_rate_pct=60.0, avg_win=300.0, avg_loss=100.0)
    assert exp["expectancy"] == 140.0 and exp["expectancy_r"] == 1.4 and exp["positive_edge"] is True

    # Profit Factor
    pf = calc.profit_factor(gross_profit=4500.0, gross_loss=1500.0)
    assert pf == 3.0, f"Expected PF 3.0, got {pf}"

    # Summary Stats
    numbers = [10.0, 20.0, 30.0, 40.0, 50.0]
    stats = calc.summary_stats(numbers)
    assert stats["count"] == 5 and stats["mean"] == 30.0 and stats["median"] == 30.0 and stats["min"] == 10.0 and stats["max"] == 50.0

    # Max Drawdown
    equity = [100000.0, 105000.0, 110000.0, 99000.0, 108000.0, 115000.0]
    dd = calc.max_drawdown(equity)
    assert dd["peak"] == 110000.0 and dd["trough"] == 99000.0 and dd["max_dd_cash"] == 11000.0
    assert abs(dd["max_dd_pct"] - 10.0) < 0.01

    # Sharpe & Sortino
    returns = [0.02, 0.015, -0.005, 0.03, 0.01, 0.025, -0.002]
    sharpe = calc.sharpe_ratio(returns)
    sortino = calc.sortino_ratio(returns)
    assert sharpe > 0.0 and sortino > 0.0

    # Parametric VaR
    var = calc.parametric_var(portfolio_value=100000.0, mean_return_pct=0.05, std_dev_pct=1.5, confidence=0.99)
    assert var["var_cash"] > 0.0 and var["confidence_pct"] == 99.0

    print("✅ Quantitative & Statistical Metrics passed all checks!")


def test_market_geometry():
    print("\n--- 4. Testing Market Geometry & Technical Calculations ---")
    calc = OmniCalculator("TEST_GEOMETRY")

    # Fibonacci Retracement from 100 to 200 (Diff = 100)
    # Bullish: 0.618 Golden Pocket = 200 - (100 * 0.618) = 138.2
    fib = calc.fibonacci_levels(swing_low=100.0, swing_high=200.0, direction="BULLISH")
    assert fib["0.618_GOLDEN_POCKET"] == 138.2
    assert fib["0.500_EQ"] == 150.0
    assert fib["1.618_GOLDEN_EXT"] == 38.2  # Retracement extension down

    # ATR Stop
    stop_long = calc.atr_stop_distance(current_price=150.0, atr=2.5, multiplier=2.0, direction="LONG")
    assert stop_long == 145.0
    stop_short = calc.atr_stop_distance(current_price=150.0, atr=2.5, multiplier=2.0, direction="SHORT")
    assert stop_short == 155.0

    # Pivot Points Standard & Camarilla
    pivots = calc.pivot_points(high=105.0, low=95.0, close=100.0, method="STANDARD")
    assert pivots["PP"] == 100.0
    assert pivots["R1"] == 105.0
    assert pivots["S1"] == 95.0

    camarilla = calc.pivot_points(high=105.0, low=95.0, close=100.0, method="CAMARILLA")
    assert "H4" in camarilla and "L4" in camarilla

    # Fair Value Gap
    # Bullish: Bar 1 High 100, Bar 3 Low 104 -> Gap of 4 points, Midpoint 102
    fvg = calc.fair_value_gap(bar1_high=100.0, bar1_low=95.0, bar3_high=110.0, bar3_low=104.0, direction="BULLISH")
    assert fvg["fvg_active"] is True
    assert fvg["gap_size"] == 4.0
    assert fvg["consequent_encroachment_50pct"] == 102.0

    print("✅ Market Geometry passed all checks!")


def test_safe_expression_evaluator():
    print("\n--- 5. Testing Safe Sandboxed Math Expression Evaluator ---")
    calc = OmniCalculator("TEST_EXPR")

    # Standard arithmetic & variables
    res1 = calc.evaluate_expression("((245.50 - 240.00) / 240.00) * 100")
    assert abs(res1 - 2.2917) < 0.001

    res2 = calc.evaluate_expression("capital * risk / diff", variables={"capital": 100000.0, "risk": 0.01, "diff": 5.0})
    assert res2 == 200.0

    # Math functions
    res3 = calc.evaluate_expression("sqrt(256) + abs(-14) + min(10, 20)")
    assert res3 == 40.0

    # Zero-division safety
    res_zero = calc.evaluate_expression("100 / 0")
    assert res_zero == 0.0

    # Security sandbox: Attempt dangerous calls (must return 0.0 or handle safely, never execute)
    res_hack1 = calc.evaluate_expression("__import__('os').system('dir')")
    assert res_hack1 == 0.0

    res_hack2 = calc.evaluate_expression("open('server.py').read()")
    assert res_hack2 == 0.0

    print("✅ Safe Expression Evaluator passed all security and arithmetic checks!")


def test_concurrent_swarm_and_clones():
    print("\n--- 6. Testing Concurrent Swarm & Tactical Clone Concurrency ---")

    # Verify all agents possess their personal calculator
    ceo = CEOAgent()
    core = CoreTradingAgent()
    risk = RiskManagementAgent()
    analytical = MarketAnalyticalAgent()
    strategy = StrategyRndAgent()
    execution = ExecutionAgent()
    news = NewsIntelligenceAgent()
    evolution = EvolutionMemoryAgent()

    agents = [ceo, core, risk, analytical, strategy, execution, news, evolution]
    for agent in agents:
        assert hasattr(agent, "calc"), f"{agent.__class__.__name__} is missing self.calc!"
        assert isinstance(agent.calc, OmniCalculator), f"{agent.__class__.__name__}.calc is not OmniCalculator!"
        assert agent.calc.owner != "SYSTEM", f"{agent.__class__.__name__} owner should be specific!"

    # Spawn ANY number of Shadow Clones dynamically across world markets (scalable to any count)
    clone_mgr = ShadowCloneManager(max_concurrent_clones=100)
    clone_specs = [
        ("CRYPTO", "BTC", "LIQUIDATION_SWEEP"),
        ("CRYPTO", "ETH", "ORDER_BLOCK"),
        ("US_STOCKS", "NVDA", "OPENING_RANGE_BREAKOUT"),
        ("US_STOCKS", "AAPL", "FVG_FILL"),
        ("INDIAN_STOCKS", "RELIANCE", "SMC_ORDER_BLOCK"),
        ("INDIAN_STOCKS", "TCS", "PIVOT_REVERSAL"),
        ("UK_STOCKS", "BP", "LONDON_OPEN_BREAKOUT"),
        ("EU_STOCKS", "SAP", "TREND_CHANNEL"),
        ("ASIAN_STOCKS", "7203.T", "MEAN_REVERSION"),
        ("FOREX", "EURUSD", "LONDON_NY_OVERLAP"),
        ("COMMODITIES", "GOLD", "MOMENTUM_SURGE"),
        ("COMMODITIES", "CRUDE_OIL", "BREAKOUT_EXPANSION"),
    ]

    clones: List[ShadowCloneSquad] = []
    for mkt, sym, strat in clone_specs:
        squad = clone_mgr.spawn_clone_squad(mkt, sym, strat)
        if squad is not None:
            clones.append(squad)

    for c in clones:
        assert hasattr(c, "calc")
        assert c.calc.owner.startswith("CLONE_")

    print(f"Verified 8 Master Agents and {len(clones)} Tactical Shadow Clones across all world markets each possess a personal OmniCalculator.")

    # Run heavy multithreaded calculation barrage across all agents and clones
    results = {}
    threads = []

    def worker(entity_name, calc_inst):
        thread_results = []
        for i in range(100):
            # Do percentages
            pct = calc_inst.pct_change(100.0 + i, 120.0 + (i * 1.5))
            # Do sizing
            sz = calc_inst.position_size(100000.0, 1.0, 200.0 + i, 195.0 + i)
            # Do R-multiple
            r = calc_inst.r_multiple(100.0, 115.0, 95.0)
            # Do eval expression
            expr_val = calc_inst.evaluate_expression(f"sqrt({100 + i}) * 2.5")
            thread_results.append((pct, sz["units"], r, expr_val))
        results[entity_name] = thread_results

    # Spawn threads for all 8 agents + 12 clones + clone manager (21 parallel entities!)
    all_calcs: List[Tuple[str, OmniCalculator]] = []
    for a in agents:
        all_calcs.append((a.__class__.__name__, a.calc))
    for c in clones:
        all_calcs.append((f"CLONE_{c.clone_id}", c.calc))
    all_calcs.append(("CloneManager", clone_mgr.calc))

    start_time = time.time()
    for name, c_inst in all_calcs:
        t = threading.Thread(target=worker, args=(name, c_inst))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    duration = time.time() - start_time

    # Verify all threads finished
    assert len(results) == len(all_calcs), "Not all threads reported results!"
    for name, res in results.items():
        assert len(res) == 100, f"{name} had incomplete calculations!"

    total_calcs = sum(c_inst.calculation_count for _, c_inst in all_calcs)
    print(f"⚡ Concurrent Barrage Complete: {total_calcs} calculations across {len(all_calcs)} parallel entities in {duration*1000:.2f}ms!")
    print("✅ All Swarm & Clone concurrency tests PASSED!")


if __name__ == "__main__":
    test_percentages()
    test_risk_and_sizing()
    test_quant_and_stats()
    test_market_geometry()
    test_safe_expression_evaluator()
    test_concurrent_swarm_and_clones()
    print("\n==================================================================")
    print("  🏆 ALL OMNICALCULATOR INTEGRATION & CONCURRENCY TESTS PASSED!   ")
    print("==================================================================")
