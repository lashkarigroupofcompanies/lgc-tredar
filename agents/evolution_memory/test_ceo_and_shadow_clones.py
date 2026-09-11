import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.ceo_agent.agent import CEOAgent
from shared_brain.shadow_clone_manager import ShadowCloneManager
from agents.core_agent.agent import CoreTradingAgent

def test_ceo_and_shadow_clones():
    print("=================================================================")
    print("   TESTING CEO SUPREME KING AGENT & SHADOW CLONE JUTSU ENGINE   ")
    print("=================================================================")

    # 1. Test CEO Supreme King Agent
    print("\n--- 1. Testing CEO Supreme King Agent ---")
    ceo = CEOAgent()

    # Test arbitration on conflicting signals
    arbitration = ceo.arbitrate_agent_conflicts(
        news_bias="EXTREME_BULLISH",
        analytical_signal="STRONG_SELL",
        strategy_action="EXECUTE",
        risk_decision="APPROVED",
        market="CRYPTO"
    )
    print("Arbitration Verdict (Macro vs Chart Contradiction):", arbitration["arbitration_verdict"])
    print("CEO Ruling:", arbitration["ceo_ruling"])
    assert arbitration["has_conflicts"] is True, "Expected conflict to be identified"

    # Test supreme approval / veto
    veto_test = ceo.grant_supreme_approval(
        market="CRYPTO",
        symbol="BTC",
        direction="LONG",
        strategy_decision={"recommended_action": "EXECUTE"},
        risk_verdict={"decision": "REJECTED", "reason": "Exceeded max drawdown"},
        arbitration=arbitration
    )
    print(f"CEO Approval Check on Risk Rejection -> Decision: {veto_test['ceo_decision']} | Mandate: {veto_test['mandate']}")
    assert veto_test["ceo_decision"] == "VETOED", "CEO must uphold risk shield rejection"
    assert veto_test["approved_for_execution"] is False

    # Test user emergency override
    override_res = ceo.emergency_override("PAUSE", "User clicked pause button")
    print("Emergency Override PAUSE:", override_res["message"])
    assert ceo.user_override_active is True

    ceo.emergency_override("RESUME", "User clicked resume button")
    assert ceo.user_override_active is False
    print("Emergency Override RESUME successful!")

    # 2. Test Naruto Shadow Clone Jutsu (Multi-Market Concurrency & Merge Jutsu)
    print("\n--- 2. Testing Naruto Shadow Clone Jutsu ---")
    manager = ShadowCloneManager()

    # Spawn Clone 1 in Crypto and Clone 2 in US Stocks
    clone_crypto = manager.spawn_clone_squad(
        market="CRYPTO",
        symbol="BTC",
        strategy_name="LIQUIDATION_WICK_SWEEP",
        allocated_capital=25000.0
    )
    clone_us = manager.spawn_clone_squad(
        market="US_STOCKS",
        symbol="NVDA",
        strategy_name="OPENING_RANGE_BREAKOUT",
        allocated_capital=25000.0
    )

    assert clone_crypto is not None, "Failed to spawn Crypto clone"
    assert clone_us is not None, "Failed to spawn US Stocks clone"
    print(f"Successfully spawned Clone Squad 1: {clone_crypto.clone_id} ({clone_crypto.market}:{clone_crypto.symbol})")
    print(f"Successfully spawned Clone Squad 2: {clone_us.clone_id} ({clone_us.market}:{clone_us.symbol})")

    # Activate trades in both clones
    clone_crypto.activate_clone_trade(
        trade_id="TRD_BTC_001",
        direction="LONG",
        entry_price=65000.0,
        stop_loss=64000.0,
        target_price=68000.0,
        units=0.38,
        dollar_risk=380.0
    )

    clone_us.activate_clone_trade(
        trade_id="TRD_NVDA_002",
        direction="LONG",
        entry_price=120.0,
        stop_loss=116.0,
        target_price=132.0,
        units=50.0,
        dollar_risk=200.0
    )

    # Verify short-term memory isolation (Clone 1 memory must NOT see Clone 2 position)
    snap1 = clone_crypto.live_memory.get_live_trade_snapshot()
    snap2 = clone_us.live_memory.get_live_trade_snapshot()
    assert snap1["live_position"]["symbol"] == "BTC", "Clone 1 must track BTC"
    assert snap2["live_position"]["symbol"] == "NVDA", "Clone 2 must track NVDA"
    print("Verified 100% Short-Term Memory Isolation between concurrent clones!")

    # Tick both clones simultaneously across markets
    market_ticks = {
        "CRYPTO:BTC": {"price": 66500.0, "high": 66600.0, "low": 64900.0},
        "US_STOCKS:NVDA": {"price": 124.0, "high": 124.5, "low": 119.8}
    }
    tick_results = manager.tick_all_active_clones(market_ticks)
    print(f"Concurrent Tick Executed across {len(tick_results)} clones.")
    for r in tick_results:
        print(f"  Clone [{r['clone_id']} {r['symbol']}]: PnL: ${r['unrealized_pnl']:.2f} | {r['unrealized_r']:.2f}R | Bars: #{r['bars_held']}")

    # 3. Test The Merge Jutsu: Disperse Clone and Consolidate into Central Mem0
    print("\n--- 3. Testing Merge Jutsu (Dispersal & Mem0 Absorption) ---")
    mem0_before_count = len(manager.mem0.memory_store.get("episodic_trade_records", []))
    
    # Merge Crypto Clone with Profit
    merged_record = clone_crypto.merge_jutsu(
        exit_reason="Take Profit target reached at higher high",
        exit_price=67500.0
    )
    print(f"Merge Jutsu Executed for {merged_record['clone_id']}! Status: {clone_crypto.status}")
    print(f"Realized PnL: ${merged_record['realized_pnl']:,.2f} ({merged_record['r_multiple']:.2f}R)")
    assert clone_crypto.status == "DISPERSED", "Clone status must be DISPERSED after merge jutsu"

    # Verify Central Mem0 absorbed the clone's experience
    mem0_after_count = len(manager.mem0.memory_store.get("episodic_trade_records", []))
    assert mem0_after_count > mem0_before_count, "Central Mem0 must contain the newly absorbed clone record"
    print(f"Verified Central Mem0 Absorption: Episodic records updated from {mem0_before_count} to {mem0_after_count}!")

    # 4. Test Core Engine Cycle with CEO and Shadow Clone Manager
    print("\n--- 4. Testing Full Core Trading Cycle with CEO & Clones ---")
    core = CoreTradingAgent()
    res = core.run_single_cycle()
    print(f"Core Cycle #{res['cycle']} completed!")
    print(f"  CEO Decision: {res.get('ceo_decision')} | Mandate: {res.get('ceo_mandate')}")
    print(f"  Active Shadow Clones Count: {res.get('active_clones_count')}")

    # Clean up test clones
    manager.kill_all_clones(reason="Test Suite Complete")

    print("\n=================================================================")
    print("   ALL CEO & SHADOW CLONE JUTSU TESTS PASSED WITH 100% SUCCESS!  ")
    print("=================================================================")

if __name__ == "__main__":
    test_ceo_and_shadow_clones()
