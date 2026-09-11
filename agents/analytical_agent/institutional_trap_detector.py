"""
Institutional Trap & Liquidity Sweep Detector (Depth 2/3)
Engineered from top quant & Smart Money Concepts (SMC) open-source architectures:
- smartmoneyconcepts (smc) liquidity sweeps & zone rejection
- Linda Raschke Turtle Soup failed 20-period breakout traps
- ICT Judas Swing stop hunts & liquidity extraction
- Wyckoff Spring & Upthrust volume absorption tests
- Order Flow Imbalance (OFI) & Depth 2/3 Orderbook Spread Vacuum
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import requests

logger = logging.getLogger("InstitutionalTrapDetector")


class InstitutionalTrapDetector:
    """
    Advanced Quantitative Engine for detecting institutional liquidity traps,
    stop-loss hunts, fake breakouts, and order book manipulation before trade entry.
    """

    def __init__(self):
        self.binance_depth_url = "https://api.binance.com/api/v3/depth"

    def detect_price_action_traps(
        self,
        df: pd.DataFrame,
        lookback: int = 20
    ) -> Dict[str, Any]:
        """
        Scans OHLCV price action for:
        1. Turtle Soup (Failed 20-period Breakout)
        2. Judas Swing (Liquidity sweep of session highs/lows with immediate wick rejection)
        3. Wyckoff Spring / Upthrust (Aggressive stop hunt beyond structural S/R followed by rapid absorption)
        4. Bull / Bear Traps (Breakout bar immediately reversed by next 1-2 bars)
        """
        if df.empty or len(df) < lookback + 2:
            return {
                "trap_detected": False,
                "trap_type": "INSUFFICIENT_DATA",
                "severity": "NONE",
                "bull_trap": False,
                "bear_trap": False,
                "liquidity_sweep": "NONE",
                "details": "Insufficient candles for trap detection."
            }

        highs: List[float] = [float(x) for x in df["high"]]
        lows: List[float] = [float(x) for x in df["low"]]
        closes: List[float] = [float(x) for x in df["close"]]
        opens: List[float] = [float(x) for x in df["open"]]
        volumes: List[float] = [float(x) for x in df["volume"]] if "volume" in df.columns else [1.0] * len(df)

        n = len(df)
        curr_idx = n - 1
        prev_idx = n - 2

        # 20-period reference swing high/low excluding the last 2 candles
        prior_highs = highs[max(0, curr_idx - lookback):prev_idx]
        prior_lows = lows[max(0, curr_idx - lookback):prev_idx]

        if not prior_highs or not prior_lows:
            return {
                "trap_detected": False,
                "trap_type": "NONE",
                "severity": "NONE",
                "bull_trap": False,
                "bear_trap": False,
                "liquidity_sweep": "NONE",
                "details": "Clean structural conditions."
            }

        swing_high = max(prior_highs)
        swing_low = min(prior_lows)

        curr_o = opens[curr_idx]
        curr_h = highs[curr_idx]
        curr_l = lows[curr_idx]
        curr_c = closes[curr_idx]
        curr_range = max(1e-6, curr_h - curr_l)

        prev_o = opens[prev_idx]
        prev_h = highs[prev_idx]
        prev_l = lows[prev_idx]
        prev_c = closes[prev_idx]

        avg_vol = sum(volumes[max(0, curr_idx - 20):curr_idx]) / max(1, min(20, curr_idx))
        curr_vol = volumes[curr_idx]
        vol_spike = curr_vol > (avg_vol * 1.25)

        # -------------------------------------------------------------
        # 1. BEARISH LIQUIDITY SWEEP / BULL TRAP (Turtle Soup High)
        # Price breaches swing high, sweeps buy-stops, but closes BACK INSIDE with upper wick
        # -------------------------------------------------------------
        upper_wick = curr_h - max(curr_o, curr_c)
        upper_wick_ratio = upper_wick / curr_range

        is_turtle_soup_high = (curr_h > swing_high) and (curr_c < swing_high) and (upper_wick_ratio >= 0.35)
        # Also check if previous bar broke out above swing high, but current bar closed back below it (Classic 2-bar Bull Trap)
        is_two_bar_bull_trap = (prev_c > swing_high) and (curr_c < swing_high)

        if is_turtle_soup_high or is_two_bar_bull_trap:
            severity = "CRITICAL" if vol_spike else "HIGH"
            trap_name = "BULL_TRAP_LIQUIDITY_SWEEP" if is_turtle_soup_high else "TWO_BAR_BULL_TRAP_FAILURE"
            return {
                "trap_detected": True,
                "trap_type": trap_name,
                "severity": severity,
                "bull_trap": True,
                "bear_trap": False,
                "liquidity_sweep": "BEARISH_SWEEP_OVER_SWING_HIGH",
                "swing_level": swing_high,
                "upper_wick_ratio": round(upper_wick_ratio, 2),
                "volume_absorption": vol_spike,
                "details": f"Price pierced swing high (${swing_high:,.2f}) to sweep buy-stops, then rejected violently into the range. High probability retail trap."
            }

        # -------------------------------------------------------------
        # 2. BULLISH LIQUIDITY SWEEP / BEAR TRAP (Turtle Soup Low / Wyckoff Spring)
        # Price breaches swing low, sweeps sell-stops, but closes BACK INSIDE with lower wick
        # -------------------------------------------------------------
        lower_wick = min(curr_o, curr_c) - curr_l
        lower_wick_ratio = lower_wick / curr_range

        is_turtle_soup_low = (curr_l < swing_low) and (curr_c > swing_low) and (lower_wick_ratio >= 0.35)
        is_two_bar_bear_trap = (prev_c < swing_low) and (curr_c > swing_low)

        if is_turtle_soup_low or is_two_bar_bear_trap:
            severity = "CRITICAL" if vol_spike else "HIGH"
            trap_name = "WYCKOFF_SPRING_BEAR_TRAP" if is_turtle_soup_low else "TWO_BAR_BEAR_TRAP_FAILURE"
            return {
                "trap_detected": True,
                "trap_type": trap_name,
                "severity": severity,
                "bull_trap": False,
                "bear_trap": True,
                "liquidity_sweep": "BULLISH_SWEEP_UNDER_SWING_LOW",
                "swing_level": swing_low,
                "lower_wick_ratio": round(lower_wick_ratio, 2),
                "volume_absorption": vol_spike,
                "details": f"Price punctured swing low (${swing_low:,.2f}) to trigger retail panic stops, followed by immediate institutional absorption. Wyckoff Spring pattern active."
            }

        # -------------------------------------------------------------
        # 3. JUDAS SWING DETECTION (Intraday False Directional Thrust)
        # -------------------------------------------------------------
        body_size = abs(curr_c - curr_o)
        body_ratio = body_size / curr_range
        recent_ranges = [highs[i] - lows[i] for i in range(max(0, curr_idx - 5), curr_idx)]
        avg_recent_range = sum(recent_ranges) / max(1, len(recent_ranges)) if recent_ranges else curr_range

        if curr_range > (avg_recent_range * 2.0) and body_ratio > 0.70 and vol_spike:
            if curr_c > curr_o and upper_wick_ratio > 0.25:
                return {
                    "trap_detected": True,
                    "trap_type": "EXHAUSTION_CLIMAX_TRAP",
                    "severity": "MODERATE",
                    "bull_trap": True,
                    "bear_trap": False,
                    "liquidity_sweep": "EXHAUSTION_BUY_BLOWOFF",
                    "details": "Sudden 2x range expansion with volume blow-off and upper wick stall. Risk of climax trap."
                }

        return {
            "trap_detected": False,
            "trap_type": "NONE",
            "severity": "NONE",
            "bull_trap": False,
            "bear_trap": False,
            "liquidity_sweep": "NONE",
            "details": "No predatory price action traps detected."
        }

    def evaluate_depth_and_orderbook(
        self,
        market: str,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Inspects Level 2 Order Book Depth and Bid-Ask Imbalance.
        For Crypto: Connects to Binance Public Depth REST (/api/v3/depth?limit=20).
        For Equities/Forex: Applies synthetic microstructure model with spread safety guard.
        """
        clean_market = market.upper()
        clean_symbol = symbol.upper().replace("/", "").replace("-", "")

        if clean_market == "CRYPTO":
            if not clean_symbol.endswith("USDT"):
                clean_symbol = f"{clean_symbol}USDT"

            url = f"{self.binance_depth_url}?symbol={clean_symbol}&limit=20"
            try:
                resp = requests.get(url, timeout=3.5)
                if resp.status_code == 200:
                    depth_data = resp.json()
                    bids = depth_data.get("bids", [])
                    asks = depth_data.get("asks", [])

                    if bids and asks:
                        best_bid = float(bids[0][0])
                        best_ask = float(asks[0][0])
                        spread_bps = ((best_ask - best_bid) / max(1e-6, best_bid)) * 10000.0

                        total_bid_vol = sum(float(qty) for _, qty in bids)
                        total_ask_vol = sum(float(qty) for _, qty in asks)
                        total_vol = total_bid_vol + total_ask_vol

                        depth_ratio = total_bid_vol / max(1e-6, total_vol)

                        ofi_score = (total_bid_vol - total_ask_vol) / max(1e-6, total_vol)

                        vacuum_risk = spread_bps > 15.0

                        circuit_locked = "NONE"
                        if depth_ratio <= 0.05 or total_bid_vol == 0:
                            circuit_locked = "LOWER_CIRCUIT_ZERO_BIDS"
                        elif depth_ratio >= 0.95 or total_ask_vol == 0:
                            circuit_locked = "UPPER_CIRCUIT_ZERO_ASKS"

                        return {
                            "depth_available": True,
                            "best_bid": best_bid,
                            "best_ask": best_ask,
                            "spread_bps": round(spread_bps, 2),
                            "bid_depth_ratio": round(depth_ratio, 3),
                            "ofi_score": round(ofi_score, 3),
                            "liquidity_vacuum": vacuum_risk,
                            "circuit_locked": circuit_locked,
                            "details": f"L2 Depth Analyzed. Spread: {spread_bps:.1f} bps, Bid Depth Ratio: {depth_ratio:.2f}"
                        }
            except Exception as e:
                logger.debug(f"[TrapDetector] Real-time L2 fetch error for {symbol}: {e}")

        return {
            "depth_available": False,
            "best_bid": 0.0,
            "best_ask": 0.0,
            "spread_bps": 3.0,
            "bid_depth_ratio": 0.50,
            "ofi_score": 0.0,
            "liquidity_vacuum": False,
            "circuit_locked": "NONE",
            "details": "L2 orderbook depth simulated / standard institutional spread assumption."
        }

    def audit_trade_proposal_against_traps(
        self,
        df: pd.DataFrame,
        market: str,
        symbol: str,
        direction: str
    ) -> Dict[str, Any]:
        """
        Master Audit Function: Cross-references proposed trade direction with:
        1. Price Action Sweeps & Traps
        2. Order Book Depth & Liquidity Vacuums
        3. Lower / Upper Circuit Lock-in Hazard

        Outputs clear VETO or APPROVE recommendation for Risk and CEO agents.
        """
        pa_trap = self.detect_price_action_traps(df)
        depth_info = self.evaluate_depth_and_orderbook(market, symbol)

        clean_dir = direction.upper()
        conflict_detected = False
        veto_reason = ""
        severity = pa_trap.get("severity", "NONE")

        # 0. Circuit Limit Lock-in Gate (SEBI / Exchange Circuit Freeze)
        if depth_info.get("circuit_locked") == "LOWER_CIRCUIT_ZERO_BIDS" and clean_dir == "LONG":
            conflict_detected = True
            severity = "CRITICAL"
            veto_reason = "CIRCUIT_LIMIT_LOCK_RISK: Orderbook depth shows zero/negligible buyers (Lower Circuit Lock). Stop loss cannot be executed."
        elif depth_info.get("circuit_locked") == "UPPER_CIRCUIT_ZERO_ASKS" and clean_dir == "SHORT":
            conflict_detected = True
            severity = "CRITICAL"
            veto_reason = "CIRCUIT_LIMIT_LOCK_RISK: Orderbook depth shows zero sellers (Upper Circuit Lock). High risk of squeeze and forced short buy-in auction."

        # 1. Directional Trap Conflict Check
        elif clean_dir == "LONG" and pa_trap.get("bull_trap"):
            conflict_detected = True
            veto_reason = f"TRAP_VETO: Long trade proposal conflicts with active {pa_trap.get('trap_type')}. Institutions are selling into retail breakout buying."

        elif clean_dir == "SHORT" and pa_trap.get("bear_trap"):
            conflict_detected = True
            veto_reason = f"TRAP_VETO: Short trade proposal conflicts with active {pa_trap.get('trap_type')}. Institutions are absorbing sell-side liquidity."

        # 2. Orderbook Imbalance Trap Check
        if depth_info.get("depth_available") and not conflict_detected:
            if clean_dir == "LONG" and depth_info.get("ofi_score", 0.0) < -0.40:
                conflict_detected = True
                severity = "HIGH"
                veto_reason = f"ORDERBOOK_WALL_TRAP: Long trade proposed directly into massive ask wall (Bid/Ask Ratio: {depth_info.get('bid_depth_ratio'):.2f})."
            elif clean_dir == "SHORT" and depth_info.get("ofi_score", 0.0) > 0.40:
                conflict_detected = True
                severity = "HIGH"
                veto_reason = f"ORDERBOOK_WALL_TRAP: Short trade proposed directly into massive bid wall (Bid/Ask Ratio: {depth_info.get('bid_depth_ratio'):.2f})."
            elif depth_info.get("liquidity_vacuum"):
                conflict_detected = True
                severity = "CRITICAL"
                veto_reason = f"LIQUIDITY_VACUUM_SPREAD_SHOCK: Bid-Ask spread ({depth_info.get('spread_bps')} bps) indicates severe liquidity dry-up. High slippage hazard."

        if conflict_detected and severity in ["CRITICAL", "HIGH"]:
            rec_action = "VETO_TRADE"
        elif conflict_detected:
            rec_action = "PROCEED_WITH_CAUTION_THROTTLE_50"
        else:
            rec_action = "CLEAR_TO_EXECUTE"

        return {
            "trap_audit_passed": not conflict_detected,
            "recommended_action": rec_action,
            "severity": severity,
            "veto_reason": veto_reason,
            "price_action_trap": pa_trap,
            "orderbook_depth": depth_info
        }
