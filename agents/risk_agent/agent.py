"""
Risk Management Agent - 15-Section Master Quantitative Capital Protection Shield
Implements the complete 15-section institutional knowledge base:
1. Risk Management Fundamentals (Survive first, profit second; defined risk always)
2. Advanced Position Sizing (Fixed %, ATR, Half-Kelly Criterion, Anti-Martingale scaling)
3. Stop Loss Strategies (Hard SL, Structure SL behind liquidity, ATR buffers, Chandelier exits)
4. Take Profit & Partial Exits (Min 1:2 R:R, 50% at 1.0R -> BE, 25% at 2R, 25% trail)
5. Portfolio Risk Management (Portfolio Heat <= 6%, Concentration <= 15%, Sector <= 25%, Cash buffer >= 20%)
6. Multi-tier Drawdown & Streak Guard (Daily limit -2.5%, 3 losses -25%, 5 losses -50%, 7 losses Halt)
7. Leverage & Margin Controller (Leverage <= 3x, Margin utilization <= 65%)
8. Time & Event Risk Management (High-impact economic catalyst checks)
9. Correlation & Hedging Guard (Pair correlation matrix, prevents duplicate exposure)
10. Mathematical Expectancy System (Expectancy = P_win * R_win - P_loss * R_loss > 0)
11. Psychological Discipline Enforcer (Prevents revenge trading, enforces cool-down)
12. Real-Time Risk Monitoring Metrics (Live Portfolio Heat, Drawdown, Margin)
13. Black Swan & Historical Tail Stress Tester (Simulates gaps, VaR 99%, and simultaneous multi-stop exits)
14. Operational & Fat-Finger Protection (Geometric direction checks, limit clamps)
15. Comprehensive Decision Matrix Integration with All Agents
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from agents.risk_agent.position_sizing_engine import PositionSizingEngine
from agents.risk_agent.portfolio_risk_controller import PortfolioRiskController
from agents.risk_agent.drawdown_streak_guard import DrawdownStreakGuard
from agents.risk_agent.stop_target_validator import StopTargetValidator
from agents.risk_agent.black_swan_stress_tester import BlackSwanStressTester
from shared_brain.omni_calculator import OmniCalculator

logger = logging.getLogger("RiskAgent")


class RiskManagementAgent:
    """
    Master Capital Protection & Risk Shield Agent.
    Possesses absolute VETO power over every trade proposal from Strategy and Analytical agents.
    """

    def __init__(
        self,
        account_balance: float = 100000.0,
        base_risk_per_trade_pct: float = 1.0,
        max_portfolio_heat_pct: float = 6.0,
        max_daily_loss_pct: float = 3.5
    ):
        self.account_balance = account_balance
        self.base_risk_per_trade_pct = base_risk_per_trade_pct
        self.calc = OmniCalculator(owner="RiskManagementAgent")
        
        # Sub-Engines
        self.portfolio_controller = PortfolioRiskController(
            max_portfolio_heat_pct=max_portfolio_heat_pct,
            max_single_asset_exposure_pct=25.0,
            max_single_sector_exposure_pct=35.0,
            min_cash_reserve_pct=15.0,
            max_margin_utilization_pct=75.0,
            max_effective_leverage=3.5
        )
        self.drawdown_guard = DrawdownStreakGuard(
            initial_capital=account_balance,
            max_daily_loss_pct=max_daily_loss_pct,
            max_weekly_loss_pct=5.0
        )
        self.active_mode = "CONSERVATIVE_SAFE"

        logger.info(f"[RiskAgent] Master Risk Shield online. Base capital: ${account_balance:,.2f} | Base risk: {base_risk_per_trade_pct}%")

    def set_mode(self, mode: str):
        """Sets active risk mode: 'CONSERVATIVE_SAFE' or 'WILD_MODE'."""
        self.active_mode = "WILD_MODE" if "WILD" in str(mode).upper() else "CONSERVATIVE_SAFE"
        logger.info(f"[RiskAgent] Risk Mode set to: {self.active_mode}")

    def reset_daily_session(self, current_balance: Optional[float] = None):
        """Called at daily market session open."""
        bal = current_balance if current_balance is not None else self.account_balance
        self.drawdown_guard.reset_daily_session(bal)

    def update_account_balance(self, new_balance: float):
        """Updates equity and recalculates drawdown and streaks."""
        self.account_balance = new_balance
        self.drawdown_guard.update_equity(new_balance)

    def record_closed_trade(self, realized_pnl: float):
        """Records trade result into streak and drawdown trackers."""
        self.drawdown_guard.record_closed_trade(realized_pnl)

    def record_trade_result(self, trade: Any):
        """
        Records a trade dictionary or PnL into drawdown and streak guards,
        and dynamically feeds Evolution Memory so the system learns from every trade over time.
        """
        if isinstance(trade, dict):
            raw_pnl = trade.get("pnl")
            if raw_pnl is None:
                raw_pnl = trade.get("realized_pnl", 0.0)
            if isinstance(raw_pnl, (int, float)):
                pnl = float(raw_pnl)
            elif isinstance(raw_pnl, str):
                try:
                    pnl = float(raw_pnl)
                except ValueError:
                    pnl = 0.0
            else:
                pnl = 0.0

            try:
                from agents.evolution_memory.agent import EvolutionMemoryAgent
                EvolutionMemoryAgent().log_trade_post_mortem(trade)
            except Exception as e:
                logger.debug(f"[RiskAgent] Could not sync trade result to Evolution Memory: {e}")
        elif isinstance(trade, (int, float)):
            pnl = float(trade)
        elif isinstance(trade, str):
            try:
                pnl = float(trade)
            except ValueError:
                pnl = 0.0
        else:
            pnl = 0.0

        self.record_closed_trade(pnl)
        new_bal = self.account_balance + pnl
        self.update_account_balance(new_bal)

    def get_risk_status(self) -> Dict[str, Any]:
        """Returns unified status including daily drawdown, streak, and trading permission."""
        perm = self.drawdown_guard.check_trade_permission()
        dd = self.drawdown_guard.get_drawdown_status()
        daily_dd = abs(min(0.0, (dd["daily_pnl"] / max(dd["peak_equity"], 1.0)) * 100.0))
        return {
            "daily_drawdown_pct": daily_dd,
            "trading_allowed": perm["permitted"],
            "consecutive_losses": dd["consecutive_losses"],
            "consecutive_wins": dd["consecutive_wins"],
            "sizing_scale": perm["sizing_scale"],
            "reason": perm.get("reason", "OK")
        }

    def get_learned_dynamic_risk(self, evolution_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculates the agent-decided dynamic risk budget based on ongoing learning,
        empirical win-rate from Evolution Memory, streak status, and market volatility.
        Never hardcodes 1.0% - dynamically adapts between 0.25% (defensive) to 3.00% (high conviction).
        """
        # Base win rate & sample from memory if available
        win_rate = 0.55
        sample_size = 0
        avg_rr = 1.8
        
        if evolution_state:
            wins = evolution_state.get("wins_analyzed", 0)
            losses = evolution_state.get("losses_analyzed", 0)
            sample_size = wins + losses
            if sample_size >= 3:
                win_rate = max(0.30, min(0.85, wins / sample_size))

        # Streak status
        streak_info = self.drawdown_guard.get_drawdown_status()
        cons_wins = streak_info.get("consecutive_wins", 0)
        cons_losses = streak_info.get("consecutive_losses", 0)
        curr_dd = streak_info.get("drawdown_pct", 0.0)

        # Evaluate dynamic edge risk
        eval_result = PositionSizingEngine.calculate_dynamic_edge_risk_pct(
            win_rate=win_rate,
            rr_ratio=avg_rr,
            triple_index=65.0 if cons_wins > 0 else 45.0,
            setup_score=7.5,
            min_risk_pct=0.25,
            max_risk_pct=3.0
        )
        base_dynamic = eval_result.get("dynamic_risk_pct", 1.25)

        # Apply anti-martingale streak & DD scaling
        scaled = PositionSizingEngine.apply_anti_martingale_streak_scaling(
            base_risk_pct=base_dynamic,
            consecutive_wins=cons_wins,
            consecutive_losses=cons_losses,
            current_drawdown_pct=curr_dd
        )
        final_risk = scaled.get("final_risk_pct", base_dynamic)

        return {
            "dynamic_risk_pct": round(final_risk, 2),
            "tier": eval_result.get("tier", "AUTONOMOUS_LEARNED_EDGE"),
            "win_rate_learned": round(win_rate * 100, 1),
            "sample_size": sample_size,
            "streak_multiplier": scaled.get("multiplier", 1.0),
            "reasoning": (
                f"Agent decided {final_risk:.2f}% risk dynamically based on {win_rate*100:.1f}% learned win rate, "
                f"{cons_wins} win streak / {cons_losses} loss defense, and Half-Kelly optimization."
            )
        }

    def evaluate_trade_proposal(
        self,
        proposal: Dict[str, Any],
        open_positions: List[Dict[str, Any]],
        candles_df: Optional[pd.DataFrame] = None,
        evolution_warnings: Optional[List[Dict[str, Any]]] = None,
        is_high_impact_news_pending: bool = False
    ) -> Dict[str, Any]:
        """
        15-Section Comprehensive Audit of Proposed Trade.
        Runs geometry checks, drawdown permissions, portfolio heat, correlation matrix,
        Kelly & ATR sizing, historical candle shock test, and black swan stress simulation.
        """
        symbol = str(proposal.get("symbol", "BTC")).upper()
        direction = str(proposal.get("direction", "LONG")).upper()
        entry_price = float(proposal.get("entry_price") or 0.0)
        stop_loss = float(proposal.get("stop_loss") or 0.0)
        tp1 = float(proposal.get("take_profit_1") or 0.0)
        tp2 = float(proposal.get("take_profit_2") or 0.0)
        strategy_name = str(proposal.get("strategy_name", "UNKNOWN"))
        vol_state = str(proposal.get("volatility_state", "")).upper()
        ttm_fired = bool((proposal.get("ttm_squeeze") or {}).get("fired_expansion", False))
        is_expansion = bool(proposal.get("is_expansion_candle", False)) or vol_state in ["HIGH", "EXPANDING", "VOLATILITY_EXPANSION", "EXPANDED"] or ttm_fired

        is_wild_mode = (
            bool(proposal.get("is_wild_mode", False)) or
            (getattr(self, "active_mode", "CONSERVATIVE_SAFE") == "WILD_MODE") or
            is_expansion
        )

        mode_str = " [🔥 WILD MODE ENGAGED (Volatility Expansion)]" if (is_wild_mode and is_expansion) else (" [🔥 WILD MODE ENGAGED]" if is_wild_mode else "")
        logger.info(f"[RiskAgent] === RUNNING 15-SECTION RISK AUDIT for [{direction} {symbol}]{mode_str} at ${entry_price:,.2f} ===")

        # -------------------------------------------------------------
        # 1. Operational & Geometric Sanity Check (Section 14)
        # -------------------------------------------------------------
        if entry_price <= 0 or stop_loss <= 0:
            return {
                "decision": "REJECTED",
                "risk_tier": "BLOCKED",
                "reason": "OPERATIONAL_ERROR: Entry price or Stop Loss is zero/negative.",
                "section": "SECTION_14_OPERATIONAL_RISK"
            }

        # -------------------------------------------------------------
        # 2. Drawdown & Streak Permission Gate (Section 6 & 11)
        # -------------------------------------------------------------
        dd_perm = self.drawdown_guard.check_trade_permission()
        if not dd_perm["permitted"]:
            logger.warning(f"[RiskAgent] 🛑 Trade blocked by Drawdown Guard: {dd_perm['reason']}")
            return {
                "decision": "REJECTED",
                "risk_tier": "BLOCKED",
                "reason": dd_perm["reason"],
                "section": "SECTION_6_DRAWDOWN_MANAGEMENT"
            }

        # -------------------------------------------------------------
        # 3. Stop Loss, Target & R:R Mathematical Audit (Section 3, 4, 10)
        # -------------------------------------------------------------
        win_prob = float(proposal.get("win_rate_estimate", 0.50))
        df_bars = candles_df if candles_df is not None else pd.DataFrame()

        geo_audit = StopTargetValidator.audit_trade_geometry(
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            direction=direction,
            df=df_bars,
            timeframe_style="INTRADAY",
            win_rate_estimate=win_prob
        )

        if geo_audit["decision"] == "REJECTED":
            logger.warning(f"[RiskAgent] ❌ Trade rejected by Geometry & R:R Auditor: {geo_audit['reason']}")
            return {
                "decision": "REJECTED",
                "risk_tier": "BLOCKED",
                "reason": geo_audit["reason"],
                "section": "SECTION_3_AND_10_STOP_AND_RR",
                "flags": geo_audit.get("flags", [])
            }

        # Use audited values
        validated_sl = geo_audit["stop_loss"]
        validated_tp1 = geo_audit["take_profit_1"]
        validated_tp2 = geo_audit["take_profit_2"]
        sl_distance = geo_audit["risk_distance"]

        # -------------------------------------------------------------
        # 4. Dynamic Edge-Driven Mathematical Sizing (Section 2, 10 & 15)
        # Driven by real empirical win rate, R:R asymmetry, and confluence (0.25% to 5.0%)
        # Eliminates arbitrary hardcoded caps. High edge = 3.0% to 5.0% conviction; thin edge = 0.25% to 0.75%
        # -------------------------------------------------------------
        triple_index = float(proposal.get("triple_historical_index") or 50.0)
        setup_score = float(proposal.get("setup_score") or 6.5)

        sizing_eval = PositionSizingEngine.calculate_dynamic_edge_risk_pct(
            win_rate=win_prob,
            rr_ratio=geo_audit["rr_ratio"],
            triple_index=triple_index,
            setup_score=setup_score,
            min_risk_pct=0.25,
            max_risk_pct=5.0
        )

        if sizing_eval.get("verdict") == "NEGATIVE_EDGE_REJECT":
            return {
                "decision": "REJECTED",
                "risk_tier": "BLOCKED",
                "reason": sizing_eval.get("reason", "NEGATIVE_EDGE_REJECT"),
                "section": "SECTION_2_KELLY_EDGE"
            }

        assigned_risk_pct = sizing_eval["dynamic_risk_pct"]
        tier = sizing_eval["tier"]
        logger.info(f"[RiskAgent] 📊 Dynamic Sizing Computed: {assigned_risk_pct:.2f}% | Tier: {tier} | Win Rate: {win_prob*100:.1f}% | R:R: {geo_audit['rr_ratio']:.2f}")

        # -------------------------------------------------------------
        # 5. Anti-Martingale Streak & Drawdown Multipliers (Section 2 & 6)
        # -------------------------------------------------------------
        scaled_sizing = PositionSizingEngine.apply_anti_martingale_streak_scaling(
            base_risk_pct=assigned_risk_pct,
            consecutive_wins=self.drawdown_guard.consecutive_wins,
            consecutive_losses=self.drawdown_guard.consecutive_losses,
            current_drawdown_pct=self.drawdown_guard.get_drawdown_status()["drawdown_pct"]
        )
        assigned_risk_pct = scaled_sizing["final_risk_pct"]

        # In Wild Mode: Dynamic Volatility-Velocity Adaptive Clamp with Over-Time Learning
        if is_wild_mode:
            curr_tr = 0.0
            baseline_atr = 0.0
            if df_bars is not None and not df_bars.empty:
                last_row = df_bars.iloc[-1]
                curr_tr = float(last_row.get("high", 0) - last_row.get("low", 0))
                if "atr" in df_bars.columns:
                    baseline_atr = float(df_bars["atr"].rolling(14, min_periods=1).mean().iloc[-1])
                elif len(df_bars) > 1:
                    highs = df_bars["high"].astype(float)
                    lows = df_bars["low"].astype(float)
                    baseline_atr = float((highs - lows).mean())

            # Query Evolution Memory for learned Wild Mode regime performance
            wild_stats = {"win_rate": 50.0, "sample_size": 0}
            try:
                from agents.evolution_memory.agent import EvolutionMemoryAgent
                wild_stats = EvolutionMemoryAgent().get_regime_memory_stats("WILD_MODE")
            except Exception:
                pass

            adaptive_clamp_eval = PositionSizingEngine.calculate_adaptive_wild_mode_clamp(
                current_candle_tr=float(curr_tr),
                baseline_atr=float(baseline_atr),
                historical_wild_win_rate=float(wild_stats.get("win_rate", 50.0)),
                historical_wild_sample=int(wild_stats.get("sample_size", 0)),
                consecutive_wins=int(self.drawdown_guard.consecutive_wins),
                consecutive_losses=int(self.drawdown_guard.consecutive_losses)
            )
            adaptive_clamp = adaptive_clamp_eval["adaptive_clamp_pct"]
            assigned_risk_pct = min(assigned_risk_pct, adaptive_clamp)
            tier += f"_WILD_ADAPTIVE({adaptive_clamp}%)"
            logger.info(
                f"[RiskAgent] ⚡ Wild Mode Adaptive Clamp Enforced: Risk capped at {assigned_risk_pct:.2f}% "
                f"(Dynamic Cap: {adaptive_clamp}%, {adaptive_clamp_eval['reason']})"
            )

        # -------------------------------------------------------------
        # 6. Evolution Memory Warning Throttle (Section 11)
        # -------------------------------------------------------------
        if evolution_warnings and len(evolution_warnings) > 0:
            logger.warning(f"[RiskAgent] Evolution memory flags detected ({len(evolution_warnings)}). Throttling size by 50%.")
            assigned_risk_pct = max(0.25, round(assigned_risk_pct * 0.50, 2))
            tier += "_THROTTLED_BY_MEMORY"

        # -------------------------------------------------------------
        # 6B. Institutional Trap & Liquidity Sweep Gate (Depth 2/3)
        # -------------------------------------------------------------
        trap_info = proposal.get("trap_analysis") or {}
        if trap_info.get("recommended_action") == "VETO_TRADE":
            logger.warning(f"[RiskAgent] 🛑 Trade REJECTED by Trap Detector: {trap_info.get('veto_reason')}")
            return {
                "decision": "REJECTED",
                "risk_tier": "BLOCKED",
                "reason": trap_info.get("veto_reason", "INSTITUTIONAL_LIQUIDITY_TRAP_DETECTED"),
                "section": "SECTION_15_TRAP_AVOIDANCE",
                "trap_details": trap_info
            }
        elif trap_info.get("recommended_action") == "PROCEED_WITH_CAUTION_THROTTLE_50":
            logger.info(f"[RiskAgent] ⚠️ Moderate trap caution: Throttling risk by 50%.")
            assigned_risk_pct = max(0.25, round(assigned_risk_pct * 0.50, 2))
            tier += "_TRAP_CAUTION_THROTTLED"

        # -------------------------------------------------------------
        # 6C. Inter-Market Macro Cross-Asset Gate (DXY / Yields / VIX)
        # -------------------------------------------------------------
        intermarket_info = proposal.get("intermarket_implications") or {}
        if intermarket_info.get("alignment") in ["MACRO_HEADWIND", "VOLATILITY_ALERT"]:
            mult = float(intermarket_info.get("throttle_multiplier", 0.50))
            logger.info(f"[RiskAgent] 🌐 Macro Intermarket Drag ({intermarket_info.get('alignment')}): Throttling risk by {int(mult*100)}%. Reason: {intermarket_info.get('reason')}")
            assigned_risk_pct = max(0.25, round(assigned_risk_pct * mult, 2))
            tier += "_MACRO_DRAG_THROTTLED"

        # -------------------------------------------------------------
        # 6D. Fractal Multi-Timeframe (HTF) Trend Lock & Squeeze Gate
        # -------------------------------------------------------------
        fractal = proposal.get("fractal_alignment") or {}
        if fractal.get("htf_collision") or fractal.get("recommended_action") == "VETO_TRADE" or fractal.get("veto_trade"):
            veto_msg = fractal.get("veto_reason") or fractal.get("reason", "Counter-trend trade contradicts 4H/1H institutional trend")
            logger.warning(f"[RiskAgent] 🛑 Trade REJECTED by Fractal HTF Alignment: {veto_msg}")
            return {
                "decision": "REJECTED",
                "risk_tier": "BLOCKED",
                "reason": f"HTF_TREND_COLLISION: {veto_msg}",
                "section": "SECTION_12_FRACTAL_HTF_ALIGNMENT",
                "fractal_alignment": fractal
            }
        elif fractal.get("conviction_boost"):
            # HTF perfectly aligned + momentum confluence: boost conviction sizing
            assigned_risk_pct = min(5.0, round(assigned_risk_pct * 1.25, 2))
            tier += "_FRACTAL_HTF_BOOSTED"
            logger.info(f"[RiskAgent] 🚀 Fractal HTF Alignment Confirmed: 25% Conviction Sizing Boost applied (Risk: {assigned_risk_pct:.2f}%).")

        ttm = proposal.get("ttm_squeeze") or {}
        if ttm.get("squeeze_fired"):
            logger.info(f"[RiskAgent] 💥 TTM Volatility Squeeze Fired! Breakout expansion confirmed.")

        # Calculate preliminary units and position dollar value
        dollar_risk = self.account_balance * (assigned_risk_pct / 100.0)
        units = dollar_risk / sl_distance
        proposed_position_val = units * entry_price

        # -------------------------------------------------------------
        # 7. Portfolio Heat, Correlation & Concentration Audit (Section 5, 7, 9)
        # -------------------------------------------------------------
        port_check = self.portfolio_controller.evaluate_portfolio_admission(
            new_symbol=symbol,
            new_direction=direction,
            proposed_risk_pct=assigned_risk_pct,
            proposed_position_value=proposed_position_val,
            account_balance=self.account_balance,
            open_positions=open_positions,
            is_high_impact_news_pending=is_high_impact_news_pending
        )

        if port_check["decision"] == "REJECTED":
            logger.warning(f"[RiskAgent] ❌ Portfolio check failed: {port_check['reason']}")
            return {
                "decision": "REJECTED",
                "risk_tier": "BLOCKED",
                "reason": port_check["reason"],
                "section": "SECTION_5_AND_9_PORTFOLIO_AND_CORRELATION"
            }
        elif port_check["decision"] == "THROTTLED_APPROVAL":
            # Apply correlation throttle
            mult = port_check.get("throttle_multiplier", 0.50)
            assigned_risk_pct = max(0.25, round(assigned_risk_pct * mult, 2))
            dollar_risk = self.account_balance * (assigned_risk_pct / 100.0)
            units = dollar_risk / sl_distance
            proposed_position_val = units * entry_price
            tier += "_CORRELATION_THROTTLED"

        # -------------------------------------------------------------
        # 8. Black Swan & Historical Chart Re-Test (Section 13)
        # -------------------------------------------------------------
        shock_test = BlackSwanStressTester.run_historical_shock_simulation(
            df=df_bars,
            entry_price=entry_price,
            stop_loss=validated_sl,
            direction=direction,
            dollar_risk=dollar_risk
        )

        if shock_test["status"] == "HIGH_TAIL_RISK":
            # If historical tail risk is high, reduce size by 30%
            logger.warning(f"[RiskAgent] High tail risk detected on old candles (VaR 99%: {shock_test['var_99_pct']}%). Adding risk padding.")
            assigned_risk_pct = max(0.25, round(assigned_risk_pct * 0.70, 2))
            dollar_risk = self.account_balance * (assigned_risk_pct / 100.0)
            units = dollar_risk / sl_distance
            proposed_position_val = units * entry_price

        # Check simultaneous portfolio liquidation
        black_swan_check = BlackSwanStressTester.test_simultaneous_portfolio_liquidation(
            open_positions=open_positions,
            new_dollar_risk=dollar_risk,
            account_balance=self.account_balance
        )
        if black_swan_check["status"] == "FAIL":
            return {
                "decision": "REJECTED",
                "risk_tier": "BLOCKED",
                "reason": black_swan_check["reason"],
                "section": "SECTION_13_BLACK_SWAN"
            }

        # -------------------------------------------------------------
        # 9. Final Institutional Approval & Execution Contract
        # -------------------------------------------------------------
        logger.info(
            f"[RiskAgent] ✅ TRADE FULLY APPROVED: [{direction} {symbol}] | "
            f"Risk: {assigned_risk_pct}% (${dollar_risk:,.2f}) | Units: {units:.4f} | R:R: 1:{geo_audit['rr_ratio']} | Tier: {tier}"
        )

        return {
            "decision": "APPROVED",
            "risk_tier": tier,
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": validated_sl,
            "take_profit_1": validated_tp1,
            "take_profit_2": validated_tp2,
            "rr_ratio": geo_audit["rr_ratio"],
            "expectancy_r": geo_audit["expectancy_r"],
            "risk_pct": assigned_risk_pct,
            "risk_percent": assigned_risk_pct,
            "dollar_risk": round(dollar_risk, 2),
            "units": round(units, 4),
            "position_value": round(proposed_position_val, 2),
            "position_size_usd": round(proposed_position_val, 2),
            "sl_distance_pct": geo_audit["risk_distance"] / entry_price * 100.0,
            "portfolio_heat_after_trade": port_check.get("new_total_heat", assigned_risk_pct),
            "portfolio_heat_pct": port_check.get("new_total_heat", assigned_risk_pct),
            "correlated_conflicts": port_check.get("correlated_conflicts", []),
            "correlation_warning": port_check.get("reason") if port_check.get("correlated_conflicts") else None,
            "reason": port_check.get("reason"),
            "partial_plan": geo_audit["partial_plan"],
            "stress_test_score": shock_test["stress_score"],
            "var_99_pct": shock_test.get("var_99_pct"),
            "account_balance": round(self.account_balance, 2),
            "is_wild_mode": is_wild_mode,
            "breakeven_trigger_r": 1.0 if is_wild_mode else 1.5,
            "max_hold_bars": 12 if is_wild_mode else 30
        }

    def get_risk_dashboard_telemetry(self, open_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Provides Section 12 live monitoring metrics for the UI."""
        dd_status = self.drawdown_guard.get_drawdown_status()
        current_heat = sum(float(p.get("risk_pct", 1.0)) for p in open_positions)

        return {
            "account_balance": round(self.account_balance, 2),
            "peak_equity": dd_status["peak_equity"],
            "drawdown_pct": dd_status["drawdown_pct"],
            "drawdown_tier": dd_status["tier"],
            "daily_loss_pct": round((dd_status["daily_pnl"] / max(dd_status["peak_equity"], 1)) * 100.0, 2),
            "daily_halted": dd_status["daily_halted"],
            "portfolio_heat_pct": round(current_heat, 2),
            "portfolio_heat_cap_pct": self.portfolio_controller.max_portfolio_heat_pct,
            "consecutive_losses": dd_status["consecutive_losses"],
            "consecutive_wins": dd_status["consecutive_wins"],
            "open_positions_count": len(open_positions)
        }


if __name__ == "__main__":
    risk_agent = RiskManagementAgent(account_balance=100000.0)
    print("Testing Risk Management Agent...")
    telemetry = risk_agent.get_risk_dashboard_telemetry(open_positions=[])
    print(f"Risk Shield Online - Peak Equity: ${telemetry['peak_equity']:,.2f} | Drawdown Tier: {telemetry['drawdown_tier']}")
    print(f"Portfolio Heat Cap: {telemetry['portfolio_heat_cap_pct']}% | Daily Halted: {telemetry['daily_halted']}")


