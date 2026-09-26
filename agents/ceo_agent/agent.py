"""
CEO Supreme King Agent - Master Institutional Commander & Arbitrator
Role:
1. Supreme All-Seeing Eye: Observes every sub-agent (News, Analytical, Strategy, Backtest, Risk, Execution, Evolution).
2. Supreme Conflict Arbitrator: Resolves contradictory signals between sub-agents.
3. Global Market Opportunist: Decides dynamic capital allocation across the 8 global share markets.
4. Final Veto & Emergency Kill Switch: Can override, pause, or kill rogue clones or trades.
5. Absolute Subordination to User Command: Obeys user master commands (START, PAUSE, STOP, VETO).
"""

import sys
import os
import time
import logging
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from shared_brain.llm_brain import LLMBrain
from shared_brain.shared_board import SharedAgentBoard
from shared_brain.omni_calculator import OmniCalculator
from agents.evolution_memory.mem0_memory_engine import Mem0MemoryEngine
from agents.evolution_memory.market_memory_matrix import MarketMemoryMatrix

logger = logging.getLogger("CEOAgent")


class CEOAgent:
    """
    The Supreme King of the Quantitative Army.
    Oversees the entire pipeline, resolves conflicts, commands shadow clones,
    and acts under the ultimate authority of the User.
    """

    def __init__(self, brain: Optional[LLMBrain] = None):
        self.brain = brain or LLMBrain()
        self.board = SharedAgentBoard()
        self.mem0 = self.board.mem0
        self.matrix = MarketMemoryMatrix()
        self.calc = OmniCalculator(owner="CEOAgent")

        # Operational State
        self.active_mandate: str = "BALANCED_CAPITAL_GROWTH"  # AGGRESSIVE | BALANCED | CAPITAL_PRESERVATION | DEFENSIVE_LOCKDOWN
        self.user_override_active: bool = False
        self.last_arbitration_report: Dict[str, Any] = {}
        self.total_vetoes_issued: int = 0
        self.total_approvals_granted: int = 0
        self.all_seeing_telemetry: Dict[str, Any] = {}

        logger.info("[CEOAgent] 👑 Supreme King Agent online. All agent feeds synchronized under CEO command.")

    def inspect_all_agent_eyes(
        self,
        news_data: Dict[str, Any],
        analytical_data: Dict[str, Any],
        strategy_data: Dict[str, Any],
        backtest_data: Dict[str, Any],
        risk_data: Dict[str, Any],
        execution_data: Dict[str, Any],
        memory_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Gathers real-time inputs from all 7 sub-agents simultaneously ('All-Seeing Eyes').
        """
        self.all_seeing_telemetry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "news_bias": news_data.get("macro_bias", "NEUTRAL"),
            "chart_signal": analytical_data.get("signal", "SCANNING"),
            "chart_pattern": analytical_data.get("chart_pattern", "NONE"),
            "confluence_index": strategy_data.get("triple_historical_edge", {}).get("triple_historical_index", 50.0),
            "champion_strategy": (strategy_data.get("champion_strategy") or {}).get("name", "NONE"),
            "lab_champion": (backtest_data.get("champion_strategy") or {}).get("name", "NONE"),
            "risk_verdict": risk_data.get("decision", "HOLD"),
            "dollar_risk": risk_data.get("dollar_risk", 0.0),
            "open_positions_count": len(execution_data.get("open_positions", [])),
            "agent_xp_level": memory_summary.get("agent_level", 1),
            "negative_constraints_active": len(self.mem0.get_all_negative_constraints())
        }
        return self.all_seeing_telemetry

    def arbitrate_agent_conflicts(
        self,
        news_bias: str,
        analytical_signal: str,
        strategy_action: str,
        risk_decision: str,
        market: str,
        trap_detected: bool = False,
        intermarket_regime: str = "MACRO_NEUTRAL_TRANSITION",
        strategy_name: Optional[str] = None,
        symbol: Optional[str] = None,
        evolution_warnings: Optional[List[Dict[str, Any]]] = None,
        chart_score: float = 0.0
    ) -> Dict[str, Any]:
        """
        Supreme Arbitrator: Resolves friction and disagreements between agents.
        Example: News is Bearish but Chart is Bullish, or Strategy wants aggressive entry but Risk is on edge.
        """
        conflicts = []
        news_dir = "LONG" if "BULL" in news_bias.upper() else ("SHORT" if "BEAR" in news_bias.upper() else "NEUTRAL")
        chart_dir = "LONG" if "BUY" in analytical_signal.upper() else ("SHORT" if "SELL" in analytical_signal.upper() else "NEUTRAL")

        # Conflict 1: Macro vs Price Action Contradiction
        macro_chart_conflict = False
        if news_dir != "NEUTRAL" and chart_dir != "NEUTRAL" and news_dir != chart_dir:
            macro_chart_conflict = True
            conflicts.append(f"Contradiction: Macro News is {news_bias} but Chart Price Action signals {analytical_signal}.")

        # Conflict 2: Strategy wants to execute but Risk rejected
        strat_risk_conflict = False
        if strategy_action == "EXECUTE" and risk_decision == "REJECTED":
            strat_risk_conflict = True
            conflicts.append("Friction: Strategy R&D signaled EXECUTE but Risk Management Shield issued REJECTED.")

        # Conflict 3: Negative constraint & Evolution Memory warning check
        active_constraints = self.mem0.get_all_negative_constraints()
        constraint_warning = False
        matching_constraint = None
        strat_up = (strategy_name or "").upper()
        sym_up = (symbol or "").upper()
        mkt_up = (market or "").upper()

        for c in active_constraints:
            c_desc = c if isinstance(c, str) else c.get("description", str(c))
            c_txt = c_desc.upper()
            # If constraint specifies a strategy, verify strategy matches
            if "CAREFUL WITH '" in c_txt:
                if strat_up and f"'{strat_up}'" in c_txt:
                    conflicts.append(f"Mem0 Warning: Historical loss constraint applies: {c_desc}")
                    constraint_warning = True
                    matching_constraint = c_desc
                    break
            elif strat_up and strat_up in c_txt:
                conflicts.append(f"Mem0 Warning: Historical loss constraint applies: {c_desc}")
                constraint_warning = True
                matching_constraint = c_desc
                break
            elif sym_up and sym_up in c_txt and mkt_up in c_txt and ("CAREFUL WITH" not in c_txt and "'" not in c_txt):
                conflicts.append(f"Mem0 Warning: Historical loss constraint applies: {c_desc}")
                constraint_warning = True
                matching_constraint = c_desc
                break

        # Check Evolution Memory warnings
        if evolution_warnings:
            for w in evolution_warnings:
                w_msg = w.get("message") or w.get("type", "EVOLUTION_MEMORY_WARNING")
                conflicts.append(f"Evolution Memory Warning: {w_msg}")
                constraint_warning = True
                if not matching_constraint:
                    matching_constraint = w_msg

        # 0. Institutional Trap Override
        if trap_detected:
            conflicts.append("PREDATORY_TRAP: Institutional Trap Detector flagged an active retail trap (Bull/Bear Trap or Orderbook Wall).")
            verdict = "RISK_PRESERVATION_OVERRIDE"
            ruling = "CEO rules: Immediate trade abort. Never trade into an active institutional liquidity sweep."
            recommended_mandate = "CAPITAL_PRESERVATION"
            self.last_arbitration_report = {
                "has_conflicts": True,
                "conflicts_identified": conflicts,
                "ceo_ruling": ruling,
                "arbitration_verdict": verdict,
                "recommended_mandate": recommended_mandate
            }
            return self.last_arbitration_report

        # 0B. Inter-Market Macro Storm Override
        if intermarket_regime == "MACRO_VOLATILITY_STORM" and strategy_action == "EXECUTE":
            conflicts.append("MACRO_VOLATILITY_STORM: Intermarket Nexus flagged VIX panic spike or liquidity drain.")
            verdict = "RISK_PRESERVATION_OVERRIDE"
            ruling = "CEO rules: Market volatility storm active. Stand down until cross-asset liquidity stabilizes."
            recommended_mandate = "DEFENSIVE_LOCKDOWN"
            self.last_arbitration_report = {
                "has_conflicts": True,
                "conflicts_identified": conflicts,
                "ceo_ruling": ruling,
                "arbitration_verdict": verdict,
                "recommended_mandate": recommended_mandate
            }
            return self.last_arbitration_report

        # 0C. Negative Constraint / Repeat Mistake Defense Override
        if constraint_warning:
            conflicts.append(f"EVOLUTION_MEMORY_VETO: Repeat setup risk detected ({matching_constraint}).")
            verdict = "RISK_PRESERVATION_OVERRIDE"
            ruling = f"CEO rules: Evolution Memory repeat mistake defense active ({matching_constraint}). Abort trade to avoid repeating historical loss."
            recommended_mandate = "CAPITAL_PRESERVATION"
            self.last_arbitration_report = {
                "has_conflicts": True,
                "conflicts_identified": conflicts,
                "ceo_ruling": ruling,
                "arbitration_verdict": verdict,
                "recommended_mandate": recommended_mandate,
                "memory_warning_active": True,
                "matching_constraint": matching_constraint
            }
            return self.last_arbitration_report

        # 1. Technical Buy vs Macro Bearish News (e.g. Geopolitical Crisis)
        if "BUY" in analytical_signal.upper() and "BEAR" in news_bias.upper():
            conflicts.append("CONFLICT_ANALYTICAL_VS_NEWS: Technical chart signals strong BUY, but breaking News/Macro is BEARISH (Geopolitical Crisis).")
            if chart_score >= 7.5:
                verdict = "HALVE_RISK_PROCEED"
                ruling = f"CEO rules: High-conviction technical edge (Score {chart_score}/10) clashes with Bearish Macro tide. Authorize HALVE_RISK_PROCEED: Cut size by 50%, enforce tighter structural SL, and switch mandate to DEFENSIVE_TACTICAL."
                recommended_mandate = "DEFENSIVE_TACTICAL"
            else:
                verdict = "STRATEGY_DE-RISK_OR_STANDBY"
                ruling = "CEO rules: Macro tide always overwhelms mediocre micro technicals. Stand down until macro aligns."
                recommended_mandate = "CAPITAL_PRESERVATION"

        # 2. Technical Sell vs Macro Bullish News
        elif "SELL" in analytical_signal.upper() and "BULL" in news_bias.upper():
            conflicts.append("CONFLICT_ANALYTICAL_VS_NEWS: Technical chart signals strong SELL, but breaking News/Macro is BULLISH.")
            if chart_score >= 7.5:
                verdict = "HALVE_RISK_PROCEED"
                ruling = f"CEO rules: High-conviction technical short (Score {chart_score}/10) clashes with Bullish Macro tide. Authorize HALVE_RISK_PROCEED: Cut size by 50%, enforce tighter SL, and switch mandate to DEFENSIVE_TACTICAL."
                recommended_mandate = "DEFENSIVE_TACTICAL"
            else:
                verdict = "STRATEGY_DE-RISK_OR_STANDBY"
                ruling = "CEO rules: Bullish macro tailwind present. Await structural confirmation before shorting."
                recommended_mandate = "CAPITAL_PRESERVATION"

        # 3. Strategy wants Execute but Risk Rejects
        elif strategy_action == "EXECUTE" and risk_decision == "REJECTED":
            conflicts.append("CONFLICT_STRATEGY_VS_RISK: Strategy selected a setup, but 15-Section Risk Shield REJECTED it.")
            verdict = "RISK_PRESERVATION_OVERRIDE"
            ruling = "CEO rules: The Risk Shield is absolute law. No trade may bypass Risk Agent."
            recommended_mandate = "CAPITAL_PRESERVATION"

        # 4. Consensus
        else:
            verdict = "UNANIMOUS_CONVERGENCE"
            ruling = "All specialist agents are aligned or neutral. Clear institutional consensus achieved."
            recommended_mandate = "BALANCED_CAPITAL_GROWTH"

        self.last_arbitration_report = {
            "has_conflicts": len(conflicts) > 0,
            "conflicts_identified": conflicts,
            "ceo_ruling": ruling,
            "arbitration_verdict": verdict,
            "recommended_mandate": recommended_mandate
        }
        return self.last_arbitration_report

    def evaluate_global_market_opportunities(
        self,
        current_active_market: str
    ) -> Dict[str, Any]:
        """
        Analyzes the 8 global share markets and recommends which market currently
        has the highest opportunity to deploy capital or launch Shadow Clones.
        """
        all_markets = ["CRYPTO", "INDIAN_STOCKS", "US_STOCKS", "UK_STOCKS", "EU_STOCKS", "ASIAN_STOCKS", "FOREX", "COMMODITIES"]
        rankings = []

        for m in all_markets:
            top_strats = self.matrix.get_top_strategies_for_market(m)
            avg_wr = sum(s.get("win_rate", 50.0) for s in top_strats[:3]) / max(len(top_strats[:3]), 1)
            
            # Bonus if market is currently in active prime hours (approximated)
            is_active = (m == current_active_market)
            opportunity_score = round(avg_wr + (5.0 if is_active else 0.0), 1)

            rankings.append({
                "market": m,
                "opportunity_score": opportunity_score,
                "top_strategy": top_strats[0]["name"] if top_strats else "NONE",
                "empirical_win_rate": top_strats[0]["win_rate"] if top_strats else 50.0
            })

        rankings.sort(key=lambda x: x["opportunity_score"], reverse=True)

        return {
            "primary_market_recommendation": rankings[0]["market"],
            "top_markets_for_clone_squads": [r["market"] for r in rankings[:3]],
            "market_rankings": rankings
        }

    def grant_supreme_approval(
        self,
        market: str,
        symbol: str,
        direction: str,
        strategy_decision: Dict[str, Any],
        risk_verdict: Dict[str, Any],
        arbitration: Dict[str, Any],
        trap_analysis: Optional[Dict[str, Any]] = None,
        intermarket_state: Optional[Dict[str, Any]] = None,
        fractal_alignment: Optional[Dict[str, Any]] = None,
        trading_mode: str = "SAFE"
    ) -> Dict[str, Any]:
        """
        Final authorization gate before any order can be dispatched to the broker or clone.
        The CEO signs off with supreme authority.
        """
        is_dangerous = "DANGEROUS" in str(trading_mode or getattr(self, "trading_mode", "SAFE")).upper()

        # 1. Check User Override
        if self.user_override_active:
            self.total_vetoes_issued += 1
            return {
                "ceo_decision": "VETOED",
                "reason": "USER_MASTER_OVERRIDE_ACTIVE: Operations suspended by human commander.",
                "mandate": "DEFENSIVE_LOCKDOWN",
                "approved_for_execution": False
            }

        # 1B. Check Institutional Trap Detection (Depth 2/3)
        if trap_analysis and trap_analysis.get("recommended_action") == "VETO_TRADE" and not is_dangerous:
            self.total_vetoes_issued += 1
            return {
                "ceo_decision": "VETOED",
                "reason": f"CEO Trap Shield Veto: {trap_analysis.get('veto_reason', 'Institutional Trap Detected')}",
                "mandate": "PREDATORY_TRAP_SHIELD",
                "approved_for_execution": False
            }

        # 1C. Check Macro Volatility Storm
        if intermarket_state and intermarket_state.get("macro_regime") == "MACRO_VOLATILITY_STORM" and not is_dangerous:
            self.total_vetoes_issued += 1
            return {
                "ceo_decision": "VETOED",
                "reason": f"CEO Macro Veto: Market-wide Volatility Storm (VIX {intermarket_state.get('vix_level')}). Aborting new risk.",
                "mandate": "DEFENSIVE_LOCKDOWN",
                "approved_for_execution": False
            }

        # 1D. Check Fractal HTF Trend Lock Veto
        # Verify if proposed trade direction actually collides with HTF trend
        htf_collision = False
        if fractal_alignment and (fractal_alignment.get("htf_collision") or fractal_alignment.get("recommended_action") == "VETO_TRADE"):
            htf_struct = fractal_alignment.get("htf_structure", {})
            htf_trend = htf_struct.get("trend", "")
            # Only veto if the actual proposed trade direction collides with HTF
            if (direction == "LONG" and htf_trend == "STRONG_BEARISH") or (direction == "SHORT" and htf_trend == "STRONG_BULLISH"):
                htf_collision = True

        if htf_collision and not is_dangerous:
            self.total_vetoes_issued += 1
            veto_msg = fractal_alignment.get("veto_reason") or fractal_alignment.get("reason", "Counter-trend trade contradicts 4H/1H institutional trend")
            return {
                "ceo_decision": "VETOED",
                "reason": f"CEO Fractal HTF Veto: {veto_msg}",
                "mandate": "FRACTAL_TREND_DEFENSE",
                "approved_for_execution": False
            }

        # 2. Check Risk Veto
        if risk_verdict.get("decision") == "REJECTED":
            self.total_vetoes_issued += 1
            risk_reason = str(risk_verdict.get("reason", "Exceeded risk limits"))
            is_heat_or_corr_veto = any(k in risk_reason for k in ["PORTFOLIO_HEAT", "CORRELATION", "CONCENTRATION"])
            mandate = "PORTFOLIO_HEAT_DEFENSE" if is_heat_or_corr_veto else "CAPITAL_PRESERVATION"
            if is_heat_or_corr_veto:
                logger.warning(f"[CEOAgent] 🛑 CEO SUPREME VETO: Portfolio Heat & Correlation Guard triggered! {risk_reason}")

            return {
                "ceo_decision": "VETOED",
                "reason": f"CEO upholds Risk Shield rejection: {risk_reason}",
                "mandate": mandate,
                "correlation_risk_flagged": is_heat_or_corr_veto,
                "approved_for_execution": False
            }

        # 3. Check Strategy Recommendation
        strat_action = strategy_decision.get("recommended_action", strategy_decision.get("action", "WAIT"))
        if strat_action not in ["EXECUTE", "BUY", "SELL"]:
            return {
                "ceo_decision": "STANDBY",
                "reason": f"Strategy indicates '{strat_action}'. Awaiting institutional high-conviction trigger.",
                "mandate": self.active_mandate,
                "approved_for_execution": False
            }

        # 4. Check Arbitration Verdict
        if arbitration.get("arbitration_verdict") == "RISK_PRESERVATION_OVERRIDE":
            self.total_vetoes_issued += 1
            return {
                "ceo_decision": "VETOED",
                "reason": f"Arbitration conflict detected: {arbitration.get('ceo_ruling')}",
                "mandate": "CAPITAL_PRESERVATION",
                "approved_for_execution": False,
                "memory_warning_considered": arbitration.get("memory_warning_active", False)
            }

        # 4B. Check HALVE_RISK_PROCEED Arbitration Decision
        if arbitration.get("arbitration_verdict") == "HALVE_RISK_PROCEED":
            self.total_approvals_granted += 1
            self.active_mandate = "DEFENSIVE_TACTICAL"

            orig_units = float(risk_verdict.get("units", 0.0))
            cut_units = round(orig_units * 0.50, 4)
            orig_dollar_risk = float(risk_verdict.get("dollar_risk", 0.0))
            cut_dollar_risk = round(orig_dollar_risk * 0.50, 2)
            orig_risk_pct = float(risk_verdict.get("risk_pct", 1.0))
            cut_risk_pct = round(orig_risk_pct * 0.50, 2)

            # Apply tighter structural stop loss (25% tighter distance from entry)
            entry_p = float(strategy_decision.get("entry_price", 0.0))
            orig_sl = float(strategy_decision.get("stop_loss", 0.0))
            sl_dist = abs(entry_p - orig_sl)
            if direction.upper() == "LONG":
                tighter_sl = round(entry_p - (sl_dist * 0.75), 2)
            else:
                tighter_sl = round(entry_p + (sl_dist * 0.75), 2)

            # Update live payloads in-place
            risk_verdict["units"] = cut_units
            risk_verdict["dollar_risk"] = cut_dollar_risk
            risk_verdict["risk_pct"] = cut_risk_pct
            risk_verdict["stop_loss"] = tighter_sl
            strategy_decision["stop_loss"] = tighter_sl

            logger.warning(
                f"[CEOAgent] ⚡ CONFLICT RESOLUTION: HALVE_RISK_PROCEED enacted! "
                f"Units cut 50%: {orig_units} -> {cut_units} | SL tightened: {orig_sl} -> {tighter_sl} | Mandate: DEFENSIVE_TACTICAL"
            )

            return {
                "ceo_decision": "HALVE_RISK_PROCEED",
                "reason": arbitration.get("ceo_ruling"),
                "mandate": "DEFENSIVE_TACTICAL",
                "approved_for_execution": True,
                "position_size_cut_pct": 50.0,
                "original_units": orig_units,
                "adjusted_units": cut_units,
                "original_stop_loss": orig_sl,
                "tighter_stop_loss": tighter_sl,
                "original_risk_pct": orig_risk_pct,
                "adjusted_risk_pct": cut_risk_pct,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

        # 5. Supreme Approval Granted (Audit Correlation & Heat)
        self.total_approvals_granted += 1
        corr_conflicts = risk_verdict.get("correlated_conflicts") or []
        correlation_flagged = False
        correlation_note = ""
        if corr_conflicts:
            correlation_flagged = True
            corr_assets = [c.get("existing_asset", "") for c in corr_conflicts]
            correlation_note = f"CORRELATION_DEFENSE_ACTIVE: {symbol} is correlated with open positions {corr_assets} (r={corr_conflicts[0].get('correlation', 0.8)}). Sizing restricted to manage joint drawdowns."
            logger.warning(f"[CEOAgent] ⚠️ {correlation_note}")

        return {
            "ceo_decision": "APPROVED",
            "reason": f"CEO Supreme Approval Granted for [{direction} {symbol}] in {market}. Confluence and Risk verified.",
            "correlation_risk_flagged": correlation_flagged,
            "correlation_note": correlation_note,
            "portfolio_heat_pct": risk_verdict.get("portfolio_heat_after_trade", risk_verdict.get("risk_pct", 0.0)),
            "mandate": arbitration.get("recommended_mandate", "BALANCED_CAPITAL_GROWTH"),
            "approved_for_execution": True,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def emergency_override(self, command: str, reason: str = "") -> Dict[str, Any]:
        """
        Emergency command receiver: User or CEO can issue a master command.
        Supported commands: PAUSE, RESUME, STOP, KILL_ALL_CLONES, SET_MANDATE
        """
        cmd = command.upper().strip()
        logger.warning(f"[CEOAgent] 🚨 COMMAND RECEIVED: [{cmd}] - {reason}")

        if cmd in ["PAUSE", "STOP", "LOCKDOWN"]:
            self.user_override_active = True
            self.active_mandate = "DEFENSIVE_LOCKDOWN"
            return {"status": "SUCCESS", "message": f"CEO entered {self.active_mandate}. Operations paused."}
        elif cmd in ["RESUME", "START"]:
            self.user_override_active = False
            self.active_mandate = "BALANCED_CAPITAL_GROWTH"
            return {"status": "SUCCESS", "message": "CEO resumed standard operations under BALANCED_CAPITAL_GROWTH."}
        elif cmd.startswith("MANDATE_"):
            new_mandate = cmd.replace("MANDATE_", "")
            self.active_mandate = new_mandate
            return {"status": "SUCCESS", "message": f"Active strategic mandate set to {new_mandate}."}
        else:
            return {"status": "ERROR", "message": f"Unknown command: {command}"}

    def command_emergency_trade_exit(
        self,
        execution_agent,
        symbol: Optional[str] = None,
        trade_id: Optional[str] = None,
        reason: str = "CEO_SUPREME_FORCE_EXIT"
    ) -> List[Dict[str, Any]]:
        """
        Supreme King Authority: Forcefully aborts/liquidates open trades mid-flight.
        Can terminate a specific trade_id, all trades on a symbol, or entire book if neither specified.
        """
        target = trade_id or symbol or ""
        logger.warning(f"[CEOAgent] 👑 SUPREME COMMAND ISSUED: Liquidate open position ({target}) - Reason: {reason}")
        if not execution_agent:
            return []

        if target:
            return execution_agent.force_close_trade(target, reason=reason)
        else:
            closed = []
            for pos in execution_agent.get_open_positions_list():
                c = execution_agent.force_close_trade(pos["trade_id"], reason=reason)
                closed.extend(c)
            return closed

    def enforce_active_risk_interventions(
        self,
        execution_agent,
        news_alert: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Active Position Surveillance & Crisis Intervention:
        Surveys all live positions against macro news shocks and severe structural contradictions.
        If a critical contrary catalyst is detected, CEO issues an instant force-close command.
        """
        if not execution_agent:
            return {"status": "NO_EXECUTION_AGENT", "actions": []}

        open_positions = execution_agent.get_open_positions_list()
        if not open_positions:
            return {"status": "NO_OPEN_POSITIONS", "actions": []}

        actions_taken = []
        if news_alert:
            macro_bias = str(news_alert.get("macro_bias", "NEUTRAL")).upper()
            precedent = news_alert.get("historical_precedent") or {}
            win_prob = float(precedent.get("historical_win_prob", 50.0))
            is_critical = (
                news_alert.get("severity") == "CRITICAL" or
                news_alert.get("urgency") == "HIGH" or
                win_prob >= 75.0
            )

            if is_critical and macro_bias in ["BULLISH", "BEARISH", "CRASH_RISK"]:
                for pos in open_positions:
                    pos_dir = str(pos.get("direction", "")).upper()
                    sym = pos.get("symbol", "UNKNOWN")
                    unrealized_r = float(pos.get("unrealized_r") or 0.0)

                    is_contrary = (
                        (pos_dir == "SHORT" and macro_bias in ["BULLISH", "SURPRISE_STIMULUS"]) or
                        (pos_dir == "LONG" and macro_bias in ["BEARISH", "CRASH_RISK"])
                    )

                    if is_contrary:
                        # If trade is well in profit, lock Breakeven so it can breathe if candle wicks
                        if unrealized_r >= 0.3:
                            pos["stop_loss"] = float(pos.get("entry_price") or pos.get("stop_loss"))
                            pos["sl_state"] = "BREAKEVEN"
                            logger.info(f"[CEOAgent] 🛡️ CEO locked Breakeven on profitable contrary trade {sym} ({pos['trade_id']}).")
                            actions_taken.append(f"LOCK_BREAKEVEN_{sym}")
                        else:
                            # If flat or in loss, liquidate immediately before news gap widens
                            reason = f"CEO_FORCE_EXIT: {macro_bias} high-impact catalyst contrary to {pos_dir} position."
                            res = self.command_emergency_trade_exit(execution_agent, trade_id=pos["trade_id"], reason=reason)
                            actions_taken.append(f"FORCE_EXIT_{sym}")

        return {
            "status": "INTERVENTIONS_EVALUATED",
            "actions": actions_taken,
            "open_positions_remaining": len(execution_agent.get_open_positions_list())
        }

    def get_ceo_dashboard_snapshot(self) -> Dict[str, Any]:
        """Full state overview for the UI and Core Engine."""
        return {
            "role": "CEO Supreme King Agent",
            "active_mandate": self.active_mandate,
            "user_override_active": self.user_override_active,
            "total_approvals_granted": self.total_approvals_granted,
            "total_vetoes_issued": self.total_vetoes_issued,
            "latest_arbitration": self.last_arbitration_report,
            "all_seeing_telemetry": self.all_seeing_telemetry
        }


if __name__ == "__main__":
    ceo = CEOAgent()
    print("Testing CEO Supreme King Agent...")
    print(f"Mandate: {ceo.active_mandate}")
    arb = ceo.arbitrate_agent_conflicts(
        news_bias="BULLISH",
        analytical_signal="BUY",
        strategy_action="EXECUTE",
        risk_decision="APPROVED",
        market="CRYPTO"
    )
    print(f"Arbitration Verdict: {arb['arbitration_verdict']} -> {arb['ceo_ruling']}")
    approval = ceo.grant_supreme_approval(
        market="CRYPTO",
        symbol="BTC",
        direction="BUY",
        strategy_decision={"recommended_action": "EXECUTE", "confidence": 0.85},
        risk_verdict={"decision": "APPROVED", "risk_tier": "TIER_1_DEFENSIVE"},
        arbitration=arb
    )
    print(f"CEO Supreme Decision: {approval['ceo_decision']} (Approved: {approval['approved_for_execution']})")


