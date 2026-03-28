"""Unit tests for the async news scraper (network calls are fully mocked)."""

import pytest
from unittest.mock import AsyncMock, patch

from bot.sentiment.scraper import NewsScraper


SAMPLE_RSS = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Yahoo Finance</title>
    <item>
      <title>Apple reports record iPhone sales</title>
      <description>AAPL shares jumped 5% after earnings beat.</description>
      <link>https://finance.yahoo.com/news/apple-record</link>
      <pubDate>Fri, 27 Feb 2026 12:00:00 +0000</pubDate>
    </item>
    <item>
      <title>Tech stocks surge on AI optimism</title>
      <description>Investors pour into tech sector amid AI boom.</description>
      <link>https://finance.yahoo.com/news/tech-surge</link>
      <pubDate>Fri, 27 Feb 2026 11:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>
"""

EMPTY_RSS = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Empty</title></channel></rss>
"""


@pytest.fixture
def scraper():
    return NewsScraper()


# ---------------------------------------------------------------------------
# _fetch_rss
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_rss_parses_articles(scraper):
    with patch.object(scraper, "_fetch", new=AsyncMock(return_value=SAMPLE_RSS)):
        articles = await scraper._fetch_rss("https://example.com/rss", limit=10)
    assert len(articles) == 2
    assert articles[0]["title"] == "Apple reports record iPhone sales"
    assert "link" in articles[0]
    assert "text" in articles[0]
    assert "AAPL" in articles[0]["text"]


@pytest.mark.asyncio
async def test_fetch_rss_respects_limit(scraper):
    with patch.object(scraper, "_fetch", new=AsyncMock(return_value=SAMPLE_RSS)):
        articles = await scraper._fetch_rss("https://example.com/rss", limit=1)
    assert len(articles) == 1
    assert articles[0]["title"] == "Apple reports record iPhone sales"


@pytest.mark.asyncio
async def test_fetch_rss_returns_empty_on_network_error(scraper):
    with patch.object(scraper, "_fetch", new=AsyncMock(side_effect=Exception("Network error"))):
        articles = await scraper._fetch_rss("https://example.com/rss")
    assert articles == []


@pytest.mark.asyncio
async def test_fetch_rss_returns_empty_for_empty_feed(scraper):
    with patch.object(scraper, "_fetch", new=AsyncMock(return_value=EMPTY_RSS)):
        articles = await scraper._fetch_rss("https://example.com/rss")
    assert articles == []


# ---------------------------------------------------------------------------
# get_news_for_ticker
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_news_for_ticker_uses_ticker_in_url(scraper):
    with patch.object(scraper, "_fetch_rss", new=AsyncMock(return_value=[])) as mock_rss:
        await scraper.get_news_for_ticker("AAPL", limit=5)
    mock_rss.assert_called_once()
    call_url = mock_rss.call_args[0][0]
    assert "AAPL" in call_url


@pytest.mark.asyncio
async def test_get_news_for_ticker_uppercases_symbol(scraper):
    with patch.object(scraper, "_fetch_rss", new=AsyncMock(return_value=[])) as mock_rss:
        await scraper.get_news_for_ticker("tsla")
    call_url = mock_rss.call_args[0][0]
    assert "TSLA" in call_url
    assert "tsla" not in call_url


@pytest.mark.asyncio
async def test_get_news_for_ticker_passes_limit(scraper):
    with patch.object(scraper, "_fetch_rss", new=AsyncMock(return_value=[])) as mock_rss:
        await scraper.get_news_for_ticker("MSFT", limit=3)
    _, kwargs = mock_rss.call_args
    assert kwargs.get("limit") == 3 or mock_rss.call_args[0][1] == 3


# ---------------------------------------------------------------------------
# get_general_news
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_general_news_calls_general_rss(scraper):
    with patch.object(scraper, "_fetch_rss", new=AsyncMock(return_value=[])) as mock_rss:
        await scraper.get_general_news(limit=5)
    mock_rss.assert_called_once()
    call_url = mock_rss.call_args[0][0]
    assert "yahoo" in call_url.lower()


# ---------------------------------------------------------------------------
# Article dict shape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_article_dict_has_required_keys(scraper):
    with patch.object(scraper, "_fetch", new=AsyncMock(return_value=SAMPLE_RSS)):
        articles = await scraper._fetch_rss("https://example.com/rss", limit=10)
    for article in articles:
        assert {"title", "summary", "text", "link", "published"}.issubset(article.keys())
