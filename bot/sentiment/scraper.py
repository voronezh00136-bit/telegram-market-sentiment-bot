"""Async financial news scraper using Yahoo Finance RSS feeds and BeautifulSoup."""

import logging
from typing import Optional

import aiohttp
import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_YAHOO_RSS_TICKER = "https://finance.yahoo.com/rss/headline?s={ticker}"
_YAHOO_RSS_GENERAL = "https://finance.yahoo.com/news/rssindex"
_USER_AGENT = "MarketSentimentBot/1.0"


class NewsScraper:
    """Asynchronously fetches financial news headlines for sentiment analysis.

    Uses publicly available Yahoo Finance RSS feeds. Pass *api_key* if you want
    to extend coverage via NewsAPI.org (future integration hook).
    """

    def __init__(self, api_key: str = "", timeout: int = 15) -> None:
        self.api_key = api_key
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_news_for_ticker(self, ticker: str, limit: int = 10) -> list:
        """Return up to *limit* recent news articles for *ticker*.

        Each article is a dict with keys: title, summary, text, link, published.
        """
        url = _YAHOO_RSS_TICKER.format(ticker=ticker.upper())
        return await self._fetch_rss(url, limit)

    async def get_general_news(self, limit: int = 10) -> list:
        """Return up to *limit* general financial news articles."""
        return await self._fetch_rss(_YAHOO_RSS_GENERAL, limit)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch(self, url: str) -> str:
        """Perform an async GET request and return the response body as text."""
        headers = {"User-Agent": _USER_AGENT}
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                return await resp.text()

    async def _fetch_rss(self, url: str, limit: int = 10) -> list:
        """Fetch and parse an RSS feed, returning a list of article dicts."""
        try:
            content = await self._fetch(url)
            feed = feedparser.parse(content)
            articles = []
            for entry in feed.entries[:limit]:
                title = entry.get("title", "")
                raw_summary = entry.get("summary", "")
                summary = BeautifulSoup(raw_summary, "html.parser").get_text(
                    separator=" ", strip=True
                )
                articles.append(
                    {
                        "title": title,
                        "summary": summary,
                        "text": f"{title}. {summary}".strip(),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", ""),
                    }
                )
            return articles
        except Exception as exc:
            logger.warning("Failed to fetch RSS feed %s: %s", url, exc)
            return []
