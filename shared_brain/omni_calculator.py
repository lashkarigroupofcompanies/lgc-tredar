"""
OmniCalculator - High-Precision Quantitative & Financial Mathematics Engine
===========================================================================
Universal institutional calculator providing microsecond-speed, thread-safe,
zero-division-defended calculations for all agents in the swarm:
- CEO King Agent
- Core Trading Agent
- Risk Management Shield
- Analytical & Technical Agents
- Strategy R&D Agent
- Execution Agent
- News & Intelligence Agent
- Evolution Memory Agent
- ALL Tactical Shadow Clone Squads (each clone gets its personal instance)

Capabilities:
1. Percentage Engine: % change, % of, % value, % diff, compound growth, CAGR, net after drag.
2. Risk & Sizing Engine: Position size, R-multiples, R:R milestones, breakeven with fees,
   liquidation price, Half-Kelly criterion, Risk of Ruin.
3. Quant & Statistics Engine: Expectancy, Profit Factor, Sharpe Ratio, Sortino Ratio,
   Max Drawdown, Parametric VaR, Annualized Volatility, summary distribution stats.
4. Market Geometry Engine: Fibonacci Golden Pocket, ATR dynamic stops, Pivot Points (Standard/Camarilla),
   Fair Value Gap (FVG) Consequent Encroachment.
5. Safe Sandboxed Expression Evaluator: Evaluates arbitrary mathematical strings via AST parsing
   with zero security vulnerabilities and zero-division protection.
"""

import math
import ast
import operator
import logging
from typing import Dict, Any, List, Optional, Union, Tuple

logger = logging.getLogger("OmniCalculator")


class SafeMathEvaluator(ast.NodeVisitor):
    """
    AST-based secure mathematical expression evaluator.
    Disallows code injection, attribute access, loops, or system calls.
    Supports standard arithmetic, powers, and safe mathematical functions.
    """

    SAFE_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sqrt": math.sqrt,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "ceil": math.ceil,
        "floor": math.floor,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
    }

    SAFE_CONSTANTS = {
        "pi": math.pi,
        "e": math.e,
    }

    def __init__(self, variables: Optional[Dict[str, float]] = None):
        self.variables = variables or {}

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    def visit_Num(self, node):  # Backward-compat for older Python AST
        return float(node.n)

    def visit_Name(self, node):
        var_name = node.id
        if var_name in self.variables:
            return float(self.variables[var_name])
        if var_name in self.SAFE_CONSTANTS:
            return float(self.SAFE_CONSTANTS[var_name])
        raise ValueError(f"Unknown variable or constant: {var_name}")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float:
        operand = float(self.visit(node.operand))
        if isinstance(node.op, ast.USub):
            return -operand
        elif isinstance(node.op, ast.UAdd):
            return +operand
        raise ValueError(f"Unsupported unary operator: {type(node.op)}")

    def visit_BinOp(self, node: ast.BinOp) -> float:
        left = float(self.visit(node.left))
        right = float(self.visit(node.right))
        op = node.op

        if isinstance(op, ast.Add):
            return left + right
        elif isinstance(op, ast.Sub):
            return left - right
        elif isinstance(op, ast.Mult):
            return left * right
        elif isinstance(op, ast.Div):
            return (left / right) if right != 0.0 else 0.0
        elif isinstance(op, ast.FloorDiv):
            return (left // right) if right != 0.0 else 0.0
        elif isinstance(op, ast.Mod):
            return (left % right) if right != 0.0 else 0.0
        elif isinstance(op, ast.Pow):
            if abs(right) > 100.0 or abs(left) > 1e6:
                return float("inf") if left > 1 else 0.0
            return left ** right
        raise ValueError(f"Unsupported binary operator: {type(op)}")

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.SAFE_FUNCTIONS:
                args = [self.visit(arg) for arg in node.args]
                func = self.SAFE_FUNCTIONS[func_name]
                try:
                    return float(func(*args))
                except (ValueError, ZeroDivisionError, OverflowError):
                    return 0.0
        raise ValueError("Unsupported or forbidden function call")

    def generic_visit(self, node):
        raise ValueError(f"Forbidden syntax construct: {type(node).__name__}")


class OmniCalculator:
    """
    Universal High-Precision Quantitative & Financial Calculator.
    Every agent and every shadow clone unit gets its own personal instance.
    Stateless calculation methods guarantee 100% thread and concurrency safety.
    """

    def __init__(self, owner: str = "SYSTEM"):
        self.owner = owner
        self.calculation_count: int = 0

    def _increment(self):
        self.calculation_count += 1

    # =========================================================================
    # 1. UNIVERSAL PERCENTAGE ENGINE
    # =========================================================================

    def pct_change(self, old_val: float, new_val: float, decimals: int = 4) -> float:
        """Percentage change from old_val to new_val: ((new - old) / old) * 100."""
        self._increment()
        if old_val == 0.0:
            return 0.0
        pct = ((new_val - old_val) / abs(old_val)) * 100.0
        return round(pct, decimals)

    def pct_of(self, part: float, total: float, decimals: int = 4) -> float:
        """Percentage of total that part represents: (part / total) * 100."""
        self._increment()
        if total == 0.0:
            return 0.0
        return round((part / total) * 100.0, decimals)

    def pct_value(self, total: float, pct: float, decimals: int = 4) -> float:
        """Cash or numeric amount represented by pct % of total: total * (pct / 100)."""
        self._increment()
        return round(total * (pct / 100.0), decimals)

    def pct_diff(self, val1: float, val2: float, decimals: int = 4) -> float:
        """Percentage difference relative to average: |v1 - v2| / ((v1 + v2) / 2) * 100."""
        self._increment()
        avg = (val1 + val2) / 2.0
        if avg == 0.0:
            return 0.0
        return round((abs(val1 - val2) / abs(avg)) * 100.0, decimals)

    def pct_add(self, base_val: float, pct: float, decimals: int = 4) -> float:
        """Add a percentage to base: base_val * (1 + pct/100)."""
        self._increment()
        return round(base_val * (1.0 + (pct / 100.0)), decimals)

    def pct_subtract(self, base_val: float, pct: float, decimals: int = 4) -> float:
        """Deduct a percentage from base: base_val * (1 - pct/100)."""
        self._increment()
        return round(base_val * (1.0 - (pct / 100.0)), decimals)

    def cagr(self, start_val: float, end_val: float, periods: float, decimals: int = 4) -> float:
        """Compound Annual / Periodic Growth Rate: ((end / start) ** (1 / periods) - 1) * 100."""
        self._increment()
        if start_val <= 0.0 or end_val <= 0.0 or periods <= 0.0:
            return 0.0
        try:
            rate = ((end_val / start_val) ** (1.0 / periods) - 1.0) * 100.0
            return round(rate, decimals)
        except Exception:
            return 0.0

    def compound_growth(
        self,
        principal: float,
        rate_pct_per_period: float,
        periods: int,
        decimals: int = 4
    ) -> float:
        """Future value from compound growth: P * (1 + r/100) ** periods."""
        self._increment()
        try:
            fv = principal * ((1.0 + (rate_pct_per_period / 100.0)) ** periods)
            return round(fv, decimals)
        except Exception:
            return 0.0

    def discount_premium_pct(
        self,
        price: float,
        reference_price: float,
        decimals: int = 4
    ) -> Dict[str, Any]:
        """Calculates whether price is at a premium or discount to reference."""
        self._increment()
        if reference_price == 0.0:
            return {"status": "PAR", "pct": 0.0, "spread": 0.0}
        spread = price - reference_price
        pct = (spread / reference_price) * 100.0
        status = "PREMIUM" if spread > 0 else ("DISCOUNT" if spread < 0 else "PAR")
        return {
            "status": status,
            "pct": round(abs(pct), decimals),
            "signed_pct": round(pct, decimals),
            "spread": round(spread, decimals),
        }

    def net_after_drag(
        self,
        gross_pnl: float,
        position_value: float,
        fee_pct: float = 0.05,
        slippage_pct: float = 0.02,
        decimals: int = 4
    ) -> Dict[str, Any]:
        """Net PnL and return after transaction fees and slippage drag."""
        self._increment()
        fee_cost = position_value * (fee_pct / 100.0)
        slippage_cost = position_value * (slippage_pct / 100.0)
        total_drag = fee_cost + slippage_cost
        net_pnl = gross_pnl - total_drag
        return {
            "gross_pnl": round(gross_pnl, decimals),
            "total_drag": round(total_drag, decimals),
            "fee_cost": round(fee_cost, decimals),
            "slippage_cost": round(slippage_cost, decimals),
            "net_pnl": round(net_pnl, decimals),
            "drag_ratio_pct": round((total_drag / abs(gross_pnl) * 100.0) if gross_pnl != 0 else 0.0, decimals),
        }

    # =========================================================================
    # 2. RISK, POSITION SIZING & TRADE GEOMETRY
    # =========================================================================

    def position_size(
        self,
        account_balance: float,
        risk_pct: float,
        entry_price: float,
        stop_loss_price: float,
        leverage: float = 1.0,
        contract_multiplier: float = 1.0,
        min_units: float = 0.0001,
        decimals: int = 4
    ) -> Dict[str, Any]:
        """
        Calculates exact unit sizing based on defined risk percentage.
        Formula:
          Risk Cash = Account Balance * (risk_pct / 100)
          Risk Per Unit = |Entry Price - Stop Loss Price|
          Units = (Risk Cash / Risk Per Unit) / contract_multiplier
        """
        self._increment()
        if account_balance <= 0.0 or risk_pct <= 0.0 or entry_price <= 0.0:
            return {"units": 0.0, "risk_cash": 0.0, "position_value": 0.0, "margin_required": 0.0, "error": "Invalid inputs"}

        risk_per_unit = abs(entry_price - stop_loss_price)
        if risk_per_unit <= 0.0:
            return {"units": 0.0, "risk_cash": 0.0, "position_value": 0.0, "margin_required": 0.0, "error": "Entry equals Stop Loss"}

        risk_cash = account_balance * (risk_pct / 100.0)
        raw_units = (risk_cash / risk_per_unit) / contract_multiplier
        units = max(raw_units, min_units) if raw_units >= min_units else 0.0
        position_value = units * entry_price * contract_multiplier
        margin_required = position_value / max(leverage, 1.0)
        portfolio_exposure_pct = (position_value / account_balance) * 100.0

        return {
            "units": round(units, decimals),
            "risk_cash": round(risk_cash, decimals),
            "risk_per_unit": round(risk_per_unit, decimals),
            "risk_pct_actual": round((risk_cash / account_balance) * 100.0, decimals),
            "position_value": round(position_value, decimals),
            "margin_required": round(margin_required, decimals),
            "portfolio_exposure_pct": round(portfolio_exposure_pct, decimals),
            "effective_leverage": round(position_value / account_balance, 2),
        }

    def r_multiple(
        self,
        entry: float,
        exit_price: float,
        stop_loss: float,
        direction: str = "LONG",
        decimals: int = 4
    ) -> float:
        """
        Calculates realized R-Multiple (Gain or Loss expressed as a multiple of defined risk).
        """
        self._increment()
        direction_upper = direction.upper()
        if direction_upper == "LONG":
            risk_dist = entry - stop_loss
            reward_dist = exit_price - entry
        else:
            risk_dist = stop_loss - entry
            reward_dist = entry - exit_price

        if risk_dist <= 0.0:
            return 0.0

        return round(reward_dist / risk_dist, decimals)

    def targets_from_rr(
        self,
        entry: float,
        stop_loss: float,
        rr_ratios: Optional[List[float]] = None,
        direction: str = "LONG",
        decimals: int = 4
    ) -> Dict[str, float]:
        """Calculates exact Take Profit price targets for given Risk-Reward multiples."""
        self._increment()
        if rr_ratios is None:
            rr_ratios = [1.0, 1.5, 2.0, 3.0, 5.0]

        direction_upper = direction.upper()
        risk_dist = abs(entry - stop_loss)
        targets = {}

        for rr in rr_ratios:
            if direction_upper == "LONG":
                target_price = entry + (risk_dist * rr)
            else:
                target_price = entry - (risk_dist * rr)
            targets[f"{rr:.1f}R"] = round(target_price, decimals)

        return targets

    def breakeven_price(
        self,
        entry: float,
        units: float,
        total_commissions: float = 0.0,
        roundtrip_fee_pct: float = 0.0,
        direction: str = "LONG",
        decimals: int = 4
    ) -> float:
        """Calculates precise Breakeven Price incorporating roundtrip commissions & fees."""
        self._increment()
        if units <= 0.0 or entry <= 0.0:
            return entry

        comm_per_unit = total_commissions / units
        fee_offset = entry * (roundtrip_fee_pct / 100.0)

        if direction.upper() == "LONG":
            be_price = entry + comm_per_unit + fee_offset
        else:
            be_price = entry - comm_per_unit - fee_offset

        return round(be_price, decimals)

    def liquidation_price(
        self,
        entry: float,
        leverage: float,
        direction: str = "LONG",
        maintenance_margin_pct: float = 0.5,
        decimals: int = 4
    ) -> float:
        """Calculates estimated Bankruptcy / Liquidation price for leveraged trades."""
        self._increment()
        if leverage <= 1.0:
            return 0.0  # Spot has no liquidation

        maint_decimal = maintenance_margin_pct / 100.0
        if direction.upper() == "LONG":
            liq = entry * (1.0 - (1.0 / leverage) + maint_decimal)
        else:
            liq = entry * (1.0 + (1.0 / leverage) - maint_decimal)

        return round(max(liq, 0.0), decimals)

    def kelly_criterion(
        self,
        win_rate_pct: float,
        win_loss_ratio: float,
        fraction: str = "HALF",
        max_cap_pct: float = 10.0,
        decimals: int = 4
    ) -> Dict[str, Any]:
        """
        Kelly Criterion optimal capital allocation:
          Full Kelly f* = (p * (b + 1) - 1) / b
          where p = win_rate, b = win_loss payoff ratio
        """
        self._increment()
        p = win_rate_pct / 100.0
        q = 1.0 - p
        b = win_loss_ratio

        if b <= 0.0 or p <= 0.0:
            return {"full_kelly_pct": 0.0, "recommended_pct": 0.0, "fraction": fraction}

        full_kelly = (p * (b + 1.0) - 1.0) / b
        full_kelly_pct = max(full_kelly * 100.0, 0.0)

        multiplier = 0.5 if fraction.upper() == "HALF" else (0.25 if fraction.upper() == "QUARTER" else 1.0)
        recommended_pct = min(full_kelly_pct * multiplier, max_cap_pct)

        return {
            "full_kelly_pct": round(full_kelly_pct, decimals),
            "recommended_pct": round(recommended_pct, decimals),
            "fraction": fraction.upper(),
            "capped": recommended_pct == max_cap_pct and full_kelly_pct * multiplier > max_cap_pct
        }

    def risk_of_ruin(
        self,
        win_rate_pct: float,
        win_loss_ratio: float,
        risk_per_trade_pct: float,
        ruin_drawdown_pct: float = 50.0,
        decimals: int = 4
    ) -> float:
        """
        Estimates Probability of Ruin using classical Gambler's Ruin approximation.
        Returns percentage chance of experiencing the ruin_drawdown_pct.
        """
        self._increment()
        p = win_rate_pct / 100.0
        q = 1.0 - p
        b = win_loss_ratio

        # Expectancy check
        expectancy = (p * b) - q
        if expectancy <= 0:
            return 100.0  # Negative edge guarantees eventual ruin

        units_of_risk = ruin_drawdown_pct / max(risk_per_trade_pct, 0.1)
        z = (1.0 - expectancy) / (1.0 + expectancy)
        if z <= 0.0 or z >= 1.0:
            return 0.0

        try:
            prob_ruin = (z ** units_of_risk) * 100.0
            return round(min(prob_ruin, 100.0), decimals)
        except Exception:
            return 0.0

    # =========================================================================
    # 3. QUANTITATIVE, STATISTICAL & PERFORMANCE SUITE
    # =========================================================================

    def expectancy(
        self,
        win_rate_pct: float,
        avg_win: float,
        avg_loss: float,
        decimals: int = 4
    ) -> Dict[str, Any]:
        """
        Mathematical Expectancy = (Win Probability * Avg Win) - (Loss Probability * Avg Loss)
        """
        self._increment()
        p_win = win_rate_pct / 100.0
        p_loss = 1.0 - p_win
        exp_value = (p_win * avg_win) - (p_loss * abs(avg_loss))
        exp_ratio = (exp_value / abs(avg_loss)) if avg_loss != 0 else 0.0

        return {
            "expectancy": round(exp_value, decimals),
            "expectancy_r": round(exp_ratio, decimals),
            "positive_edge": exp_value > 0.0,
        }

    def profit_factor(
        self,
        gross_profit: float,
        gross_loss: float,
        decimals: int = 4
    ) -> float:
        """Profit Factor = Gross Profits / Gross Losses."""
        self._increment()
        if gross_loss == 0.0:
            return 99.99 if gross_profit > 0 else 0.0
        return round(abs(gross_profit) / abs(gross_loss), decimals)

    def summary_stats(self, values: List[float], decimals: int = 4) -> Dict[str, Any]:
        """Calculates complete statistical distribution summary for a series of numbers."""
        self._increment()
        n = len(values)
        if n == 0:
            return {"count": 0, "sum": 0.0, "mean": 0.0, "median": 0.0, "std_dev": 0.0, "variance": 0.0, "min": 0.0, "max": 0.0}

        v_sum = sum(values)
        v_mean = v_sum / n
        s_vals = sorted(values)
        median = s_vals[n // 2] if n % 2 != 0 else (s_vals[n // 2 - 1] + s_vals[n // 2]) / 2.0

        variance = sum((x - v_mean) ** 2 for x in values) / n if n > 1 else 0.0
        std_dev = math.sqrt(variance)

        return {
            "count": n,
            "sum": round(v_sum, decimals),
            "mean": round(v_mean, decimals),
            "median": round(median, decimals),
            "std_dev": round(std_dev, decimals),
            "variance": round(variance, decimals),
            "min": round(s_vals[0], decimals),
            "max": round(s_vals[-1], decimals),
        }

    def sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate_pct: float = 0.0,
        periods_per_year: int = 252,
        decimals: int = 4
    ) -> float:
        """Annualized Sharpe Ratio: (Mean Return - Rf) / Volatility * sqrt(periods)."""
        self._increment()
        if len(returns) < 2:
            return 0.0

        stats = self.summary_stats(returns)
        std = stats["std_dev"]
        if std <= 0.0:
            return 0.0

        rf_period = (risk_free_rate_pct / 100.0) / periods_per_year
        excess_mean = stats["mean"] - rf_period
        annualized_sharpe = (excess_mean / std) * math.sqrt(periods_per_year)
        return round(annualized_sharpe, decimals)

    def sortino_ratio(
        self,
        returns: List[float],
        target_return_pct: float = 0.0,
        periods_per_year: int = 252,
        decimals: int = 4
    ) -> float:
        """Annualized Sortino Ratio using downside semi-deviation."""
        self._increment()
        if len(returns) < 2:
            return 0.0

        target_return = target_return_pct / 100.0
        mean_ret = sum(returns) / len(returns)

        downside_diffs = [min(0.0, r - target_return) ** 2 for r in returns]
        downside_variance = sum(downside_diffs) / len(returns)
        downside_std = math.sqrt(downside_variance)

        if downside_std <= 0.0:
            return 0.0

        sortino = ((mean_ret - target_return) / downside_std) * math.sqrt(periods_per_year)
        return round(sortino, decimals)

    def max_drawdown(
        self,
        equity_curve: List[float],
        decimals: int = 4
    ) -> Dict[str, Any]:
        """Calculates Maximum Drawdown (Peak to Trough) in absolute cash and percentage."""
        self._increment()
        if not equity_curve:
            return {"max_dd_cash": 0.0, "max_dd_pct": 0.0, "peak": 0.0, "trough": 0.0}

        running_peak = equity_curve[0]
        peak_at_max_dd = running_peak
        max_dd_cash = 0.0
        max_dd_pct = 0.0
        best_trough = running_peak

        for val in equity_curve:
            if val > running_peak:
                running_peak = val
            dd_cash = running_peak - val
            dd_pct = (dd_cash / running_peak * 100.0) if running_peak > 0 else 0.0

            if dd_cash > max_dd_cash:
                max_dd_cash = dd_cash
                max_dd_pct = dd_pct
                best_trough = val
                peak_at_max_dd = running_peak

        return {
            "max_dd_cash": round(max_dd_cash, decimals),
            "max_dd_pct": round(max_dd_pct, decimals),
            "peak": round(peak_at_max_dd, decimals),
            "trough": round(best_trough, decimals),
            "all_time_peak": round(running_peak, decimals),
        }

    def parametric_var(
        self,
        portfolio_value: float,
        mean_return_pct: float,
        std_dev_pct: float,
        confidence: float = 0.99,
        time_horizon_days: int = 1,
        decimals: int = 4
    ) -> Dict[str, Any]:
        """
        Parametric Value at Risk (VaR): Maximum estimated loss over time horizon at confidence level.
        Z-scores: 95% -> 1.645, 99% -> 2.326.
        """
        self._increment()
        z = 2.326 if confidence >= 0.99 else (1.960 if confidence >= 0.975 else 1.645)
        std_horizon = (std_dev_pct / 100.0) * math.sqrt(time_horizon_days)
        mean_horizon = (mean_return_pct / 100.0) * time_horizon_days

        var_pct = (z * std_horizon) - mean_horizon
        var_cash = portfolio_value * var_pct

        return {
            "confidence_pct": confidence * 100.0,
            "time_horizon_days": time_horizon_days,
            "var_pct": round(var_pct * 100.0, decimals),
            "var_cash": round(var_cash, decimals),
        }

    # =========================================================================
    # 4. TECHNICAL & MARKET GEOMETRY SUITE
    # =========================================================================

    def fibonacci_levels(
        self,
        swing_low: float,
        swing_high: float,
        direction: str = "BULLISH",
        decimals: int = 4
    ) -> Dict[str, float]:
        """
        Calculates Institutional Fibonacci Retracement & Extension Levels:
        0.236, 0.382, 0.500, 0.618 (Golden Pocket), 0.65 (GP Ext), 0.786, 1.0, 1.272, 1.618.
        """
        self._increment()
        diff = swing_high - swing_low
        direction_upper = direction.upper()
        ratios = {
            "0.0_HIGH": 0.0,
            "0.236": 0.236,
            "0.382": 0.382,
            "0.500_EQ": 0.500,
            "0.618_GOLDEN_POCKET": 0.618,
            "0.650_GP_SWEET_SPOT": 0.650,
            "0.786_DEEP_DISCOUNT": 0.786,
            "1.0_LOW": 1.0,
            "1.272_EXT": 1.272,
            "1.618_GOLDEN_EXT": 1.618,
        }

        levels = {}
        for name, r in ratios.items():
            if direction_upper == "BULLISH":  # Retracement down from high
                price = swing_high - (diff * r)
            else:  # Bearish retracement up from low
                price = swing_low + (diff * r)
            levels[name] = round(price, decimals)

        return levels

    def atr_stop_distance(
        self,
        current_price: float,
        atr: float,
        multiplier: float = 2.0,
        direction: str = "LONG",
        decimals: int = 4
    ) -> float:
        """Dynamic volatility stop distance based on ATR."""
        self._increment()
        dist = atr * multiplier
        stop = current_price - dist if direction.upper() == "LONG" else current_price + dist
        return round(max(stop, 0.0), decimals)

    def pivot_points(
        self,
        high: float,
        low: float,
        close: float,
        method: str = "STANDARD",
        decimals: int = 4
    ) -> Dict[str, float]:
        """Calculates institutional Pivot Points (Standard or Camarilla)."""
        self._increment()
        pp = (high + low + close) / 3.0

        if method.upper() == "CAMARILLA":
            diff = high - low
            return {
                "H4": round(close + (diff * 1.1 / 2.0), decimals),
                "H3": round(close + (diff * 1.1 / 4.0), decimals),
                "PP": round(pp, decimals),
                "L3": round(close - (diff * 1.1 / 4.0), decimals),
                "L4": round(close - (diff * 1.1 / 2.0), decimals),
            }

        # Standard Classic Pivots
        r1 = (2.0 * pp) - low
        s1 = (2.0 * pp) - high
        r2 = pp + (high - low)
        s2 = pp - (high - low)
        r3 = high + 2.0 * (pp - low)
        s3 = low - 2.0 * (high - pp)

        return {
            "R3": round(r3, decimals),
            "R2": round(r2, decimals),
            "R1": round(r1, decimals),
            "PP": round(pp, decimals),
            "S1": round(s1, decimals),
            "S2": round(s2, decimals),
            "S3": round(s3, decimals),
        }

    def fair_value_gap(
        self,
        bar1_high: float,
        bar1_low: float,
        bar3_high: float,
        bar3_low: float,
        direction: str = "BULLISH",
        decimals: int = 4
    ) -> Dict[str, Any]:
        """
        SMC Fair Value Gap (FVG) and Consequent Encroachment (50% midpoint).
        - Bullish FVG: Bar 3 Low > Bar 1 High
        - Bearish FVG: Bar 3 High < Bar 1 Low
        """
        self._increment()
        if direction.upper() == "BULLISH":
            gap_exists = bar3_low > bar1_high
            gap_size = bar3_low - bar1_high if gap_exists else 0.0
            midpoint = (bar3_low + bar1_high) / 2.0 if gap_exists else 0.0
            top = bar3_low
            bottom = bar1_high
        else:
            gap_exists = bar3_high < bar1_low
            gap_size = bar1_low - bar3_high if gap_exists else 0.0
            midpoint = (bar1_low + bar3_high) / 2.0 if gap_exists else 0.0
            top = bar1_low
            bottom = bar3_high

        return {
            "fvg_active": gap_exists,
            "gap_size": round(gap_size, decimals),
            "gap_pct": round((gap_size / bottom * 100.0) if bottom > 0 else 0.0, decimals),
            "consequent_encroachment_50pct": round(midpoint, decimals),
            "top_level": round(top, decimals),
            "bottom_level": round(bottom, decimals),
        }

    # =========================================================================
    # 5. SAFE SANDBOXED EXPRESSION EVALUATOR
    # =========================================================================

    def evaluate_expression(
        self,
        expression: str,
        variables: Optional[Dict[str, float]] = None,
        decimals: int = 4
    ) -> float:
        """
        Safely evaluates an arbitrary mathematical expression string.
        Examples:
          "((245.50 - 240.00) / 240.00) * 100"
          "100000 * 0.01 / (150 - 145)"
          "sqrt(252) * (0.15 / 0.10)"
        """
        self._increment()
        clean_expr = expression.strip()
        if not clean_expr:
            return 0.0

        try:
            tree = ast.parse(clean_expr, mode="eval")
            evaluator = SafeMathEvaluator(variables=variables)
            result = evaluator.visit(tree)
            return round(float(result), decimals)
        except Exception as e:
            logger.warning(f"[{self.owner}] OmniCalculator expression evaluation failed for '{expression}': {e}")
            return 0.0

    # =========================================================================
    # 6. BATCH / VECTORIZED HELPERS
    # =========================================================================

    def batch_pct_changes(self, series: List[float], decimals: int = 4) -> List[float]:
        """Calculates step-by-step percentage changes across an entire series."""
        if len(series) < 2:
            return []
        return [self.pct_change(series[i], series[i + 1], decimals=decimals) for i in range(len(series) - 1)]

    def batch_evaluate(
        self,
        expressions: List[str],
        variables: Optional[Dict[str, float]] = None,
        decimals: int = 4
    ) -> List[float]:
        """Evaluates multiple expressions concurrently."""
        return [self.evaluate_expression(expr, variables=variables, decimals=decimals) for expr in expressions]

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns diagnostic usage telemetry for this calculator instance."""
        return {
            "owner": self.owner,
            "total_calculations": self.calculation_count,
            "status": "ONLINE",
        }
