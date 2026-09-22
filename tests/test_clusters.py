"""Tests for the related coverage clusters features."""

import pytest
from feedparser import FeedParserDict
from google_news_api.client import AsyncGoogleNewsClient, GoogleNewsClient


def test_parse_article_clusters_basic():
    """Test parsing clusters from feed entries with simple summary HTML."""
    feed = FeedParserDict()
    p_link = "http://primary.com"
    r_link_1 = "http://related1.com"
    r_link_2 = "http://related2.com"
    summary_html = (
        "<ol>"
        f"<li><a href=\"{p_link}\" target=\"_blank\">Primary Article Title</a>"
        "&nbsp;&nbsp;<font color=\"#6f6f6f\">Publisher Primary</font></li>"
        f"<li><a href=\"{r_link_1}\" target=\"_blank\">Related Article 1</a>"
        "&nbsp;&nbsp;<font color=\"#6f6f6f\">Publisher 1</font></li>"
        f"<li><a href=\"{r_link_2}\" target=\"_blank\">Related Article 2</a>"
        "&nbsp;&nbsp;<font color=\"#6f6f6f\">Publisher 2</font></li>"
        "<li><a href=\"https://news.google.com/stories/CAAqNggKIj...\" "
        "target=\"_blank\">See more headlines</a></li>"
        "</ol>"
    )

    feed.entries = [
        FeedParserDict(
            title="Primary Article Title - Publisher Primary",
            link="http://primary.com",
            published="Wed, 29 Jul 2026 12:00:00 GMT",
            summary=summary_html,
            source=FeedParserDict(title="Publisher Primary"),
            id="article-id",
        )
    ]

    client = object.__new__(GoogleNewsClient)
    clusters = client._parse_article_clusters(feed)

    assert len(clusters) == 1
    cluster = clusters[0]

    # Verify primary article matches top_news parser output
    assert cluster["primary"]["title"] == "Primary Article Title - Publisher Primary"
    assert cluster["primary"]["link"] == "http://primary.com"
    assert cluster["primary"]["summary"] == summary_html

    # Verify related articles are extracted and filtered
    # Primary article should be skipped. Story link should be skipped.
    assert len(cluster["related"]) == 2

    assert cluster["related"][0]["title"] == "Related Article 1"
    assert cluster["related"][0]["link"] == "http://related1.com"
    assert cluster["related"][0]["source"] == "Publisher 1"

    assert cluster["related"][1]["title"] == "Related Article 2"
    assert cluster["related"][1]["link"] == "http://related2.com"
    assert cluster["related"][1]["source"] == "Publisher 2"


def test_parse_article_clusters_deduplication():
    """Test that duplicate related articles are deduplicated."""
    feed = FeedParserDict()
    summary_html = (
        "<ol>"
        "<li><a href=\"http://related1.com\">Related 1</a>"
        "&nbsp;&nbsp;<font>Pub 1</font></li>"
        "<li><a href=\"http://related1.com\">Related 1 (Same Link)</a>"
        "&nbsp;&nbsp;<font>Pub 1</font></li>"
        "<li><a href=\"http://related2.com\">Related  2  with spaces</a>"
        "&nbsp;&nbsp;<font>Pub 2</font></li>"
        "<li><a href=\"http://related3.com\">related 2 with spaces</a>"
        "&nbsp;&nbsp;<font>Pub 3</font></li>"
        "</ol>"
    )

    feed.entries = [
        FeedParserDict(
            title="Primary Title",
            link="http://primary.com",
            published="Wed, 29 Jul 2026 12:00:00 GMT",
            summary=summary_html,
            source=FeedParserDict(title="Publisher Primary"),
            id="article-id",
        )
    ]

    client = object.__new__(GoogleNewsClient)
    clusters = client._parse_article_clusters(feed)

    assert len(clusters) == 1
    related = clusters[0]["related"]
    assert len(related) == 2
    assert related[0]["link"] == "http://related1.com"
    assert related[1]["link"] == "http://related2.com"


def test_parse_article_clusters_no_list():
    """Test entry without related articles."""
    feed = FeedParserDict()
    summary_html = "<a href=\"http://primary.com\">Primary</a> <font>Pub</font>"
    feed.entries = [
        FeedParserDict(
            title="Primary",
            link="http://primary.com",
            published="Wed, 29 Jul 2026 12:00:00 GMT",
            summary=summary_html,
            source=FeedParserDict(title="Publisher Primary"),
            id="article-id",
        )
    ]

    client = object.__new__(GoogleNewsClient)
    clusters = client._parse_article_clusters(feed)

    assert len(clusters) == 1
    assert clusters[0]["related"] == []


def test_parse_article_clusters_empty_or_missing_summary():
    """Test that empty or missing summary results in related = []."""
    feed = FeedParserDict()
    feed.entries = [
        FeedParserDict(
            title="Primary",
            link="http://primary.com",
            published="Wed, 29 Jul 2026 12:00:00 GMT",
            summary="",
            source=FeedParserDict(title="Publisher Primary"),
            id="article-id",
        )
    ]

    client = object.__new__(GoogleNewsClient)
    clusters = client._parse_article_clusters(feed)

    assert len(clusters) == 1
    assert clusters[0]["related"] == []


def test_parse_article_clusters_max_results():
    """Test that max_results correctly limits primary cluster count."""
    feed = FeedParserDict()
    feed.entries = [
        FeedParserDict(title=f"Article {i}", link=f"http://art{i}.com")
        for i in range(5)
    ]

    client = object.__new__(GoogleNewsClient)

    # max_results = 0 -> empty
    assert len(client._parse_article_clusters(feed, max_results=0)) == 0
    # max_results = 2 -> first two primaries
    clusters = client._parse_article_clusters(feed, max_results=2)
    assert len(clusters) == 2
    assert clusters[0]["primary"]["title"] == "Article 0"
    assert clusters[1]["primary"]["title"] == "Article 1"


def test_parse_article_clusters_malformed_html_graceful_fallback(monkeypatch):
    """Test that malformed HTML parsing exception is caught."""
    feed = FeedParserDict()
    feed.entries = [
        FeedParserDict(
            title="Primary",
            link="http://primary.com",
            published="Wed, 29 Jul 2026 12:00:00 GMT",
            summary="<ol><li>malformed",
            source=FeedParserDict(title="Publisher Primary"),
            id="article-id",
        )
    ]

    # Force selectolax HTMLParser to raise an exception for testing
    def mock_parser_init(*args, **kwargs):
        raise ValueError("Simulated parsing error")

    monkeypatch.setattr("google_news_api.client.HTMLParser", mock_parser_init)

    client = object.__new__(GoogleNewsClient)
    clusters = client._parse_article_clusters(feed)

    assert len(clusters) == 1
    assert clusters[0]["primary"]["title"] == "Primary"
    assert clusters[0]["related"] == []


def test_primary_result_equality_with_top_news():
    """Test that primary results are identical to top_news results."""
    feed = FeedParserDict()
    sum_html = "<ol><li><a href=\"http://primary.com\">P</a><font>P</font></li></ol>"
    feed.entries = [
        FeedParserDict(
            title="Primary Title",
            link="http://primary.com",
            published="Wed, 29 Jul 2026 12:00:00 GMT",
            summary=sum_html,
            source=FeedParserDict(title="Pub"),
            id="id1",
        )
    ]

    client = object.__new__(GoogleNewsClient)
    articles = client._parse_articles(feed)
    clusters = client._parse_article_clusters(feed)

    assert len(articles) == len(clusters)
    assert articles[0] == clusters[0]["primary"]


@pytest.mark.asyncio
async def test_async_top_news_clusters_client_method(monkeypatch):
    """Test top_news_clusters method in AsyncGoogleNewsClient."""
    feed = FeedParserDict()
    feed.entries = [
        FeedParserDict(
            title="Primary",
            link="http://primary.com",
            published="Wed, 29 Jul 2026 12:00:00 GMT",
            summary="<ol><li><a href=\"http://related.com\">Related</a></li></ol>",
            source=FeedParserDict(title="Pub"),
            id="id1",
        )
    ]

    async def mock_fetch_feed(self, url):
        return feed

    monkeypatch.setattr(AsyncGoogleNewsClient, "_fetch_feed", mock_fetch_feed)

    async with AsyncGoogleNewsClient() as client:
        clusters = await client.top_news_clusters(topic="WORLD")
        assert len(clusters) == 1
        assert clusters[0]["primary"]["title"] == "Primary"
        assert len(clusters[0]["related"]) == 1
        assert clusters[0]["related"][0]["link"] == "http://related.com"


def test_sync_top_news_clusters_client_method(monkeypatch):
    """Test top_news_clusters method in GoogleNewsClient."""
    feed = FeedParserDict()
    feed.entries = [
        FeedParserDict(
            title="Primary",
            link="http://primary.com",
            published="Wed, 29 Jul 2026 12:00:00 GMT",
            summary="<ol><li><a href=\"http://related.com\">Related</a></li></ol>",
            source=FeedParserDict(title="Pub"),
            id="id1",
        )
    ]

    def mock_fetch_feed(self, url):
        return feed

    monkeypatch.setattr(GoogleNewsClient, "_fetch_feed", mock_fetch_feed)

    with GoogleNewsClient() as client:
        clusters = client.top_news_clusters(topic="WORLD")
        assert len(clusters) == 1
        assert clusters[0]["primary"]["title"] == "Primary"
        assert len(clusters[0]["related"]) == 1
        assert clusters[0]["related"][0]["link"] == "http://related.com"


@pytest.mark.integration
def test_live_top_news_clusters_probe():
    """Live probe to verify that parsing works on actual Google News RSS."""
    with GoogleNewsClient() as client:
        clusters = client.top_news_clusters(topic="WORLD", max_results=5)
        assert len(clusters) > 0

        # Verify shape of returned structures
        for cluster in clusters:
            primary = cluster["primary"]
            assert "title" in primary
            assert "link" in primary
            assert "source" in primary
            assert "summary" in primary

            # Related articles
            for rel in cluster["related"]:
                assert "title" in rel
                assert "link" in rel
                assert "source" in rel
                # Verify story links are not present
                assert "/stories/" not in (rel["link"] or "")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_async_top_news_clusters_probe():
    """Live async probe to verify that parsing works on actual Google News RSS."""
    async with AsyncGoogleNewsClient() as client:
        clusters = await client.top_news_clusters(topic="WORLD", max_results=5)
        assert len(clusters) > 0

        for cluster in clusters:
            primary = cluster["primary"]
            assert "title" in primary
            assert "link" in primary
            assert "source" in primary

            for rel in cluster["related"]:
                assert "title" in rel
                assert "link" in rel
                assert "source" in rel
                assert "/stories/" not in (rel["link"] or "")
