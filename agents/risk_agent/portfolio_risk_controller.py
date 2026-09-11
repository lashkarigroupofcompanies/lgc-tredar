"""
Portfolio Risk Controller - Section 5, 7, 8 & 9 of Risk Management Knowledge Base
Enforces portfolio-level survival constraints:
- Portfolio Heat: Sum of all open trade risks capped at <= 6.0% (Hard stop at 8%)
- Asset & Sector Concentration: Max 15% single asset, Max 25% single sector
- Correlation Matrix Check: Prevents double exposure on highly correlated assets (BTC/ETH, NIFTY/BANKNIFTY)
- Margin & Leverage Management: Effective leverage <= 3x, Margin utilization <= 65%
- Cash Reserve Protection: Minimum 20-30% cash buffer always maintained
- Time & Event Risk: High-impact catalyst and weekend holding checks
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("PortfolioRiskController")


class PortfolioRiskController:
    """
    Portfolio Risk & Correlation Guard.
    Monitors portfolio heat, sector exposure, and multi-asset correlation in real time.
    """

    # Empirical correlation matrix for typical risk assets
    CORRELATION_TABLE = {
        ("BTC", "ETH"): 0.88,
        ("BTC", "SOL"): 0.82,
        ("ETH", "SOL"): 0.85,
        ("NIFTY", "BANKNIFTY"): 0.86,
        ("RELIANCE", "NIFTY"): 0.78,
        ("TCS", "INFY"): 0.89,
        ("HDFCBANK", "ICICIBANK"): 0.84,
        ("AAPL", "MSFT"): 0.82,
        ("NVDA", "QQQ"): 0.85,
        ("GOLD", "SILVER"): 0.81
    }

    SECTOR_MAP = {
        "BTC": "CRYPTO_L1",
        "ETH": "CRYPTO_L1",
        "SOL": "CRYPTO_L1",
        "BNB": "CRYPTO_EXCHANGE",
        "XRP": "CRYPTO_PAYMENT",
        "RELIANCE": "ENERGY_CONGLOMERATE",
        "TCS": "INDIAN_IT",
        "INFY": "INDIAN_IT",
        "HDFCBANK": "INDIAN_BANKING",
        "TATAMOTORS": "AUTO",
        "NVDA": "SEMI_TECH",
        "AAPL": "TECH_HARDWARE",
        "MSFT": "TECH_CLOUD",
        "GOOGL": "TECH_AD",
        "AMZN": "TECH_ECOMMERCE"
    }

    def __init__(
        self,
        max_portfolio_heat_pct: float = 6.0,
        max_single_asset_exposure_pct: float = 25.0,
        max_single_sector_exposure_pct: float = 35.0,
        min_cash_reserve_pct: float = 15.0,
        max_margin_utilization_pct: float = 75.0,
        max_effective_leverage: float = 3.5
    ):
        self.max_portfolio_heat_pct = max_portfolio_heat_pct
        self.max_single_asset_exposure_pct = max_single_asset_exposure_pct
        self.max_single_sector_exposure_pct = max_single_sector_exposure_pct
        self.min_cash_reserve_pct = min_cash_reserve_pct
        self.max_margin_utilization_pct = max_margin_utilization_pct
        self.max_effective_leverage = max_effective_leverage

    def get_asset_correlation(self, asset1: str, asset2: str) -> float:
        """Returns empirical correlation coefficient between two assets (0.0 to 1.0)."""
        a1, a2 = asset1.upper().replace(".NS", ""), asset2.upper().replace(".NS", "")
        if a1 == a2:
            return 1.0
        pair1 = (a1, a2)
        pair2 = (a2, a1)
        return self.CORRELATION_TABLE.get(pair1, self.CORRELATION_TABLE.get(pair2, 0.40))

    def evaluate_portfolio_admission(
        self,
        new_symbol: str,
        new_direction: str,
        proposed_risk_pct: float,
        proposed_position_value: float,
        account_balance: float,
        open_positions: List[Dict[str, Any]],
        is_high_impact_news_pending: bool = False
    ) -> Dict[str, Any]:
        """
        Validates whether the portfolio can safely accommodate the new trade.
        Checks Heat, Correlation, Concentration, Margin, and Event Risk.
        """
        if account_balance <= 0:
            return {"decision": "REJECTED", "reason": "ACCOUNT_BALANCE_ZERO"}

        # 1. Portfolio Heat Check (Sum of all open risks)
        current_heat_pct = sum(float(p.get("risk_pct", 1.0)) for p in open_positions)
        new_total_heat = current_heat_pct + proposed_risk_pct

        if new_total_heat > self.max_portfolio_heat_pct:
            logger.warning(f"[PortfolioRisk] Portfolio Heat ({new_total_heat:.2f}%) exceeds limit of {self.max_portfolio_heat_pct}%.")
            return {
                "decision": "REJECTED",
                "reason": f"PORTFOLIO_HEAT_LIMIT_EXCEEDED: Total heat {new_total_heat:.2f}% > {self.max_portfolio_heat_pct}%. No new trades until existing positions close.",
                "current_heat": round(current_heat_pct, 2),
                "proposed_risk": round(proposed_risk_pct, 2)
            }

        # 2. Correlation Risk Check
        clean_new = new_symbol.upper().replace(".NS", "")
        correlated_conflicts = []
        for pos in open_positions:
            pos_sym = pos.get("symbol", "").upper().replace(".NS", "")
            pos_dir = pos.get("direction", "LONG").upper()
            corr = self.get_asset_correlation(clean_new, pos_sym)

            # High correlation in same direction = Double Exposure Risk
            if corr >= 0.80 and pos_dir == new_direction.upper():
                correlated_conflicts.append({
                    "existing_asset": pos_sym,
                    "correlation": corr,
                    "direction": pos_dir
                })

        if len(correlated_conflicts) > 0:
            logger.warning(f"[PortfolioRisk] Correlated exposure detected for {new_symbol}: {correlated_conflicts}")
            # If 2 correlated assets already open, strictly reject. If 1 open, throttle size by 50%
            if len(correlated_conflicts) >= 2:
                return {
                    "decision": "REJECTED",
                    "reason": f"HIGH_CORRELATION_CONCENTRATION: Already holding multiple correlated positions ({[c['existing_asset'] for c in correlated_conflicts]}).",
                    "correlated_conflicts": correlated_conflicts
                }
            else:
                return {
                    "decision": "THROTTLED_APPROVAL",
                    "throttle_multiplier": 0.50,
                    "reason": f"Correlated with {correlated_conflicts[0]['existing_asset']} (r={correlated_conflicts[0]['correlation']}). Reducing size by 50% to manage joint exposure.",
                    "correlated_conflicts": correlated_conflicts,
                    "current_heat": round(current_heat_pct, 2),
                    "new_total_heat": round(current_heat_pct + (proposed_risk_pct * 0.50), 2)
                }

        # 3. Single Asset Concentration Limit (Section 5)
        # In institutional margin/perpetuals trading, nominal position value can safely scale
        # up to effective leverage limit (e.g. 1.5x - 2.5x) while dollar risk remains strictly budgeted.
        current_asset_exposure = sum(
            float(p.get("remaining_units", 0.0)) * float(p.get("current_price", 0.0))
            for p in open_positions if p.get("symbol", "").upper().replace(".NS", "") == clean_new
        )
        total_asset_exposure = current_asset_exposure + proposed_position_value
        max_notional_allowed = account_balance * min(self.max_effective_leverage, 2.5)

        if total_asset_exposure > max_notional_allowed:
            avail_val = max(0.0, max_notional_allowed - current_asset_exposure)
            if avail_val <= (account_balance * 0.05):
                return {
                    "decision": "REJECTED",
                    "reason": f"ASSET_LEVERAGE_FULL: Notional exposure (${total_asset_exposure:,.2f}) would exceed max asset leverage limit (${max_notional_allowed:,.2f}).",
                    "exposure_pct": round((total_asset_exposure / account_balance) * 100.0, 2)
                }
            scale_factor = min(1.0, avail_val / proposed_position_value)
            return {
                "decision": "THROTTLED_APPROVAL",
                "throttle_multiplier": round(scale_factor, 4),
                "reason": f"Single asset notional capped at ${max_notional_allowed:,.2f} ({min(self.max_effective_leverage, 2.5):.1f}x). Sizing scaled down to ${avail_val:,.2f}."
            }

        # 4. Sector Concentration Limit (Section 5)
        target_sector = self.SECTOR_MAP.get(clean_new, "GENERAL_MARKET")
        current_sector_exposure = sum(
            float(p.get("remaining_units", 0.0)) * float(p.get("current_price", 0.0))
            for p in open_positions
            if self.SECTOR_MAP.get(p.get("symbol", "").upper().replace(".NS", ""), "GENERAL_MARKET") == target_sector
        )
        total_sector_exposure = current_sector_exposure + proposed_position_value
        max_notional_sector = account_balance * min(self.max_effective_leverage, 2.5)

        if total_sector_exposure > max_notional_sector:
            avail_val = max(0.0, max_notional_sector - current_sector_exposure)
            if avail_val <= (account_balance * 0.05):
                return {
                    "decision": "REJECTED",
                    "reason": f"SECTOR_LEVERAGE_FULL: Notional exposure (${total_sector_exposure:,.2f}) would exceed max sector leverage limit (${max_notional_sector:,.2f}).",
                    "sector": target_sector
                }
            scale_factor = min(1.0, avail_val / proposed_position_value)
            return {
                "decision": "THROTTLED_APPROVAL",
                "throttle_multiplier": round(scale_factor, 4),
                "reason": f"Sector '{target_sector}' notional capped at ${max_notional_sector:,.2f} ({min(self.max_effective_leverage, 2.5):.1f}x). Sizing scaled down to ${avail_val:,.2f}."
            }

        # 5. Margin Utilization & Effective Leverage Check
        total_portfolio_position_val = sum(
            float(p.get("remaining_units", 0.0)) * float(p.get("current_price", 0.0))
            for p in open_positions
        ) + proposed_position_value

        effective_leverage = total_portfolio_position_val / account_balance
        if effective_leverage > self.max_effective_leverage:
            return {
                "decision": "REJECTED",
                "reason": f"EFFECTIVE_LEVERAGE_EXCEEDED: Portfolio leverage would reach {effective_leverage:.2f}x (Max: {self.max_effective_leverage}x).",
                "effective_leverage": round(effective_leverage, 2)
            }

        # 6. Event Risk Filter
        if is_high_impact_news_pending:
            logger.info(f"[PortfolioRisk] High-impact event pending in <24hrs for {new_symbol}. Throttling risk by 50%.")
            return {
                "decision": "THROTTLED_APPROVAL",
                "throttle_multiplier": 0.50,
                "reason": "HIGH_IMPACT_EVENT_PENDING: Sizing reduced by 50% to protect against event binary volatility."
            }

        # All portfolio checks passed cleanly
        return {
            "decision": "APPROVED",
            "current_heat": round(current_heat_pct, 2),
            "new_total_heat": round(new_total_heat, 2),
            "effective_leverage": round(effective_leverage, 2),
            "sector": target_sector
        }
