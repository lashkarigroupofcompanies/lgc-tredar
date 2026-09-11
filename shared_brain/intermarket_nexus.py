"""
Inter-Market Intelligence Nexus (Cross-Asset Macro Lead-Lag Engine)
Inspired by institutional multi-asset desks, Requiem-Intermarket-Nexus,
and Riskfolio-Lib cross-asset covariance matrices.

Tracks:
1. DXY (US Dollar Index / UUP) - Global liquidity drain & USD strength
2. US10Y (^TNX) - US 10-Year Treasury yield & risk-free discount rate
3. VIX (^VIX) - CBOE Equity Volatility / Market Fear Gauge
4. BTCUSDT - High-beta risk asset sentiment lead indicator

Enables continuous cross-market conversation:
- "If DXY or US10Y surges, Crypto & Indian Equity Long setups face heavy headwinds."
- "If VIX spikes > 24, liquidity vanishes and slippage jumps."
"""

import logging
import time
from typing import Dict, Any, Optional
import yfinance as yf
import requests

logger = logging.getLogger("IntermarketNexus")


class IntermarketNexus:
    """
    Central Cross-Market Intelligence Hub.
    Maintains synchronized macro telemetry so Crypto, Indian Stocks,
    and US Equity squads share unified macro situational awareness.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(IntermarketNexus, cls).__new__(cls)
            cls._instance._init_nexus()
        return cls._instance

    def _init_nexus(self):
        self.last_refresh_time: float = 0.0
        self.cache_duration_sec: float = 300.0  # 5-minute cache to avoid yfinance rate limits
        self.cached_telemetry: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "macro_regime": "MACRO_NEUTRAL_TRANSITION",
            "dxy_change_pct": 0.0,
            "dxy_level": 104.5,
            "us10y_yield": 4.25,
            "us10y_change_pct": 0.0,
            "vix_level": 16.5,
            "vix_change_pct": 0.0,
            "btc_change_pct": 0.0,
            "btc_price": 65000.0,
            "cross_market_warnings": []
        }
        logger.info("[IntermarketNexus] 🌐 Inter-Market Cross-Asset Intelligence Hub initialized.")

    def refresh_macro_telemetry(self, force: bool = False) -> Dict[str, Any]:
        """
        Fetches updated macro metrics across DXY, US10Y, VIX, and BTC.
        Uses cached data if called within cache_duration_sec.
        """
        now = time.time()
        if not force and (now - self.last_refresh_time) < self.cache_duration_sec and self.last_refresh_time > 0:
            return self.cached_telemetry

        dxy_chg = 0.0
        dxy_val = 104.5
        us10y_chg = 0.0
        us10y_val = 4.25
        vix_chg = 0.0
        vix_val = 16.5
        btc_chg = 0.0
        btc_val = 65000.0

        # 1. Fetch DXY (or UUP ETF fallback)
        try:
            dxy_ticker = yf.Ticker("DX-Y.NYB")
            hist = dxy_ticker.history(period="5d", interval="1d")
            if not hist.empty and len(hist) >= 2:
                dxy_val = float(hist["Close"].iloc[-1])
                dxy_chg = ((dxy_val - float(hist["Close"].iloc[-2])) / float(hist["Close"].iloc[-2])) * 100.0
        except Exception as e:
            logger.debug(f"[IntermarketNexus] DXY fetch error: {e}")

        # 2. Fetch US 10-Year Yield (^TNX)
        try:
            tnx_ticker = yf.Ticker("^TNX")
            hist = tnx_ticker.history(period="5d", interval="1d")
            if not hist.empty and len(hist) >= 2:
                us10y_val = float(hist["Close"].iloc[-1])
                us10y_chg = ((us10y_val - float(hist["Close"].iloc[-2])) / float(hist["Close"].iloc[-2])) * 100.0
        except Exception as e:
            logger.debug(f"[IntermarketNexus] ^TNX fetch error: {e}")

        # 3. Fetch VIX (^VIX)
        try:
            vix_ticker = yf.Ticker("^VIX")
            hist = vix_ticker.history(period="5d", interval="1d")
            if not hist.empty and len(hist) >= 2:
                vix_val = float(hist["Close"].iloc[-1])
                vix_chg = ((vix_val - float(hist["Close"].iloc[-2])) / float(hist["Close"].iloc[-2])) * 100.0
        except Exception as e:
            logger.debug(f"[IntermarketNexus] ^VIX fetch error: {e}")

        # 4. Fetch BTC 24h ticker via Binance public REST
        try:
            resp = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT", timeout=3.5)
            if resp.status_code == 200:
                data = resp.json()
                btc_val = float(data.get("lastPrice", 65000.0))
                btc_chg = float(data.get("priceChangePercent", 0.0))
        except Exception as e:
            logger.debug(f"[IntermarketNexus] BTC ticker fetch error: {e}")

        # 5. Synthesize Macro Lead-Lag Regime
        warnings = []
        regime = "MACRO_NEUTRAL_TRANSITION"

        # Check Dollar Surge / Yield Spike
        if dxy_chg >= 0.50 or us10y_chg >= 2.5:
            regime = "MACRO_RISK_OFF_DOLLAR_SURGE"
            warnings.append("USD / US10Y Surging: Liquidity drain on Crypto and Emerging Equities.")

        # Check Volatility Storm
        if vix_val >= 24.0 or vix_chg >= 12.0:
            regime = "MACRO_VOLATILITY_STORM"
            warnings.append(f"VIX Spike ({vix_val:.1f}): Market-wide panic and liquidity vacuum risk.")

        # Check Bullish Risk-On
        elif dxy_chg <= -0.25 and vix_val < 18.0 and btc_chg >= 0.5:
            regime = "MACRO_RISK_ON"

        self.last_refresh_time = now
        self.cached_telemetry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "macro_regime": regime,
            "dxy_level": round(dxy_val, 2),
            "dxy_change_pct": round(dxy_chg, 2),
            "us10y_yield": round(us10y_val, 2),
            "us10y_change_pct": round(us10y_chg, 2),
            "vix_level": round(vix_val, 2),
            "vix_change_pct": round(vix_chg, 2),
            "btc_price": round(btc_val, 2),
            "btc_change_pct": round(btc_chg, 2),
            "cross_market_warnings": warnings
        }

        logger.info(f"[IntermarketNexus] 📡 Macro Nexus Updated: {regime} | DXY: {dxy_chg:+.2f}% | VIX: {vix_val:.1f} | BTC: {btc_chg:+.2f}%")
        return self.cached_telemetry

    def get_cross_market_implications(self, market: str, direction: str) -> Dict[str, Any]:
        """
        Determines whether a proposed trade in a specific market aligns with
        or conflicts with global inter-market flows.
        """
        telemetry = self.refresh_macro_telemetry(force=False)
        regime = telemetry.get("macro_regime", "MACRO_NEUTRAL_TRANSITION")
        m = market.upper()
        d = direction.upper()

        status = "ALIGNED"
        throttle_multiplier = 1.0
        reason = "Inter-market macro flows are neutral or favorable."

        # Rule 1: Dollar Surge vs Long Crypto/Equities
        if regime == "MACRO_RISK_OFF_DOLLAR_SURGE":
            if d == "LONG" and m in ["CRYPTO", "INDIAN_STOCKS", "US_STOCKS", "EU_STOCKS", "ASIAN_STOCKS"]:
                status = "MACRO_HEADWIND"
                throttle_multiplier = 0.50
                reason = f"DXY / Yield surge ({telemetry['dxy_change_pct']:+.2f}%) creates systematic drag against {m} LONGs."
            elif d == "SHORT" and m in ["CRYPTO", "INDIAN_STOCKS", "US_STOCKS"]:
                status = "MACRO_TAILWIND"
                reason = "DXY surge provides macro tailwind for shorting risk assets."

        # Rule 2: VIX Volatility Panic
        elif regime == "MACRO_VOLATILITY_STORM":
            if d == "LONG":
                status = "VOLATILITY_ALERT"
                throttle_multiplier = 0.50
                reason = f"High VIX ({telemetry['vix_level']:.1f}) elevates gap risk and false breakout rate."

        # Rule 3: Risk-On Green Light
        elif regime == "MACRO_RISK_ON":
            if d == "LONG":
                status = "MACRO_TAILWIND"
                reason = "Favorable risk-on environment (Falling USD, sub-18 VIX)."

        return {
            "regime": regime,
            "market": m,
            "direction": d,
            "alignment": status,
            "throttle_multiplier": throttle_multiplier,
            "reason": reason,
            "telemetry": telemetry
        }
