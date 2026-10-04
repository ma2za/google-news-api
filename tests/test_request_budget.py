"""Fixture-based request-budget regression checks.

Asserts exact HTTP request counts and concurrency bounds for:
1. Cached versus uncached RSS search
2. Sync and async batch request counts
3. Decode concurrency bounding
4. Enrichment request count
5. Cluster parsing with zero additional requests
6. Monitor poll with no new results
"""

import asyncio
import json
import threading
from typing import List

import httpx
import pytest

from google_news_api import (
    ArticleEnricher,
    AsyncArticleEnricher,
    AsyncGoogleNewsClient,
    GoogleNewsClient,
)
from google_news_api.monitor import ArticleTracker

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Google News</title>
    <link>https://news.google.com</link>
    <item>
      <title>Budget Test Story - Tech News</title>
      <link>https://news.google.com/rss/articles/CBMi_budget_1</link>
      <pubDate>Mon, 05 Oct 2026 12:00:00 GMT</pubDate>
      <description>&lt;a href="https://news.google.com/rss/articles/CBMi_budget_1"&gt;Budget Test Story&lt;/a&gt;&amp;nbsp;&amp;nbsp;&lt;font color="#6f6f6f"&gt;Tech News&lt;/font&gt;&lt;ol&gt;&lt;li&gt;&lt;a href="https://news.google.com/rss/articles/CBMi_related_1"&gt;Related Story&lt;/a&gt;&amp;nbsp;&amp;nbsp;&lt;font color="#6f6f6f"&gt;Other Source&lt;/font&gt;&lt;/li&gt;&lt;/ol&gt;</description>  # noqa: E501
      <source url="https://technews.com">Tech News</source>
    </item>
    <item>
      <title>Second Budget Story - Finance News</title>
      <link>https://news.google.com/rss/articles/CBMi_budget_2</link>
      <pubDate>Mon, 05 Oct 2026 13:00:00 GMT</pubDate>
      <description>&lt;a href="https://news.google.com/rss/articles/CBMi_budget_2"&gt;Second Budget Story&lt;/a&gt;&amp;nbsp;&amp;nbsp;&lt;font color="#6f6f6f"&gt;Finance News&lt;/font&gt;</description>  # noqa: E501
      <source url="https://financenews.com">Finance News</source>
    </item>
  </channel>
</rss>
"""

CWIZ_HTML = """
<!DOCTYPE html>
<html>
<body>
  <c-wiz>
    <div jscontroller="c42" data-n-a-sg="sig-token" data-n-a-ts="1720000000"></div>
  </c-wiz>
</body>
</html>
"""


def _make_batch_body(target: str) -> str:
    inner = json.dumps([None, target])
    return f")]}}'\n\n{json.dumps([[None, None, inner], None, None])}"


class RequestBudgetTransport(httpx.BaseTransport, httpx.AsyncBaseTransport):
    """Transport that serves recorded fixtures and tracks request budgets."""

    def __init__(self, artificial_delay: float = 0.0):
        self.artificial_delay = artificial_delay
        self.request_count = 0
        self.active_concurrency = 0
        self.max_concurrency = 0
        self.requests: List[httpx.Request] = []
        self._lock = threading.Lock()

    def close(self) -> None:
        pass

    async def aclose(self) -> None:
        pass

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        with self._lock:
            self.request_count += 1
            self.active_concurrency += 1
            if self.active_concurrency > self.max_concurrency:
                self.max_concurrency = self.active_concurrency
            self.requests.append(request)

        try:
            if self.artificial_delay > 0:
                import time

                time.sleep(self.artificial_delay)

            url_str = str(request.url)
            if "batchexecute" in url_str:
                return httpx.Response(
                    200,
                    text=_make_batch_body("https://decoded-target.com/article"),
                    headers={"Content-Type": "text/plain"},
                    request=request,
                )
            elif "/articles/" in url_str:
                return httpx.Response(
                    200,
                    text=CWIZ_HTML,
                    headers={"Content-Type": "text/html"},
                    request=request,
                )
            else:
                return httpx.Response(
                    200,
                    text=SAMPLE_RSS,
                    headers={"Content-Type": "application/rss+xml"},
                    request=request,
                )
        finally:
            with self._lock:
                self.active_concurrency -= 1

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        with self._lock:
            self.request_count += 1
            self.active_concurrency += 1
            if self.active_concurrency > self.max_concurrency:
                self.max_concurrency = self.active_concurrency
            self.requests.append(request)

        try:
            if self.artificial_delay > 0:
                await asyncio.sleep(self.artificial_delay)

            url_str = str(request.url)
            if "batchexecute" in url_str:
                return httpx.Response(
                    200,
                    text=_make_batch_body("https://decoded-target.com/article"),
                    headers={"Content-Type": "text/plain"},
                    request=request,
                )
            elif "/articles/" in url_str:
                return httpx.Response(
                    200,
                    text=CWIZ_HTML,
                    headers={"Content-Type": "text/html"},
                    request=request,
                )
            else:
                return httpx.Response(
                    200,
                    text=SAMPLE_RSS,
                    headers={"Content-Type": "application/rss+xml"},
                    request=request,
                )
        finally:
            with self._lock:
                self.active_concurrency -= 1


# -----------------------------------------------------------------------------
# 1. Cached versus uncached RSS search budget
# -----------------------------------------------------------------------------


def test_sync_cached_versus_uncached_search_budget():
    transport = RequestBudgetTransport()
    client = GoogleNewsClient(transport=transport, cache_ttl=60)

    # First search: uncached -> exactly 1 HTTP request
    articles_1 = client.search("quantum computing")
    assert len(articles_1) == 2
    assert transport.request_count == 1

    # Second identical search: cached -> exactly 0 additional HTTP requests
    articles_2 = client.search("quantum computing")
    assert len(articles_2) == 2
    assert transport.request_count == 1

    # Third distinct search: uncached -> exactly 1 additional HTTP request
    articles_3 = client.search("neural networks")
    assert len(articles_3) == 2
    assert transport.request_count == 2


@pytest.mark.asyncio
async def test_async_cached_versus_uncached_search_budget():
    transport = RequestBudgetTransport()
    async with AsyncGoogleNewsClient(transport=transport, cache_ttl=60) as client:
        # First search: uncached -> exactly 1 HTTP request
        articles_1 = await client.search("quantum computing")
        assert len(articles_1) == 2
        assert transport.request_count == 1

        # Second identical search: cached -> exactly 0 additional HTTP requests
        articles_2 = await client.search("quantum computing")
        assert len(articles_2) == 2
        assert transport.request_count == 1

        # Third distinct search: uncached -> exactly 1 additional HTTP request
        articles_3 = await client.search("neural networks")
        assert len(articles_3) == 2
        assert transport.request_count == 2


# -----------------------------------------------------------------------------
# 2. Sync and async batch request counts
# -----------------------------------------------------------------------------


def test_sync_batch_search_request_count():
    transport = RequestBudgetTransport()
    client = GoogleNewsClient(transport=transport)

    queries = ["python", "rust", "golang"]
    results = client.batch_search(queries)

    assert len(results) == 3
    # N distinct uncached queries must yield exactly N HTTP requests
    assert transport.request_count == len(queries)


@pytest.mark.asyncio
async def test_async_batch_search_request_count():
    transport = RequestBudgetTransport()
    async with AsyncGoogleNewsClient(transport=transport) as client:
        queries = ["query_a", "query_b", "query_c", "query_d"]
        results = await client.batch_search(queries, max_concurrent=2, delay=0)

        assert len(results) == 4
        # N distinct uncached queries must yield exactly N HTTP requests
        assert transport.request_count == len(queries)


# -----------------------------------------------------------------------------
# 3. Decode concurrency bound
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_decode_concurrency_bound():
    # Transport with slight artificial delay to ensure concurrency overlap
    transport = RequestBudgetTransport(artificial_delay=0.03)
    async with AsyncGoogleNewsClient(transport=transport) as client:
        urls = [
            f"https://news.google.com/rss/articles/CBMi_concurrent_{i}"
            for i in range(6)
        ]
        max_limit = 2

        results = await client.decode_urls(urls, max_concurrent=max_limit, delay=0)

        assert len(results) == 6
        assert all(r == "https://decoded-target.com/article" for r in results)
        # Peak concurrency across all async workers must never exceed configured limit
        assert transport.max_concurrency <= max_limit


# -----------------------------------------------------------------------------
# 4. Enrichment request count
# -----------------------------------------------------------------------------


def test_sync_enrichment_request_count_budget():
    transport = RequestBudgetTransport()
    client = GoogleNewsClient(transport=transport)
    enricher = ArticleEnricher(client=client, delay=0)

    articles = [
        {
            "title": "Article 1",
            "link": "https://news.google.com/rss/articles/CBMi_art_1",
            "published": "2026-10-05",
            "summary": "Summary 1",
            "source": "Source 1",
        },
        {
            "title": "Article 2",
            "link": "https://news.google.com/rss/articles/CBMi_art_2",
            "published": "2026-10-05",
            "summary": "Summary 2",
            "source": "Source 2",
        },
    ]

    # decode_links=True, extract_text=False
    # Decoding requires 2 requests per article: 1 GET splash page + 1 POST batchexecute
    enriched = enricher.enrich(articles, decode_links=True, extract_text=False)
    assert len(enriched) == 2
    assert transport.request_count == 2 * len(articles)

    # decode_links=False, extract_text=False -> exactly 0 requests
    transport_noop = RequestBudgetTransport()
    client_noop = GoogleNewsClient(transport=transport_noop)
    enricher_noop = ArticleEnricher(client=client_noop, delay=0)
    enriched_noop = enricher_noop.enrich(
        articles, decode_links=False, extract_text=False
    )
    assert len(enriched_noop) == 2
    assert transport_noop.request_count == 0


@pytest.mark.asyncio
async def test_async_enrichment_request_count_budget():
    transport = RequestBudgetTransport()
    async with AsyncGoogleNewsClient(transport=transport) as client:
        enricher = AsyncArticleEnricher(client=client, delay=0)
        articles = [
            {
                "title": "Article A",
                "link": "https://news.google.com/rss/articles/CBMi_async_1",
                "published": "2026-10-05",
                "summary": "Summary A",
                "source": "Source A",
            }
        ]

        # 1 article: 2 requests (1 splash + 1 batchexecute)
        enriched = await enricher.enrich(
            articles, decode_links=True, extract_text=False
        )
        assert len(enriched) == 1
        assert transport.request_count == 2


# -----------------------------------------------------------------------------
# 5. Cluster parsing with no additional request
# -----------------------------------------------------------------------------


def test_sync_cluster_parsing_budget():
    transport = RequestBudgetTransport()
    client = GoogleNewsClient(transport=transport)

    # top_news_clusters extracts related coverage from the same feed payload
    clusters = client.top_news_clusters("WORLD")
    assert len(clusters) == 2
    assert len(clusters[0]["related"]) == 1
    # Exactly 1 HTTP request for the whole cluster extraction
    assert transport.request_count == 1


@pytest.mark.asyncio
async def test_async_cluster_parsing_budget():
    transport = RequestBudgetTransport()
    async with AsyncGoogleNewsClient(transport=transport) as client:
        clusters = await client.top_news_clusters("WORLD")
        assert len(clusters) == 2
        assert len(clusters[0]["related"]) == 1
        # Exactly 1 HTTP request for the whole cluster extraction
        assert transport.request_count == 1


# -----------------------------------------------------------------------------
# 6. Monitor poll with no new results
# -----------------------------------------------------------------------------


def test_monitor_poll_no_new_results_budget(tmp_path):
    transport = RequestBudgetTransport()
    client = GoogleNewsClient(transport=transport)
    state_file = str(tmp_path / "monitor_state.json")
    tracker = ArticleTracker(state_file)

    # Poll 1: initial run
    feed_1 = client.search("tech updates")
    new_1 = tracker.filter_new(feed_1, fingerprint="fp1", emit_existing=True)
    assert len(new_1) == 2
    assert transport.request_count == 1

    # Clear cache to simulate next polling cycle interval
    client._cache.clear()

    # Poll 2: returns same feed entries
    feed_2 = client.search("tech updates")
    new_2 = tracker.filter_new(feed_2, fingerprint="fp1", emit_existing=False)
    # Zero new articles emitted
    assert len(new_2) == 0
    # Exactly 1 feed request made during this poll, zero extra / secondary requests
    assert transport.request_count == 2
