"""
MiroFish Financial Intelligence & Sentiment Analysis Engine
Incorporates entity extraction, cashtags detection ($BTC, $NVDA, $RELIANCE),
sentiment scoring (-1.0 to +1.0), and market impact classification.
"""

import re
from typing import List, Dict, Any, Optional

# Cashtag Regex: e.g. $BTC, $ETH, $NVDA, $AAPL, $TSLA, $RELIANCE
CASHTAG_RE = re.compile(r"(?<![A-Za-z0-9$])\$([A-Z]{1,8})(?![A-Za-z0-9])")

# Common Company / Asset Keyword Mapping to Standard Tickers
ASSET_KEYWORD_MAP = {
    "bitcoin": "BTC",
    "btc": "BTC",
    "ethereum": "ETH",
    "ether": "ETH",
    "solana": "SOL",
    "sol": "SOL",
    "nvidia": "NVDA",
    "apple": "AAPL",
    "tesla": "TSLA",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "reliance": "RELIANCE",
    "tcs": "TCS",
    "nifty": "NIFTY50",
    "banknifty": "BANKNIFTY",
    "crude oil": "CRUDE",
    "brent": "CRUDE",
    "wti": "CRUDE",
    "gold": "GOLD",
    "silver": "SILVER",
    "dxy": "DXY",
    "dollar": "DXY",
    "fed": "FED_MACRO",
    "rbi": "RBI_MACRO",
}

# High-impact Bullish & Bearish vocabulary for financial context
BULLISH_KEYWORDS = {
    "surge": 0.6, "rally": 0.5, "jump": 0.4, "breakout": 0.7, "soar": 0.6,
    "bullish": 0.8, "record high": 0.7, "all-time high": 0.8, "ath": 0.7,
    "outperform": 0.5, "upgrade": 0.6, "rate cut": 0.7, "stimulus": 0.6,
    "profit surge": 0.7, "revenue beat": 0.6, "accumulate": 0.5, "buy": 0.4,
    "inflow": 0.5, "approved": 0.7, "partnership": 0.4, "gains": 0.4,
}

BEARISH_KEYWORDS = {
    "plunge": -0.6, "crash": -0.8, "dump": -0.6, "tumble": -0.5, "drop": -0.4,
    "bearish": -0.8, "record low": -0.7, "sell-off": -0.6, "liquidation": -0.7,
    "downgrade": -0.6, "rate hike": -0.6, "inflation spike": -0.6, "recession": -0.8,
    "revenue miss": -0.6, "loss": -0.5, "ban": -0.7, "investigation": -0.5,
    "hack": -0.8, "outflow": -0.5, "war": -0.7, "sanctions": -0.6, "warning": -0.5,
}

CRITICAL_TRIGGERS = [
    "rate cut", "rate hike", "interest rate decision", "fomc", "rbi rate",
    "war", "invaded", "military strike", "emergency meeting", "bank run",
    "crypto ban", "etf approved", "sec lawsuit", "all-time high", "market crash"
]


class MiroFishIntelligence:
    """
    Processes unstructured headlines into structured market signals.
    """

    @staticmethod
    def extract_tickers(text: str) -> List[str]:
        """
        Extract both explicit $TICKERS and mapped asset names.
        """
        found_tickers = []

        # 1. Explicit Cashtags: $BTC, $NVDA
        for match in CASHTAG_RE.findall(text):
            found_tickers.append(match.upper())

        # 2. Asset Names matching
        lower_text = text.lower()
        for keyword, ticker in ASSET_KEYWORD_MAP.items():
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, lower_text):
                if ticker not in found_tickers:
                    found_tickers.append(ticker)

        return found_tickers[:5]

    @staticmethod
    def score_sentiment(text: str) -> float:
        """
        Calculates sentiment polarity from -1.0 (Strongly Bearish) to +1.0 (Strongly Bullish).
        """
        lower_text = text.lower()
        score = 0.0
        hits = 0

        for word, weight in BULLISH_KEYWORDS.items():
            if word in lower_text:
                score += weight
                hits += 1

        for word, weight in BEARISH_KEYWORDS.items():
            if word in lower_text:
                score += weight
                hits += 1

        if hits == 0:
            return 0.0

        # Bound score between -1.0 and +1.0
        normalized = max(min(score / max(hits, 1), 1.0), -1.0)
        return round(normalized, 2)

    @staticmethod
    def classify_severity(text: str) -> str:
        """
        Returns severity tier: CRITICAL, HIGH, MEDIUM, LOW
        """
        lower = text.lower()
        for trigger in CRITICAL_TRIGGERS:
            if trigger in lower:
                return "CRITICAL"

        score = abs(MiroFishIntelligence.score_sentiment(text))
        if score >= 0.6:
            return "HIGH"
        elif score >= 0.3:
            return "MEDIUM"
        return "LOW"

    @classmethod
    def analyze_news_item(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriches a raw feed item with MiroFish intelligence tags.
        """
        full_text = f"{item.get('title', '')} {item.get('summary', '')}"
        tickers = cls.extract_tickers(full_text)
        sentiment = cls.score_sentiment(full_text)
        severity = cls.classify_severity(full_text)

        # Categorize actionability
        if sentiment >= 0.4:
            bias = "BULLISH"
        elif sentiment <= -0.4:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"

        return {
            **item,
            "tickers": tickers,
            "sentiment_score": sentiment,
            "bias": bias,
            "severity": severity,
            "is_actionable": len(tickers) > 0 and abs(sentiment) >= 0.3
        }

    @classmethod
    def process_batch(cls, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch process and rank by severity and actionability.
        """
        enriched = [cls.analyze_news_item(item) for item in items]
        # Sort so that CRITICAL & actionable items come first
        severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        enriched.sort(key=lambda x: (severity_rank.get(x["severity"], 3), -abs(x["sentiment_score"])))
        return enriched


if __name__ == "__main__":
    sample_news = [
        {"title": "Bitcoin surges past $95,000 as Fed hints at upcoming rate cuts", "summary": "$BTC breaks all resistance."},
        {"title": "Crude oil plunges 4% amid unexpected OPEC supply increase", "summary": "Brent drops sharply."},
        {"title": "Nifty reaches all-time high led by Reliance and TCS profit surge", "summary": "Indian markets rally."}
    ]
    results = MiroFishIntelligence.process_batch(sample_news)
    for r in results:
        print(f"[{r['severity']}] {r['bias']} (Score: {r['sentiment_score']}) | Tickers: {r['tickers']} | {r['title']}")
