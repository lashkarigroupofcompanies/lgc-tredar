"""
Multi-Market Live Candlestick & Tick Data Feed
Connects to 24/7 Crypto exchanges (via CCXT/Public REST) and Indian/US Equities (via yfinance).
Outputs standard OHLCV (Open, High, Low, Close, Volume) DataFrames.
"""

import logging
import time
from typing import Dict, Any, Optional, List
import pandas as pd
import yfinance as yf
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MarketFeed")


class MarketFeedEngine:
    """
    Unified market data engine providing real-time and historical candles
    across Crypto, Indian Stocks (NSE/BSE), and US Stocks.
    """

    def __init__(self):
        self.crypto_base_url = "https://api.binance.com/api/v3"

    def fetch_crypto_candles(self, symbol: str = "BTCUSDT", interval: str = "15m", limit: int = 100) -> pd.DataFrame:
        """
        Fetches 24/7 real-time crypto candles directly from public high-speed REST endpoint (no key required).
        Intervals: 1m, 5m, 15m, 1h, 4h, 1d
        """
        clean_symbol = symbol.replace("/", "").replace("-", "").upper()
        if not clean_symbol.endswith("USDT"):
            clean_symbol = f"{clean_symbol}USDT"

        url = f"{self.crypto_base_url}/klines?symbol={clean_symbol}&interval={interval}&limit={limit}"
        try:
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                raw_data = resp.json()
                df = pd.DataFrame(raw_data, columns=[
                    "open_time", "open", "high", "low", "close", "volume",
                    "close_time", "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"
                ])
                # Format into numeric columns
                df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms")
                for col in ["open", "high", "low", "close", "volume"]:
                    df[col] = df[col].astype(float)
                
                df = df[["timestamp", "open", "high", "low", "close", "volume"]]
                df.set_index("timestamp", inplace=True)
                return df
            else:
                logger.error(f"Crypto fetch failed {resp.status_code}: {resp.text}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Crypto feed exception for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_stock_candles(self, symbol: str, interval: str = "15m", period: str = "5d") -> pd.DataFrame:
        """
        Fetches Indian (e.g. RELIANCE.NS, ^NSEI) or US Stocks (AAPL, NVDA, TSLA) via yfinance.
        Intervals: 1m, 5m, 15m, 1h, 1d
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(interval=interval, period=period)
            if df.empty:
                logger.warning(f"Empty data returned for stock {symbol}")
                return pd.DataFrame()

            # Clean and standardize column names
            df.reset_index(inplace=True)
            col_map = {c: c.lower() for c in df.columns}
            df.rename(columns=col_map, inplace=True)
            
            # Find date/datetime column
            time_col = "datetime" if "datetime" in df.columns else "date"
            if time_col in df.columns:
                df["timestamp"] = pd.to_datetime(df[time_col])
                df.set_index("timestamp", inplace=True)

            required_cols = ["open", "high", "low", "close", "volume"]
            avail_cols = [c for c in required_cols if c in df.columns]
            return df[avail_cols]
        except Exception as e:
            logger.error(f"Stock feed exception for {symbol}: {e}")
            return pd.DataFrame()

    def get_market_data(self, market_type: str, symbol: str, interval: str = "15m") -> pd.DataFrame:
        """
        Universal Global Router for:
        CRYPTO | INDIAN_STOCKS | US_STOCKS | UK_STOCKS | EU_STOCKS | ASIAN_STOCKS | FOREX | COMMODITIES
        """
        m_type = market_type.upper()
        sym = symbol.upper().strip()

        if m_type == "CRYPTO":
            return self.fetch_crypto_candles(sym, interval=interval)
        elif m_type in ["INDIAN_STOCKS", "INDIA"]:
            if not sym.startswith("^") and not sym.endswith(".NS") and not sym.endswith(".BO"):
                sym = f"{sym}.NS"
            return self.fetch_stock_candles(sym, interval=interval)
        elif m_type in ["UK_STOCKS", "UK"]:
            if not sym.endswith(".L"):
                sym = f"{sym}.L"
            return self.fetch_stock_candles(sym, interval=interval)
        elif m_type in ["EU_STOCKS", "EU"]:
            if not any(sym.endswith(sfx) for sfx in [".DE", ".PA", ".AS", ".MI"]):
                sym = f"{sym}.DE"
            return self.fetch_stock_candles(sym, interval=interval)
        elif m_type in ["ASIAN_STOCKS", "ASIA"]:
            # Tokyo (.T), Hong Kong (.HK), Australia (.AX)
            return self.fetch_stock_candles(sym, interval=interval)
        elif m_type in ["FOREX", "FX"]:
            if not sym.endswith("=X"):
                sym = f"{sym}=X"
            return self.fetch_stock_candles(sym, interval=interval)
        elif m_type in ["COMMODITIES", "COMMODITY"]:
            # Standard futures symbols GC=F, CL=F, SI=F
            commodity_map = {"GOLD": "GC=F", "CRUDEOIL": "CL=F", "CRUDE": "CL=F", "SILVER": "SI=F", "NATGAS": "NG=F"}
            sym = commodity_map.get(sym, sym if sym.endswith("=F") else f"{sym}=F")
            return self.fetch_stock_candles(sym, interval=interval)
        else:  # US_STOCKS default
            return self.fetch_stock_candles(sym, interval=interval)


if __name__ == "__main__":
    feed = MarketFeedEngine()
    print("Testing Market Feed on Crypto BTC 15m...")
    btc_df = feed.fetch_crypto_candles("BTC", interval="15m", limit=5)
    print("Crypto BTC Data:")
    print(btc_df.tail(3))

    print("\nTesting Market Feed on Indian Stock Reliance...")
    rel_df = feed.get_market_data("INDIAN_STOCKS", "RELIANCE", interval="1d")
    print("Reliance Data:")
    print(rel_df.tail(3))
