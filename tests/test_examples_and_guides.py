"""Tests ensuring all examples and documentation guides are executable offline."""

import httpx
import pytest

from examples import advanced_usage, basic_usage
from google_news_api import (
    ArticleEnricher,
    AsyncGoogleNewsClient,
    ClientConfig,
    GoogleNewsClient,
    NewsQuery,
    deduplicate_articles,
    normalize_articles,
    sort_articles,
)
from google_news_api.monitor import ArticleTracker

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Google News</title>
    <link>https://news.google.com</link>
    <item>
      <title>Robotics Breakthrough - Tech Science</title>
      <link>https://news.google.com/rss/articles/CBMi_example_1</link>
      <pubDate>Mon, 05 Oct 2026 14:00:00 GMT</pubDate>
      <description>&lt;a href="https://news.google.com/rss/articles/CBMi_example_1"&gt;Robotics Breakthrough&lt;/a&gt;&amp;nbsp;&amp;nbsp;&lt;font color="#6f6f6f"&gt;Tech Science&lt;/font&gt;&lt;ol&gt;&lt;li&gt;&lt;a href="https://news.google.com/rss/articles/CBMi_rel"&gt;Related Story&lt;/a&gt;&amp;nbsp;&amp;nbsp;&lt;font color="#6f6f6f"&gt;Other&lt;/font&gt;&lt;/li&gt;&lt;/ol&gt;</description>  # noqa: E501
      <source url="https://techscience.com">Tech Science</source>
    </item>
  </channel>
</rss>
"""


def _make_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "batchexecute" in url_str:
            return httpx.Response(
                200,
                text=')]}}\'\n\n[[null, null, "[null, \\"https://techscience.com/news/1\\"]"], null, null]',  # noqa: E501
                request=request,
            )
        elif "/articles/" in url_str:
            cwiz = '<c-wiz><div jscontroller="x" data-n-a-sg="sg" data-n-a-ts="100"></div></c-wiz>'  # noqa: E501
            return httpx.Response(200, text=cwiz, request=request)
        return httpx.Response(200, text=SAMPLE_RSS, request=request)

    return httpx.MockTransport(handler)


# -----------------------------------------------------------------------------
# Test Examples Scripts Offline
# -----------------------------------------------------------------------------


def test_basic_usage_sync_offline(capsys):
    transport = _make_transport()
    client = GoogleNewsClient(transport=transport)
    basic_usage.sync_example(client=client)
    captured = capsys.readouterr()
    assert "Synchronous Client Example" in captured.out
    assert "Robotics Breakthrough" in captured.out


@pytest.mark.asyncio
async def test_basic_usage_async_offline(capsys):
    transport = _make_transport()
    client = AsyncGoogleNewsClient(transport=transport)
    await basic_usage.async_example(client=client)
    captured = capsys.readouterr()
    assert "Asynchronous Client Example" in captured.out
    assert "Robotics Breakthrough" in captured.out


@pytest.mark.asyncio
async def test_advanced_usage_offline(capsys):
    transport = _make_transport()
    client_es = AsyncGoogleNewsClient(transport=transport, language="es", country="ES")
    client_en = AsyncGoogleNewsClient(transport=transport, language="en", country="US")
    await advanced_usage.main(client_es=client_es, client_en=client_en)
    captured = capsys.readouterr()
    assert "Top News from Spain" in captured.out
    assert "Technology News" in captured.out


# -----------------------------------------------------------------------------
# Test Snippets in Guides
# -----------------------------------------------------------------------------


def test_guide_first_search_snippets():
    transport = _make_transport()
    with GoogleNewsClient(transport=transport) as client:
        articles = client.search("artificial intelligence", max_results=5)
        assert len(articles) == 1
        assert articles[0]["source"] == "Tech Science"

        tech = client.top_news(topic="TECHNOLOGY", max_results=3)
        assert len(tech) == 1


@pytest.mark.asyncio
async def test_guide_async_batch_snippets():
    transport = _make_transport()
    async with AsyncGoogleNewsClient(transport=transport) as client:
        queries = ["driving", "batteries"]
        results = await client.batch_search(queries, max_concurrent=2, delay=0)
        assert len(results) == 2
        assert "driving" in results


def test_guide_geographic_headlines_snippets():
    transport = _make_transport()
    with GoogleNewsClient(transport=transport) as client:
        articles = client.location_news("Chicago", max_results=5)
        assert len(articles) == 1
        assert articles[0]["title"] == "Robotics Breakthrough - Tech Science"


def test_guide_advanced_queries_snippets():
    query = NewsQuery(
        text="solar",
        exact_phrase="clean energy",
        exclude_words=["subsidies"],
        in_title="breakthrough",
    ).build()
    assert '"clean energy"' in query
    assert "solar" in query
    assert "-subsidies" in query
    assert 'intitle:"breakthrough"' in query

    transport = _make_transport()
    with GoogleNewsClient(transport=transport) as client:
        dated = client.search(
            "nobel prize",
            after="2026-01-01",
            before="2026-10-01",
        )
        assert len(dated) == 1


def test_guide_clean_dataset_export_snippets():
    raw_articles = [
        {
            "title": "Clean Energy Revolution",
            "link": "https://www.reuters.com/business/clean-energy-1",
            "published": "Mon, 05 Oct 2026 12:00:00 GMT",
            "summary": "Summary...",
            "source": "Reuters",
        },
        {
            "title": "Clean Energy Revolution",  # duplicate title
            "link": "https://www.reuters.com/business/clean-energy-2",
            "published": "Mon, 05 Oct 2026 13:00:00 GMT",
            "summary": "Summary...",
            "source": "Syndicated",
        },
    ]

    normalized = normalize_articles(raw_articles)
    assert normalized[0]["source_domain"] == "www.reuters.com"
    assert normalized[0]["published_datetime"] is not None

    unique = deduplicate_articles(normalized, by="title")
    assert len(unique) == 1

    sorted_arts = sort_articles(unique, newest_first=True)
    assert len(sorted_arts) == 1


def test_guide_full_text_enrichment_snippets():
    transport = _make_transport()
    with GoogleNewsClient(transport=transport) as client:
        enricher = ArticleEnricher(client=client, delay=0)
        articles = [
            {
                "title": "Robotics",
                "link": "https://news.google.com/rss/articles/CBMi_test",
                "published": "2026-10-05",
                "summary": "Sum",
                "source": "Tech",
            }
        ]
        enriched = enricher.enrich(articles, decode_links=True, extract_text=False)
        assert enriched[0]["link"] == "https://techscience.com/news/1"
        assert (
            enriched[0]["google_link"]
            == "https://news.google.com/rss/articles/CBMi_test"
        )


def test_guide_custom_transports_snippets():
    transport = _make_transport()
    config = ClientConfig(
        language="en",
        country="US",
        timeout=20.0,
        headers={"X-App": "Crawler"},
        transport=transport,
    )
    with GoogleNewsClient.from_config(config) as client:
        articles = client.search("market outlook", max_results=5)
        assert len(articles) == 1


def test_guide_incremental_monitoring_snippets(tmp_path):
    transport = _make_transport()
    with GoogleNewsClient(transport=transport) as client:
        tracker = ArticleTracker(str(tmp_path / "state.json"))
        articles = client.search("cyberattack")
        new_arts = tracker.filter_new(articles, fingerprint="fp", emit_existing=True)
        assert len(new_arts) == 1
