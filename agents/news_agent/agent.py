"""
News & Financial Intelligence Agent
Powered by WorldMonitor Feeds + MiroFish Sentiment + Financial Knowledge Graph + NVIDIA NIM LLM Brain.
"""

import sys
import os
import logging
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.news_agent.world_monitor_feed import WorldMonitorFeedEngine
from agents.news_agent.miro_fish_intel import MiroFishIntelligence
from agents.news_agent.knowledge_graph import FinancialKnowledgeGraph
from agents.news_agent.browser_eyes import BrowserEyesEngine
from agents.news_agent.historical_news_precedent import HistoricalNewsPrecedentEngine
from shared_brain.llm_brain import LLMBrain

from shared_brain.omni_calculator import OmniCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NewsAgent")


class NewsIntelligenceAgent:
    """
    Scans WorldMonitor global feeds, analyzes them through MiroFish sentiment engine,
    cross-references against the Financial Knowledge Graph, and reasons deeply using NVIDIA LLM.
    """

    def __init__(self):
        self.calc = OmniCalculator(owner="NewsIntelligenceAgent")
        self.feed_engine = WorldMonitorFeedEngine()
        self.mirofish = MiroFishIntelligence()
        self.knowledge_graph = FinancialKnowledgeGraph()
        self.browser_eyes = BrowserEyesEngine()
        self.llm_brain = LLMBrain()
        self.latest_intelligence: List[Dict[str, Any]] = []
        self.latest_synthesis: Dict[str, Any] = {}

    def scan_market_news(self, market_type: str = "ALL", limit: int = 15) -> List[Dict[str, Any]]:
        """
        Scans feeds based on selected market (CRYPTO, INDIAN_STOCKS, US_STOCKS, or ALL).
        """
        cat_map = {
            "CRYPTO": ["crypto", "macro_centralbanks"],
            "INDIAN_STOCKS": ["india_markets", "macro_centralbanks", "commodities"],
            "US_STOCKS": ["markets", "macro_centralbanks", "commodities"],
            "ALL": ["markets", "crypto", "macro_centralbanks", "commodities", "india_markets"]
        }

        categories = cat_map.get(market_type.upper(), cat_map["ALL"])
        raw_news = self.feed_engine.fetch_all(categories=categories, max_total_items=limit * 2)

        # 1. MiroFish Entity Extraction & Sentiment
        processed_news = self.mirofish.process_batch(raw_news)[:limit]

        # 2. Financial Knowledge Graph Causality Matching
        enriched_news = [self.knowledge_graph.evaluate_news_intelligence(item) for item in processed_news]
        self.latest_intelligence = enriched_news
        return enriched_news

    def generate_llm_intelligence_report(self, market_type: str = "ALL") -> Dict[str, Any]:
        """
        Runs the 3-Layer intelligence pipeline: Feeds -> Knowledge Graph -> LLM Synthesis.
        """
        if not self.latest_intelligence:
            self.scan_market_news(market_type, limit=12)

        # 3. NVIDIA LLM Brain Reasoning
        synthesis = self.llm_brain.analyze_news_signals(self.latest_intelligence)
        self.latest_synthesis = synthesis

        critical_count = sum(1 for item in self.latest_intelligence if item.get("severity") == "CRITICAL")
        high_count = sum(1 for item in self.latest_intelligence if item.get("severity") == "HIGH")

        # 4. Empirical Historical News Precedent Matching
        headlines = [item.get("title", "") for item in self.latest_intelligence]
        precedent_analysis = HistoricalNewsPrecedentEngine.match_news_to_historical_precedents(headlines, market_type=market_type)

        return {
            "agent_name": "News & Intelligence Agent",
            "market_focus": market_type,
            "status": "ONLINE",
            "total_stories_analyzed": len(self.latest_intelligence),
            "critical_events": critical_count,
            "high_severity_events": high_count,
            "llm_thought": synthesis.get("thought_process", ""),
            "macro_bias": synthesis.get("macro_bias", "NEUTRAL"),
            "risk_stance": synthesis.get("risk_stance", "NORMAL"),
            "historical_precedent": precedent_analysis,
            "recommended_targets": synthesis.get("high_probability_targets", []),
            "actionable_trades": synthesis.get("trade_recommendations", []),
            "top_stories": self.latest_intelligence[:6]
        }

    def investigate_ticker_with_browser(self, ticker: str) -> Dict[str, Any]:
        """
        Uses Browser Eyes to search and read breaking internet updates for a specific ticker.
        """
        query = f"{ticker} financial stock crypto news analysis"
        hits = self.browser_eyes.search_duckduckgo(query, max_results=3)
        combined_text = " ".join([f"{h['title']} - {h['snippet']}" for h in hits])
        sentiment = self.mirofish.score_sentiment(combined_text)

        return {
            "ticker": ticker,
            "sentiment_score": sentiment,
            "bias": "BULLISH" if sentiment > 0.2 else ("BEARISH" if sentiment < -0.2 else "NEUTRAL"),
            "source_count": len(hits),
            "headlines": [h["title"] for h in hits]
        }


if __name__ == "__main__":
    agent = NewsIntelligenceAgent()
    print("Testing Complete News Intelligence Agent with LLM Brain...")
    report = agent.generate_llm_intelligence_report("ALL")
    print(f"Status: {report['status']} | Macro Bias: {report['macro_bias']}")
    print(f"Agent Thought: {report['llm_thought']}")
    print(f"Targets: {report['recommended_targets']}")
    print("Actionable Trades:", report['actionable_trades'])
