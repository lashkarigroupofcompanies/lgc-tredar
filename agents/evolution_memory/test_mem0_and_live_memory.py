import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from shared_brain.live_trade_working_memory import LiveTradeWorkingMemory
from agents.evolution_memory.mem0_memory_engine import Mem0MemoryEngine
from agents.evolution_memory.market_memory_matrix import MarketMemoryMatrix

def test_mem0_and_live_memory():
    print("=== 1. Testing Mem0 Long-Term Memory Engine ===")
    test_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/test_mem0.json"))
    if os.path.exists(test_db):
        os.remove(test_db)
        
    mem0 = Mem0MemoryEngine(store_path=test_db)
    mem0.record_episodic_trade({
        "trade_id": "TEST_001",
        "symbol": "RELIANCE.NS",
        "market": "INDIAN_STOCKS",
        "direction": "LONG",
        "strategy": "VWAP_MEAN_REVERSION",
        "exit_type": "STOP_LOSS",
        "realized_pnl": -1200.0,
        "r_multiple": -1.0,
        "exit_reason": "High volatility gap down during opening 15m",
        "market_regime": "HIGH_VOLATILITY"
    })
    
    results = mem0.search_memories("INDIAN_STOCKS VWAP_MEAN_REVERSION")
    print(f"Mem0 Search Results: {len(results)} items found")
    assert len(results) > 0, "Expected at least 1 memory match"
    
    constraints = mem0.get_all_negative_constraints()
    print(f"Negative constraints generated: {len(constraints)}")
    assert len(constraints) > 0, "Expected negative constraint from stop loss trade"

    print("\n=== 2. Testing Short-Term Live Trade Working Memory ===")
    live_mem = LiveTradeWorkingMemory()
    live_mem.activate_trade({
        "trade_id": "TRD_LIVE_99",
        "symbol": "BTC/USDT",
        "direction": "LONG",
        "strategy_name": "ICT_ORDER_BLOCK",
        "entry_price": 65000.0,
        "stop_loss": 64200.0,
        "initial_units": 0.5,
        "dollar_risk": 400.0,
        "market": "CRYPTO"
    })
    
    live_mem.post_analytical_live_update(
        rejection_wick=True,
        micro_choch=False,
        volume_surge=False,
        structure_state="BULLISH_ORDER_BLOCK_HOLD",
        notes="OB holding strong at 64,800. Single minor wick against, bullish continuation intact."
    )
    live_mem.post_inter_agent_message(
        from_agent="AnalyticalAgent",
        to_agent="StrategyAgent",
        message="OB holding strong at 64,800. Single minor wick against, bullish continuation intact.",
        priority="NORMAL"
    )

    live_mem.update_live_position_tick(
        current_price=66200.0,
        bars_held=3,
        unrealized_pnl=600.0,
        unrealized_r=1.5,
        stop_loss=65000.0,
        sl_state="BREAKEVEN",
        mae_price=64950.0,
        mfe_price=66300.0
    )
    live_mem.post_risk_live_update(
        risk_stance="BREAKEVEN_ARMED",
        trailing_stop_action="LOCK_BE",
        be_locked=True,
        notes="Risk-free runner active. Capital fully protected."
    )
    live_mem.post_inter_agent_message(
        from_agent="RiskShield",
        to_agent="ALL_AGENTS",
        message="Trade at +1.5R. SL moved to Break-Even (65,000.0). Capital fully protected.",
        priority="CRITICAL"
    )

    snapshot = live_mem.get_live_trade_snapshot()
    pos = snapshot["live_position"]
    print(f"Live Snapshot R-Multiple: {pos['unrealized_r']:.2f}R | Current Price: ${pos['current_price']}")
    print(f"Tactical Chat Events: {len(snapshot['inter_agent_feed'])}")
    assert pos["unrealized_r"] == 1.5, f"Expected 1.5R, got {pos['unrealized_r']}"
    assert len(snapshot["inter_agent_feed"]) >= 3, "Expected system + analytical + risk chat entries"

    # Test trade closure and archive
    live_mem.close_and_archive_trade({
        "trade_id": "TRD_LIVE_99",
        "symbol": "BTC/USDT",
        "market": "CRYPTO",
        "realized_pnl": 750.0,
        "r_multiple": 1.88,
        "exit_reason": "Target bank at higher high",
        "exit_type": "TAKE_PROFIT"
    })
    print("Archived trade. Live working memory is_trade_active:", live_mem.is_trade_active)
    assert not live_mem.is_trade_active, "Live working memory should be inactive after trade close"

    print("\n=== 3. Testing Global Market Affinity Matrix ===")
    matrix = MarketMemoryMatrix()
    all_markets = ["US_STOCKS", "INDIAN_STOCKS", "UK_STOCKS", "EU_STOCKS", "ASIAN_STOCKS", "FOREX", "COMMODITIES", "CRYPTO"]
    for m in all_markets:
        top_strats = matrix.get_top_strategies_for_market(m)
        strat_names = [s["name"] for s in top_strats[:2]]
        print(f"[{m}] Top Strats: {strat_names}")

    print("\n=== ALL TEST CHECKS PASSED PERFECTLY! ===")
    if os.path.exists(test_db):
        os.remove(test_db)

if __name__ == "__main__":
    test_mem0_and_live_memory()
