"""
Financial Knowledge Graph & Event-Driven Impact Engine
Fuses FinGPT taxonomy, QuantConnect Macro Rules, and Institutional Event Matrix.
Provides deterministic causality mapping between live breaking events and market assets.
"""

import json
import re
import os
from typing import Dict, Any, List, Optional

RULES_PATH = os.path.join(os.path.dirname(__file__), "market_event_rules.json")


class FinancialKnowledgeGraph:
    """
    Evaluates market events and news against codified financial causality rules.
    """

    def __init__(self, rules_file: str = RULES_PATH):
        self.rules_file = rules_file
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        try:
            with open(self.rules_file, "r", encoding="utf-8") as f:
                return json.load(f).get("categories", {})
        except Exception as e:
            print(f"Error loading rules: {e}")
            return {}

    def match_event(self, text: str) -> List[Dict[str, Any]]:
        """
        Cross-examines headline/text against the knowledge graph to detect active market catalysts.
        """
        lower_text = text.lower()
        matches = []

        for category_name, event_list in self.rules.items():
            for event in event_list:
                for keyword in event["keywords"]:
                    pattern = rf"\b{re.escape(keyword)}\b"
                    if re.search(pattern, lower_text):
                        matches.append({
                            "category": category_name,
                            "event_id": event["id"],
                            "matched_keyword": keyword,
                            "primary_effect": event["primary_effect"],
                            "affected_assets": event.get("affected_assets", []),
                            "crypto_bias": event.get("crypto_effect", "NEUTRAL"),
                            "equities_bias": event.get("equities_effect", "NEUTRAL"),
                            "commodities_bias": event.get("commodities_effect", "NEUTRAL"),
                            "confidence": event.get("confidence", 0.75),
                            "recommended_action": event.get("recommended_action", "HOLD")
                        })
                        break  # Avoid duplicate hits per event rule

        return matches

    def evaluate_news_intelligence(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriches a MiroFish news item with deterministic Knowledge Graph causality.
        """
        full_text = f"{news_item.get('title', '')} {news_item.get('summary', '')}"
        events = self.match_event(full_text)

        if not events:
            return {
                **news_item,
                "has_knowledge_catalyst": False,
                "catalysts": [],
                "knowledge_confidence": 0.50,
                "knowledge_recommendation": "NO_HISTORICAL_MATCH"
            }

        # Select highest confidence catalyst
        top_event = max(events, key=lambda x: x["confidence"])

        return {
            **news_item,
            "has_knowledge_catalyst": True,
            "catalysts": events,
            "primary_catalyst_id": top_event["event_id"],
            "knowledge_confidence": top_event["confidence"],
            "knowledge_recommendation": top_event["recommended_action"],
            "macro_effect_summary": top_event["primary_effect"]
        }


if __name__ == "__main__":
    kg = FinancialKnowledgeGraph()
    test_headlines = [
        "Federal Reserve announces surprise 50 bps rate cut amid economic slowdown",
        "Major cryptocurrency exchange hacked, loses 50,000 Bitcoins in security breach",
        "CPI drops to 2.1%, inflation cools faster than forecasted"
    ]
    for h in test_headlines:
        events = kg.match_event(h)
        print("Headline:", h)
        if events:
            print(f"-> Catalysts: {events[0]['event_id']} | Action: {events[0]['recommended_action']} | Conf: {events[0]['confidence']}")
        else:
            print("-> No match")
        print("---")
