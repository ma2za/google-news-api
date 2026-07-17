import sys
from types import SimpleNamespace

import pytest

from google_news_api import mcp_server


class FakeResponse:
    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def text(self):
        return "<html>article</html>"


class FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def get(self, url):
        return FakeResponse()


class FakeClient:
    def __init__(self, decoded_urls=None):
        self.decoded_urls = decoded_urls or []
        self.decode_calls = []
        self.search_kwargs = None
        self.batch_search_kwargs = None
        self.top_news_kwargs = None

    async def decode_urls(self, urls, **kwargs):
        self.decode_calls.append((urls, kwargs))
        return self.decoded_urls

    async def search(self, **kwargs):
        self.search_kwargs = kwargs
        return [
            {
                "title": "Search",
                "link": "https://news.google.com/rss/articles/search",
                "published": "2026-01-01",
                "summary": "",
                "source": "Example",
            }
        ]

    async def top_news(self, **kwargs):
        self.top_news_kwargs = kwargs
        return [
            {
                "title": "Top",
                "link": "https://news.google.com/rss/articles/top",
                "published": "2026-01-01",
                "summary": "",
                "source": "Example",
            }
        ]

    async def batch_search(self, **kwargs):
        self.batch_search_kwargs = kwargs
        return {
            query: [
                {
                    "title": query,
                    "link": f"https://news.google.com/rss/articles/{query}",
                    "published": "2026-01-01",
                    "summary": "",
                    "source": "Example",
                }
            ]
            for query in kwargs["queries"]
        }


def install_article_dependency_fakes(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "aiohttp",
        SimpleNamespace(ClientSession=lambda: FakeSession()),
    )
    monkeypatch.setitem(
        sys.modules,
        "trafilatura",
        SimpleNamespace(extract=lambda html: "Article text"),
    )


@pytest.mark.asyncio
async def test_mcp_enrich_defaults_decode_and_extract(monkeypatch):
    install_article_dependency_fakes(monkeypatch)
    client = FakeClient(decoded_urls=["https://example.com/article"])
    articles = [
        {
            "title": "Title",
            "link": "https://news.google.com/rss/articles/id",
            "published": "2026-01-01",
            "summary": "",
            "source": "Example",
        }
    ]

    enriched = await mcp_server._enrich_articles(client, articles)

    assert client.decode_calls[0][0] == ["https://news.google.com/rss/articles/id"]
    assert enriched == [
        {
            "title": "Title",
            "link": "https://example.com/article",
            "google_link": "https://news.google.com/rss/articles/id",
            "published": "2026-01-01",
            "summary": "",
            "source": "Example",
            "text": "Article text",
        }
    ]


@pytest.mark.asyncio
async def test_mcp_enrich_can_skip_decode_and_extract():
    client = FakeClient()
    articles = [
        {
            "title": "Title",
            "link": "https://news.google.com/rss/articles/id",
            "published": "2026-01-01",
            "summary": "",
            "source": "Example",
        }
    ]

    enriched = await mcp_server._enrich_articles(
        client,
        articles,
        decode_links=False,
        extract_text=True,
    )

    assert client.decode_calls == []
    assert enriched == articles


@pytest.mark.asyncio
async def test_mcp_enrich_can_decode_without_extracting_text():
    client = FakeClient(decoded_urls=["https://example.com/article"])
    articles = [
        {
            "title": "Title",
            "link": "https://news.google.com/rss/articles/id",
            "published": "2026-01-01",
            "summary": "",
            "source": "Example",
        }
    ]

    enriched = await mcp_server._enrich_articles(
        client,
        articles,
        decode_links=True,
        extract_text=False,
    )

    assert enriched == [
        {
            "title": "Title",
            "link": "https://example.com/article",
            "google_link": "https://news.google.com/rss/articles/id",
            "published": "2026-01-01",
            "summary": "",
            "source": "Example",
        }
    ]


@pytest.mark.asyncio
async def test_mcp_enrich_failed_decode_keeps_article_unchanged(monkeypatch):
    install_article_dependency_fakes(monkeypatch)
    client = FakeClient(decoded_urls=[None])
    articles = [
        {
            "title": "Title",
            "link": "https://news.google.com/rss/articles/id",
            "published": "2026-01-01",
            "summary": "",
            "source": "Example",
        }
    ]

    enriched = await mcp_server._enrich_articles(client, articles)

    assert enriched == articles


@pytest.mark.asyncio
async def test_mcp_news_search_passes_mode(monkeypatch):
    client = FakeClient()

    async def get_client(language="en", country="US"):
        return client

    monkeypatch.setattr(mcp_server, "get_client", get_client)

    result = await mcp_server.news_search(
        "python",
        max_results=3,
        when="24h",
        decode_links=False,
        extract_text=False,
        mode="searchapi_light",
    )

    assert result[0]["title"] == "Search"
    assert client.search_kwargs["query"] == "python"
    assert client.search_kwargs["max_results"] == 3
    assert client.search_kwargs["when"] == "24h"
    assert client.search_kwargs["mode"] == "searchapi_light"


@pytest.mark.asyncio
async def test_mcp_batch_search_passes_domain_filters(monkeypatch):
    client = FakeClient()

    async def get_client(language="en", country="US"):
        return client

    monkeypatch.setattr(mcp_server, "get_client", get_client)

    result = await mcp_server.batch_news_search(
        ["python", "rust"],
        include_domains=["example.com"],
        exclude_domains=["youtube.com"],
        decode_links=False,
        extract_text=False,
    )

    assert list(result) == ["python", "rust"]
    assert client.batch_search_kwargs["include_domains"] == ["example.com"]
    assert client.batch_search_kwargs["exclude_domains"] == ["youtube.com"]


def test_mcp_app_registers_batch_search(monkeypatch):
    registered = []

    class FakeMCP:
        def __init__(self, name):
            self.name = name

        def tool(self):
            def register(function):
                registered.append(function.__name__)
                return function

            return register

    monkeypatch.setattr(mcp_server, "_load_fastmcp", lambda: FakeMCP)

    app = mcp_server.create_mcp_app()

    assert app.name == "googlenews"
    assert registered == ["news_search", "batch_news_search", "top_news"]


@pytest.mark.asyncio
async def test_mcp_top_news_passes_mode(monkeypatch):
    client = FakeClient()

    async def get_client(language="en", country="US"):
        return client

    monkeypatch.setattr(mcp_server, "get_client", get_client)

    result = await mcp_server.top_news(
        topic="TECHNOLOGY",
        max_results=2,
        decode_links=False,
        extract_text=False,
        mode="searchapi_portal",
    )

    assert result[0]["title"] == "Top"
    assert client.top_news_kwargs["topic"] == "TECHNOLOGY"
    assert client.top_news_kwargs["max_results"] == 2
    assert client.top_news_kwargs["mode"] == "searchapi_portal"


def test_mcp_server_entrypoint_reports_missing_extra(monkeypatch, capsys):
    def missing_dependencies():
        raise RuntimeError(mcp_server.MCP_EXTRA_INSTALL_MESSAGE)

    monkeypatch.setattr(mcp_server, "_load_article_dependencies", missing_dependencies)

    with pytest.raises(SystemExit) as exc_info:
        mcp_server.main()

    assert exc_info.value.code == 1
    assert 'pip install "google-news-api[mcp]"' in capsys.readouterr().err
