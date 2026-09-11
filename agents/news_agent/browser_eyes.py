"""
Agent Eyes & Live Web Browser Engine
Provides autonomous browser capabilities for agents to inspect live news,
read economic calendars, and extract real-time web intelligence.
"""

import logging
import asyncio
import urllib.parse
from typing import Dict, Any, Optional, List
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BrowserEyes")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


class BrowserEyesEngine:
    """
    Autonomous browser and web vision tool for agents.
    Provides fast HTTP scraping with fallback to Playwright headless automation.
    """

    def __init__(self, use_headless_browser: bool = False):
        self.use_headless_browser = use_headless_browser
        self.headers = {"User-Agent": USER_AGENT}

    def fetch_webpage_content(self, url: str, max_chars: int = 4000) -> Dict[str, Any]:
        """
        Fast lightweight web reader using Requests + BeautifulSoup.
        """
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return {"success": False, "error": f"HTTP {resp.status_code}", "content": ""}

            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove scripts, styles, navigation bars
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.extract()

            text = soup.get_text(separator=" ", strip=True)
            clean_text = " ".join(text.split())[:max_chars]

            return {
                "success": True,
                "url": url,
                "title": soup.title.get_text(strip=True) if soup.title else "",
                "content": clean_text
            }
        except Exception as e:
            logger.error(f"Error reading {url}: {e}")
            return {"success": False, "error": str(e), "content": ""}

    async def fetch_with_playwright(self, url: str, wait_selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Full JavaScript-rendering browser for dynamic web apps, charts, and trading portals.
        """
        try:
            import importlib
            playwright_mod = importlib.import_module("playwright.async_api")
            async_playwright = getattr(playwright_mod, "async_playwright")
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=USER_AGENT)
                await page.goto(url, timeout=25000, wait_until="domcontentloaded")

                if wait_selector:
                    await page.wait_for_selector(wait_selector, timeout=5000)
                else:
                    await asyncio.sleep(2)  # Give JS a moment to hydrate

                title = await page.title()
                content = await page.inner_text("body")
                clean_content = " ".join(content.split())[:5000]

                await browser.close()
                return {
                    "success": True,
                    "url": url,
                    "title": title,
                    "content": clean_content
                }
        except ImportError:
            logger.warning("Playwright not installed, falling back to static parser.")
            return self.fetch_webpage_content(url)
        except Exception as e:
            logger.error(f"Playwright browser error on {url}: {e}")
            return self.fetch_webpage_content(url)

    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Free web search without requiring an API key.
        """
        try:
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            resp = requests.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            results: List[Dict[str, str]] = []

            for result in soup.find_all("div", class_="result__body")[:max_results]:
                title_elem = result.find("a", class_="result__a")
                snippet_elem = result.find("a", class_="result__snippet")

                if title_elem:
                    href = title_elem.get("href")
                    link_str = href[0] if isinstance(href, list) and href else (str(href) if href else "")
                    snippet_str = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    results.append({
                        "title": str(title_elem.get_text(strip=True)),
                        "link": link_str,
                        "snippet": snippet_str
                    })

            return results
        except Exception as e:
            logger.error(f"Search failed for {query}: {e}")
            return []


if __name__ == "__main__":
    eyes = BrowserEyesEngine()
    print("Testing Browser Eyes web search...")
    res = eyes.search_duckduckgo("bitcoin market news today", max_results=2)
    print("Search Results:", res)
