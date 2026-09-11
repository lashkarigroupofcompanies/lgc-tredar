"""
Overfitting & Red Flag Detection Engine (Section 17 Framework)
Protects against curve-fitting, look-ahead bias, and data snooping.
Flags 'too good to be true' backtest results before real capital is deployed.
"""

from typing import Dict, Any, List


class OverfittingRedFlagDetector:
    """
    Skeptical quantitative auditor flagging over-optimized or curve-fitted strategies.
    """

    @classmethod
    def audit_backtest_for_red_flags(
        cls,
        win_rate_pct: float,
        profit_factor: float,
        sharpe_ratio: float,
        sqn: float,
        total_trades: int,
        max_consecutive_losses: int,
        walk_forward_efficiency: float = 0.6
    ) -> Dict[str, Any]:
        """
        Scans backtest statistics and returns red flag warnings.
        """
        red_flags: List[str] = []

        # 1. Suspiciously High Win Rate with Strong Profit Factor
        if win_rate_pct >= 82.0 and profit_factor >= 3.0:
            red_flags.append(f"Suspiciously high win rate ({win_rate_pct}%) with PF {profit_factor}. High likelihood of curve-fitting.")

        # 2. Extreme Sharpe Ratio
        if sharpe_ratio >= 4.0:
            red_flags.append(f"Unrealistic Sharpe Ratio ({sharpe_ratio}). Institutional standard rarely exceeds 3.0 without look-ahead bias.")

        # 3. Holy Grail SQN Warning
        if sqn >= 7.0:
            red_flags.append(f"Van Tharp SQN ({sqn}) exceeds Holy Grail threshold (7.0). Likely overfit to historical noise.")

        # 4. Inadequate Statistical Sample Size
        if total_trades < 30:
            red_flags.append(f"Insufficient trade sample size ({total_trades} trades). Minimum 30-100 trades required for validity.")

        # 5. Zero Losing Streak Anomaly
        if max_consecutive_losses <= 0 and total_trades >= 15:
            red_flags.append("Zero consecutive losses detected. Highly abnormal in financial markets; check for forward bias.")

        # 6. Walk-Forward Degradation (OOS Collapse)
        if walk_forward_efficiency < 0.35:
            red_flags.append(f"Out-of-sample Walk-Forward Efficiency ({walk_forward_efficiency}) collapsed below 0.35. Strategy is non-generalizable.")

        is_flagged = len(red_flags) > 0
        verdict = "REJECTED_CURVE_FITTED" if len(red_flags) >= 2 else ("CAUTION_FLAGGED" if len(red_flags) == 1 else "CLEAN_AUDIT_PASSED")

        return {
            "is_overfit_suspect": is_flagged,
            "red_flags_count": len(red_flags),
            "red_flags": red_flags,
            "audit_verdict": verdict,
            "passes_audit": not is_flagged
        }
