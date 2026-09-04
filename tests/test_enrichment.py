import asyncio
import threading
import time
from copy import deepcopy
from types import SimpleNamespace

import pytest

from google_news_api import ArticleEnricher, AsyncArticleEnricher, enrichment
from google_news_api.exceptions import ValidationError


def article(link, title="Title"):
    return {
        "title": title,
        "link": link,
        "published": "2026-08-30",
        "summary": "Summary",
        "source": "Example",
        "id": title.lower(),
    }


class SyncHTTPClient:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        status, text = self.responses.get(url, (200, "<article>Text</article>"))
        return SimpleNamespace(status_code=status, text=text)


class SyncClient:
    def __init__(self, decoded_urls=None, responses=None):
        self.decoded_urls = decoded_urls or []
        self.decode_calls = []
        self._client = SyncHTTPClient(responses)

    def decode_urls(self, urls, **kwargs):
        self.decode_calls.append((urls, kwargs))
        return self.decoded_urls


class AsyncHTTPClient:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    async def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        status, text = self.responses.get(url, (200, "<article>Text</article>"))
        return SimpleNamespace(status_code=status, text=text)


class AsyncClient:
    def __init__(self, decoded_urls=None, responses=None):
        self.decoded_urls = decoded_urls or []
        self.decode_calls = []
        self.client = AsyncHTTPClient(responses)

    async def decode_urls(self, urls, **kwargs):
        self.decode_calls.append((urls, kwargs))
        return self.decoded_urls


def test_sync_enrichment_decodes_extracts_and_preserves_input(monkeypatch):
    google_url = "https://news.google.com/rss/articles/id"
    publisher_url = "https://example.com/article"
    articles = [article(google_url)]
    original = deepcopy(articles)
    client = SyncClient(decoded_urls=[publisher_url])
    monkeypatch.setattr(enrichment, "_load_extractor", lambda: lambda html: "Text")

    result = ArticleEnricher(client, max_concurrent=2, timeout=12.5, delay=0).enrich(
        articles, extract_text=True
    )

    assert articles == original
    assert client.decode_calls == [([google_url], {"timeout": 12.5, "delay": 0})]
    assert client._client.calls == [(publisher_url, {"timeout": 12.5})]
    assert result == [
        {
            **original[0],
            "google_link": google_url,
            "link": publisher_url,
            "text": "Text",
        }
    ]


def test_sync_enrichment_keeps_decode_failures_aligned(monkeypatch):
    first = "https://news.google.com/rss/articles/first"
    second = "https://news.google.com/rss/articles/second"
    client = SyncClient(
        decoded_urls=["https://example.com/first", None],
    )
    monkeypatch.setattr(enrichment, "_load_extractor", lambda: lambda html: "Text")

    result = ArticleEnricher(client, delay=0).enrich(
        [article(first, "First"), article(second, "Second")],
        extract_text=True,
    )

    assert result[0]["google_link"] == first
    assert result[0]["text"] == "Text"
    assert result[1]["link"] == second
    assert "google_link" not in result[1]
    assert "text" not in result[1]


def test_invalid_decoded_and_article_urls_are_left_unchanged():
    google_url = "https://news.google.com/rss/articles/id"
    malformed_url = "http://[invalid"
    client = SyncClient(decoded_urls=[malformed_url])

    result = ArticleEnricher(client, delay=0).enrich(
        [article(google_url), article(malformed_url)],
    )

    assert result[0]["link"] == google_url
    assert result[1]["link"] == malformed_url


def test_sync_enrichment_extracts_direct_publisher_links(monkeypatch):
    publisher_url = "https://example.com/article"
    client = SyncClient()
    monkeypatch.setattr(enrichment, "_load_extractor", lambda: lambda html: None)

    result = ArticleEnricher(client, delay=0).enrich(
        [article(publisher_url)],
        decode_links=False,
        extract_text=True,
    )

    assert client.decode_calls == []
    assert result[0]["link"] == publisher_url
    assert result[0]["text"] == ""


def test_decode_only_does_not_load_extraction_dependency(monkeypatch):
    google_url = "https://news.google.com/rss/articles/id"
    publisher_url = "https://example.com/article"
    client = SyncClient(decoded_urls=[publisher_url])

    def unexpected_load():
        raise AssertionError("extract dependency should remain lazy")

    monkeypatch.setattr(enrichment, "_load_extractor", unexpected_load)

    result = ArticleEnricher(client, delay=0).enrich(
        [article(google_url)],
        extract_text=False,
    )

    assert result[0]["google_link"] == google_url
    assert result[0]["link"] == publisher_url
    assert "text" not in result[0]


def test_sync_enrichment_isolates_fetch_and_extraction_failures(monkeypatch):
    urls = [
        "https://example.com/good",
        "https://example.com/http-error",
        "https://example.com/extract-error",
    ]
    client = SyncClient(responses={urls[1]: (503, ""), urls[2]: (200, "bad")})

    def extract(html):
        if html == "bad":
            raise ValueError("broken document")
        return "Text"

    monkeypatch.setattr(enrichment, "_load_extractor", lambda: extract)

    result = ArticleEnricher(client, delay=0).enrich(
        [article(url, str(index)) for index, url in enumerate(urls)],
        extract_text=True,
    )

    assert result[0]["text"] == "Text"
    assert "text" not in result[1]
    assert "text" not in result[2]


def test_missing_extract_extra_fails_before_decoding(monkeypatch):
    client = SyncClient(decoded_urls=["https://example.com/article"])

    def missing():
        raise RuntimeError(enrichment.EXTRACT_EXTRA_INSTALL_MESSAGE)

    monkeypatch.setattr(enrichment, "_load_extractor", missing)

    with pytest.raises(RuntimeError, match=r"google-news-api\[extract\]"):
        ArticleEnricher(client).enrich(
            [article("https://news.google.com/rss/articles/id")],
            extract_text=True,
        )

    assert client.decode_calls == []


@pytest.mark.parametrize(
    ("kwargs", "field"),
    [
        ({"max_concurrent": 0}, "max_concurrent"),
        ({"max_concurrent": True}, "max_concurrent"),
        ({"timeout": 0}, "timeout"),
        ({"timeout": "slow"}, "timeout"),
        ({"delay": -1}, "delay"),
        ({"delay": False}, "delay"),
    ],
)
def test_enricher_configuration_validation(kwargs, field):
    with pytest.raises(ValidationError) as exc_info:
        ArticleEnricher(SyncClient(), **kwargs)
    assert exc_info.value.field == field


def test_sync_extraction_respects_concurrency_limit(monkeypatch):
    lock = threading.Lock()
    active = 0
    peak = 0

    class ConcurrentHTTPClient:
        def get(self, url, **kwargs):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            time.sleep(0.03)
            with lock:
                active -= 1
            return SimpleNamespace(status_code=200, text="html")

    client = SyncClient()
    client._client = ConcurrentHTTPClient()
    monkeypatch.setattr(enrichment, "_load_extractor", lambda: lambda html: "Text")

    ArticleEnricher(client, max_concurrent=2, delay=0).enrich(
        [article(f"https://example.com/{index}") for index in range(4)],
        extract_text=True,
    )

    assert peak == 2


@pytest.mark.asyncio
async def test_async_enrichment_matches_sync_behavior(monkeypatch):
    google_url = "https://news.google.com/rss/articles/id"
    publisher_url = "https://example.com/article"
    client = AsyncClient(decoded_urls=[publisher_url])
    monkeypatch.setattr(enrichment, "_load_extractor", lambda: lambda html: "Text")

    result = await AsyncArticleEnricher(
        client, max_concurrent=3, timeout=7, delay=0
    ).enrich([article(google_url)], extract_text=True)

    assert client.decode_calls == [
        (
            [google_url],
            {"max_concurrent": 3, "timeout": 7, "delay": 0},
        )
    ]
    assert client.client.calls == [(publisher_url, {"timeout": 7})]
    assert result[0]["google_link"] == google_url
    assert result[0]["link"] == publisher_url
    assert result[0]["text"] == "Text"


@pytest.mark.asyncio
async def test_async_extraction_respects_concurrency_limit(monkeypatch):
    active = 0
    peak = 0

    class ConcurrentHTTPClient:
        async def get(self, url, **kwargs):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.03)
            active -= 1
            return SimpleNamespace(status_code=200, text="html")

    client = AsyncClient()
    client.client = ConcurrentHTTPClient()
    monkeypatch.setattr(enrichment, "_load_extractor", lambda: lambda html: "Text")

    await AsyncArticleEnricher(client, max_concurrent=2, delay=0).enrich(
        [article(f"https://example.com/{index}") for index in range(4)],
        extract_text=True,
    )

    assert peak == 2
