"""
Session Timing Controller - Global Multi-Market Timezone & Session Engine
Section 5: Execution Timing & Session Management

Provides institutional session rules & precision timezone conversions across ALL world share markets:
1. US_STOCKS: NYSE / NASDAQ (Timezone: America/New_York)
2. INDIAN_STOCKS: NSE / BSE (Timezone: Asia/Kolkata)
3. UK_STOCKS: LSE London (Timezone: Europe/London)
4. EU_STOCKS: Frankfurt DAX / Euronext Paris (Timezone: Europe/Berlin)
5. ASIAN_STOCKS: Tokyo JPX (Asia/Tokyo) / Hong Kong HKEX (Asia/Hong_Kong) / Sydney ASX (Australia/Sydney)
6. FOREX: Global 24/5 Currencies (UTC)
7. COMMODITIES: Gold, Crude Oil, Silver - COMEX/NYMEX & MCX
8. CRYPTO: 24/7/365 Global Liquid Markets (UTC)

Features:
- Real timezone localization via Python zoneinfo.
- Opening volatility protection (avoids initial whipsaws and opening manipulation traps).
- Mid-day lull protection (scales down size in low-liquidity lunch chop).
- Institutional Power Hour tracking.
- Compulsory intraday square-off triggers.
- News blackout clearance.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import datetime
import zoneinfo
from typing import Dict, Any, Optional
import logging

from agents.evolution_memory.market_memory_matrix import MarketMemoryMatrix

logger = logging.getLogger("SessionTimingController")


class SessionTimingController:
    """
    Global Multi-Market Timezone & Session Gatekeeper.
    Converts universal timestamps to exchange-local time and validates session eligibility.
    """

    TIMEZONE_MAP = {
        "US_STOCKS": "America/New_York",
        "INDIAN_STOCKS": "Asia/Kolkata",
        "UK_STOCKS": "Europe/London",
        "EU_STOCKS": "Europe/Berlin",
        "ASIAN_STOCKS": "Asia/Tokyo",
        "FOREX": "UTC",
        "COMMODITIES": "America/New_York",
        "CRYPTO": "UTC"
    }

    @classmethod
    def get_exchange_local_time(
        cls,
        market: str,
        custom_dt: Optional[datetime.datetime] = None
    ) -> datetime.datetime:
        """
        Converts input datetime (or current system time) into the exact exchange-local time.
        """
        norm_market = MarketMemoryMatrix.normalize_market_key(market)
        tz_name = cls.TIMEZONE_MAP.get(norm_market, "UTC")
        try:
            target_tz = zoneinfo.ZoneInfo(tz_name)
        except Exception:
            target_tz = zoneinfo.ZoneInfo("UTC")

        if custom_dt is None:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            return now_utc.astimezone(target_tz)

        # If custom_dt has no timezone, assume system local time and convert
        if custom_dt.tzinfo is None:
            return custom_dt.replace(tzinfo=target_tz)
        else:
            return custom_dt.astimezone(target_tz)

    @classmethod
    def evaluate_session_timing(
        cls,
        market: str,
        simulated_time_ist: Optional[datetime.datetime] = None,
        is_news_pending: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates session conditions for the specified world share market.
        Returns execution clearance, session name, quality modifier, and intraday square-off status.
        """
        norm_market = MarketMemoryMatrix.normalize_market_key(market)
        local_time = cls.get_exchange_local_time(norm_market, simulated_time_ist)
        weekday = local_time.weekday()  # 0=Monday ... 5=Saturday, 6=Sunday

        # News Blackout Check (Section 5)
        if is_news_pending:
            return {
                "can_execute": False,
                "session_name": "NEWS_BLACKOUT",
                "market": norm_market,
                "local_time": local_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "reason": "High-impact macro news release pending in next 30 min. Capital preservation lock.",
                "quality_modifier": 0.0,
                "is_killzone": False,
                "is_expiry_day": False,
                "intraday_square_off_required": False
            }

        # Weekend Check for Non-Crypto
        if norm_market != "CRYPTO" and norm_market != "FOREX":
            if weekday >= 5:
                return {
                    "can_execute": False,
                    "session_name": "WEEKEND_CLOSED",
                    "market": norm_market,
                    "local_time": local_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "reason": f"{norm_market} exchange is closed for the weekend.",
                    "quality_modifier": 0.0,
                    "is_killzone": False,
                    "is_expiry_day": False,
                    "intraday_square_off_required": True
                }

        # Route to market-specific session evaluator
        if norm_market == "INDIAN_STOCKS":
            return cls._eval_indian_session(local_time)
        elif norm_market == "US_STOCKS":
            return cls._eval_us_session(local_time)
        elif norm_market == "UK_STOCKS":
            return cls._eval_uk_session(local_time)
        elif norm_market == "EU_STOCKS":
            return cls._eval_eu_session(local_time)
        elif norm_market == "ASIAN_STOCKS":
            return cls._eval_asian_session(local_time)
        elif norm_market == "FOREX":
            return cls._eval_forex_session(local_time)
        elif norm_market == "COMMODITIES":
            return cls._eval_commodity_session(local_time)
        else:  # CRYPTO
            return cls._eval_crypto_session(local_time)

    # ------------------ 1. INDIAN EQUITIES (NSE/BSE - IST) ------------------
    @classmethod
    def _eval_indian_session(cls, t: datetime.datetime) -> Dict[str, Any]:
        hour, minute = t.hour, t.minute
        time_dec = hour + minute / 60.0
        is_expiry = (t.weekday() == 3)  # Thursday weekly expiry
        time_str = t.strftime("%H:%M:%S IST")

        if 9.0 <= time_dec < 9.25:
            return cls._pkg(False, "PRE_OPEN", "Pre-open order matching. No live execution.", 0.0, False, is_expiry, False, time_str)
        if 9.25 <= time_dec < 9.75:
            return cls._pkg(False, "OPENING_RANGE_FORMATION", "Opening 30-min range formation (9:15-9:45 AM IST). Avoid whipsaws and establish range.", 0.3, False, is_expiry, False, time_str)
        if 9.75 <= time_dec < 11.5:
            return cls._pkg(True, "PRIME_MORNING", "NSE/BSE Prime morning momentum session (ORB Breakout Window).", 1.2, True, is_expiry, False, time_str)
        if 11.5 <= time_dec < 13.0:
            return cls._pkg(True, "MIDDAY_LULL", "Mid-day lull trap. Trade smaller or wait.", 0.7, False, is_expiry, False, time_str)
        if 13.0 <= time_dec < 14.5:
            return cls._pkg(True, "AFTERNOON_SESSION", "London open overlap momentum.", 1.0, True, is_expiry, False, time_str)
        if 14.5 <= time_dec < 15.5:
            intraday_close = time_dec >= 15.0
            return cls._pkg(not intraday_close, "POWER_HOUR", "Intraday square-off window (3:00 PM)" if intraday_close else "Power hour volume expansion.", 0.5 if intraday_close else 1.1, True, is_expiry, intraday_close, time_str)

        return cls._pkg(False, "MARKET_CLOSED", "Indian markets closed.", 0.0, False, is_expiry, True, time_str)

    # ------------------ 2. US EQUITIES (NYSE/NASDAQ - EST) ------------------
    @classmethod
    def _eval_us_session(cls, t: datetime.datetime) -> Dict[str, Any]:
        time_dec = t.hour + t.minute / 60.0
        is_expiry = (t.weekday() == 4)  # Friday weekly options expiry
        time_str = t.strftime("%H:%M:%S EST")

        if 9.5 <= time_dec < 9.75:
            return cls._pkg(False, "OPENING_VOLATILITY", "Opening 15-min whipsaw avoidance.", 0.4, False, is_expiry, False, time_str)
        if 9.75 <= time_dec < 11.5:
            return cls._pkg(True, "PRIME_MORNING", "US Morning Prime Momentum Window (ORB & FVG).", 1.3, True, is_expiry, False, time_str)
        if 11.5 <= time_dec < 13.5:
            return cls._pkg(True, "LUNCH_CHOP", "Wall Street lunch hour chop zone.", 0.7, False, is_expiry, False, time_str)
        if 13.5 <= time_dec < 15.0:
            return cls._pkg(True, "AFTERNOON_TREND", "Institutional re-accumulation session.", 1.0, True, is_expiry, False, time_str)
        if 15.0 <= time_dec < 16.0:
            intraday_close = time_dec >= 15.75
            return cls._pkg(not intraday_close, "US_POWER_HOUR", "Power hour closing imbalance flow." if not intraday_close else "Day trade square-off.", 1.2 if not intraday_close else 0.4, True, is_expiry, intraday_close, time_str)

        return cls._pkg(False, "MARKET_CLOSED", "US regular trading session closed.", 0.0, False, is_expiry, True, time_str)

    # ------------------ 3. UK EQUITIES (LSE London - GMT/BST) ------------------
    @classmethod
    def _eval_uk_session(cls, t: datetime.datetime) -> Dict[str, Any]:
        time_dec = t.hour + t.minute / 60.0
        time_str = t.strftime("%H:%M:%S London")

        if 8.0 <= time_dec < 8.5:
            return cls._pkg(False, "OPENING_VOLATILITY", "London open auction volatility shakeout.", 0.4, False, False, False, time_str)
        if 8.5 <= time_dec < 11.5:
            return cls._pkg(True, "PRIME_MORNING", "LSE Prime morning trend window.", 1.2, True, False, False, time_str)
        if 11.5 <= time_dec < 13.0:
            return cls._pkg(True, "MIDDAY_LULL", "Mid-day lull.", 0.7, False, False, False, time_str)
        if 13.0 <= time_dec < 15.5:
            return cls._pkg(True, "US_OVERLAP_PRIME", "Heaviest European volume: US Open overlap.", 1.3, True, False, False, time_str)
        if 15.5 <= time_dec < 16.5:
            intraday_close = time_dec >= 16.25
            return cls._pkg(not intraday_close, "EUROPEAN_POWER_HOUR", "LSE closing fix auction flow.", 1.0, True, False, intraday_close, time_str)

        return cls._pkg(False, "MARKET_CLOSED", "London Stock Exchange closed.", 0.0, False, False, True, time_str)

    # ------------------ 4. EUROPEAN EQUITIES (Frankfurt/Paris - CET) ------------------
    @classmethod
    def _eval_eu_session(cls, t: datetime.datetime) -> Dict[str, Any]:
        time_dec = t.hour + t.minute / 60.0
        time_str = t.strftime("%H:%M:%S CET")

        if 9.0 <= time_dec < 9.5:
            return cls._pkg(False, "OPENING_VOLATILITY", "DAX/CAC Opening whipsaw.", 0.4, False, False, False, time_str)
        if 9.5 <= time_dec < 12.0:
            return cls._pkg(True, "PRIME_MORNING", "European morning trend continuation.", 1.2, True, False, False, time_str)
        if 12.0 <= time_dec < 14.0:
            return cls._pkg(True, "MIDDAY_LULL", "European lunch lull.", 0.7, False, False, False, time_str)
        if 14.0 <= time_dec < 16.5:
            return cls._pkg(True, "US_OVERLAP_PRIME", "Transatlantic peak liquidity.", 1.3, True, False, False, time_str)
        if 16.5 <= time_dec < 17.5:
            intraday_close = time_dec >= 17.25
            return cls._pkg(not intraday_close, "EU_POWER_HOUR", "European closing auctions.", 1.0, True, False, intraday_close, time_str)

        return cls._pkg(False, "MARKET_CLOSED", "European exchanges closed.", 0.0, False, False, True, time_str)

    # ------------------ 5. ASIAN EQUITIES (Tokyo JPX / HKEX - JST/HKT) ------------------
    @classmethod
    def _eval_asian_session(cls, t: datetime.datetime) -> Dict[str, Any]:
        time_dec = t.hour + t.minute / 60.0
        time_str = t.strftime("%H:%M:%S JST")

        if 9.0 <= time_dec < 9.25:
            return cls._pkg(False, "OPENING_VOLATILITY", "Tokyo/Asian open volatility.", 0.4, False, False, False, time_str)
        if 9.25 <= time_dec < 11.5:
            return cls._pkg(True, "TOKYO_PRIME_MORNING", "Asian morning auction & momentum window.", 1.2, True, False, False, time_str)
        if 11.5 <= time_dec < 12.5:
            return cls._pkg(False, "TOKYO_LUNCH_BREAK", "Exchange lunch break pause.", 0.0, False, False, False, time_str)
        if 12.5 <= time_dec < 14.0:
            return cls._pkg(True, "AFTERNOON_AUCTION", "Asian afternoon trend.", 0.9, True, False, False, time_str)
        if 14.0 <= time_dec < 15.0:
            intraday_close = time_dec >= 14.75
            return cls._pkg(not intraday_close, "TOKYO_POWER_HOUR", "Tokyo closing auction.", 1.0, True, False, intraday_close, time_str)

        return cls._pkg(False, "MARKET_CLOSED", "Asian regular session closed.", 0.0, False, False, True, time_str)

    # ------------------ 6. FOREX (24/5 Global Currencies - UTC) ------------------
    @classmethod
    def _eval_forex_session(cls, t: datetime.datetime) -> Dict[str, Any]:
        weekday = t.weekday()
        hour = t.hour
        time_str = t.strftime("%H:%M:%S UTC")

        # Weekend close: Friday 22:00 UTC to Sunday 22:00 UTC
        if (weekday == 4 and hour >= 22) or weekday == 5 or (weekday == 6 and hour < 22):
            return cls._pkg(False, "WEEKEND_CLOSED", "Global FX interbank market closed for weekend.", 0.0, False, False, True, time_str)

        if 12 <= hour < 16:
            return cls._pkg(True, "LONDON_NY_OVERLAP", "Peak World Liquidity: London/New York overlap session.", 1.4, True, False, False, time_str)
        elif 7 <= hour < 12:
            return cls._pkg(True, "LONDON_ACTIVE", "London European currency prime session.", 1.2, True, False, False, time_str)
        elif 16 <= hour < 21:
            return cls._pkg(True, "NY_AFTERNOON", "New York afternoon currency flows.", 1.0, True, False, False, time_str)
        elif 0 <= hour < 7:
            return cls._pkg(True, "ASIAN_SESSION", "Tokyo/Sydney Asian currency session.", 0.9, True, False, False, time_str)
        else:
            return cls._pkg(True, "FX_ROLLOVER", "Interbank rollover session (wide spreads). Trade smaller.", 0.6, False, False, False, time_str)

    # ------------------ 7. COMMODITIES (Gold/Crude - EST) ------------------
    @classmethod
    def _eval_commodity_session(cls, t: datetime.datetime) -> Dict[str, Any]:
        time_dec = t.hour + t.minute / 60.0
        time_str = t.strftime("%H:%M:%S EST")

        if 8.0 <= time_dec < 13.5:
            return cls._pkg(True, "COMEX_PRIME_DAY", "High-volume metals & energy pit trading session.", 1.3, True, False, False, time_str)
        elif 13.5 <= time_dec < 17.0:
            return cls._pkg(True, "COMEX_AFTERNOON", "Commodity settlement session.", 1.0, True, False, False, time_str)
        elif 18.0 <= time_dec or time_dec < 8.0:
            return cls._pkg(True, "COMMODITY_ELECTRONIC_GLOBEX", "Overnight Globex electronic futures trading.", 0.8, False, False, False, time_str)
        else:
            return cls._pkg(False, "COMMODITY_MAINTENANCE_PAUSE", "Daily exchange maintenance break (17:00-18:00 EST).", 0.0, False, False, False, time_str)

    # ------------------ 8. CRYPTO (24/7 Global - UTC) ------------------
    @classmethod
    def _eval_crypto_session(cls, t: datetime.datetime) -> Dict[str, Any]:
        hour = t.hour
        time_str = t.strftime("%H:%M:%S UTC")

        if 7 <= hour < 10:
            return cls._pkg(True, "LONDON_OPEN_KILLZONE", "High-volume London Open session. Premium liquidity.", 1.2, True, False, False, time_str)
        elif 12 <= hour < 15:
            return cls._pkg(True, "NY_OPEN_KILLZONE", "NY Open institutional influx. Highest daily crypto volume.", 1.3, True, False, False, time_str)
        elif 0 <= hour < 3:
            return cls._pkg(True, "ASIAN_KILLZONE", "Asian session range expansion.", 0.9, True, False, False, time_str)
        else:
            return cls._pkg(True, "STANDARD_24_7_CONTINUOUS", "Continuous crypto session. Standard liquidity.", 1.0, False, False, False, time_str)

    @classmethod
    def _pkg(
        cls,
        can_exec: bool,
        session: str,
        reason: str,
        mod: float,
        killzone: bool,
        expiry: bool,
        sqoff: bool,
        time_str: str
    ) -> Dict[str, Any]:
        return {
            "can_execute": can_exec,
            "session_name": session,
            "reason": reason,
            "quality_modifier": mod,
            "is_killzone": killzone,
            "is_expiry_day": expiry,
            "intraday_square_off_required": sqoff,
            "exchange_time": time_str
        }
