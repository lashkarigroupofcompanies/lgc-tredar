"""
WorldMonitor Live Feed Engine
Curated Global Macro, Financial, Commodity, and Crypto RSS Feeds
Extracted and adapted from WorldMonitor (koala73) architecture.
"""

import logging
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Any, Optional
import feedparser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WorldMonitorFeed")

# Curated High-Impact Global Financial & Macro Feeds from WorldMonitor
FEEDS_CATALOG: Dict[str, List[Dict[str, str]]] = {
    "markets": [
        {"name": "CNBC Market News", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
        {"name": "Yahoo Finance Top Stories", "url": "https://finance.yahoo.com/rss/topstories"},
        {"name": "Seeking Alpha Currents", "url": "https://seekingalpha.com/market_currents.xml"},
        {"name": "Reuters Markets", "url": "https://news.google.com/rss/search?q=site:reuters.com+markets+stocks+when:1d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Bloomberg Markets", "url": "https://news.google.com/rss/search?q=site:bloomberg.com+markets+when:1d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Investing.com News", "url": "https://news.google.com/rss/search?q=site:investing.com+markets+when:1d&hl=en-US&gl=US&ceid=US:en"},
    ],
    "crypto": [
        {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
        {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss"},
        {"name": "The Block", "url": "https://news.google.com/rss/search?q=site:theblock.co+when:1d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Decrypt", "url": "https://decrypt.co/feed"},
        {"name": "Bitcoin Magazine", "url": "https://bitcoinmagazine.com/feed"},
    ],
    "macro_centralbanks": [
        {"name": "Federal Reserve Press", "url": "https://www.federalreserve.gov/feeds/press_all.xml"},
        {"name": "ECB & Global Rates", "url": "https://news.google.com/rss/search?q=(\"central+bank\"+OR+\"interest+rate\"+OR+\"rate+decision\"+OR+\"monetary+policy\")+when:2d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Economic Inflation & CPI", "url": "https://news.google.com/rss/search?q=(CPI+OR+inflation+OR+GDP+OR+\"jobs+report\")+when:2d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Dollar Watch (DXY)", "url": "https://news.google.com/rss/search?q=(\"dollar+index\"+OR+DXY+OR+\"US+dollar\")+when:2d&hl=en-US&gl=US&ceid=US:en"},
    ],
    "commodities": [
        {"name": "Crude Oil & OPEC", "url": "https://news.google.com/rss/search?q=(oil+price+OR+OPEC+OR+\"crude+oil\"+OR+WTI+OR+Brent)+when:1d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Gold & Silver Metals", "url": "https://news.google.com/rss/search?q=(gold+price+OR+silver+price+OR+\"precious+metals\")+when:2d&hl=en-US&gl=US&ceid=US:en"},
    ],
    "india_markets": [
        {"name": "Economic Times Markets", "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"},
        {"name": "Moneycontrol News", "url": "https://news.google.com/rss/search?q=site:moneycontrol.com+market+nifty+when:1d&hl=en-IN&gl=IN&ceid=IN:en"},
        {"name": "Livemint Markets", "url": "https://www.livemint.com/rss/markets"},
    ]
}


class WorldMonitorFeedEngine:
    """
    Asynchronously aggregates and parses global financial intelligence feeds.
    """

    def __init__(self, timeout_seconds: int = 7):
        self.timeout = timeout_seconds

    def _fetch_single_feed(self, source_name: str, category: str, url: str) -> List[Dict[str, Any]]:
        items = []
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:6]:  # Keep the freshest 6 items per feed
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()
                link = entry.get("link", "").strip()
                published = entry.get("published", entry.get("updated", datetime.utcnow().isoformat()))

                if not title:
                    continue

                items.append({
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "source": source_name,
                    "category": category,
                    "published": str(published),
                    "timestamp": datetime.utcnow().timestamp()
                })
        except Exception as e:
            logger.debug(f"Feed fetch skipped for {source_name}: {e}")
        return items

    def fetch_all(self, categories: Optional[List[str]] = None, max_total_items: int = 35) -> List[Dict[str, Any]]:
        """
        Fetch all feeds in parallel using ThreadPoolExecutor.
        """
        selected_categories = categories or list(FEEDS_CATALOG.keys())
        feed_tasks = []

        for cat in selected_categories:
            if cat in FEEDS_CATALOG:
                for feed in FEEDS_CATALOG[cat]:
                    feed_tasks.append((feed["name"], cat, feed["url"]))

        all_news: List[Dict[str, Any]] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            future_to_feed = {
                executor.submit(self._fetch_single_feed, name, cat, url): name 
                for name, cat, url in feed_tasks
            }
            for future in concurrent.futures.as_completed(future_to_feed):
                try:
                    results = future.result()
                    all_news.extend(results)
                except Exception as exc:
                    logger.debug(f"Task generated exception: {exc}")

        # Sort by timestamp and deduplicate by title
        seen_titles = set()
        deduped = []
        for item in all_news:
            clean_title = item["title"].lower().strip()
            if clean_title not in seen_titles:
                seen_titles.add(clean_title)
                deduped.append(item)

        return deduped[:max_total_items]


if __name__ == "__main__":
    engine = WorldMonitorFeedEngine()
    print("Testing WorldMonitor Feed Engine...")
    feeds = engine.fetch_all(categories=["crypto", "markets"], max_total_items=5)
    for f in feeds:
        print(f"[{f['category'].upper()}] {f['source']}: {f['title']}")
