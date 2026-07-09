"""Tests for the google-news command-line interface."""

import io
import json

from google_news_api import cli

ARTICLES = [
    {
        "title": "Python News",
        "link": "https://news.google.com/rss/articles/python",
        "published": "2026-07-09",
        "summary": "Python summary",
        "source": "Example",
        "id": "python-id",
    }
]


class FakeClient:
    instances = []

    def __init__(self, language="en", country="US"):
        self.language = language
        self.country = country
        self.search_kwargs = None
        self.top_news_kwargs = None
        self.decode_calls = []
        FakeClient.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def search(self, query, **kwargs):
        self.search_query = query
        self.search_kwargs = kwargs
        return [dict(article) for article in ARTICLES]

    def top_news(self, **kwargs):
        self.top_news_kwargs = kwargs
        return [dict(article) for article in ARTICLES]

    def decode_urls(self, urls, **kwargs):
        self.decode_calls.append((urls, kwargs))
        return ["https://example.com/python"]


def install_fake_client(monkeypatch):
    """Install a no-network client test double."""
    FakeClient.instances = []
    monkeypatch.setattr(cli, "GoogleNewsClient", FakeClient)


def test_cli_search_writes_json_and_passes_filters(monkeypatch):
    """The search command passes filters through and writes JSON."""
    install_fake_client(monkeypatch)
    output = io.StringIO()

    exit_code = cli.main(
        [
            "search",
            "python",
            "--when",
            "24h",
            "--max-results",
            "5",
            "--mode",
            "searchapi_light",
            "--language",
            "en",
            "--country",
            "GB",
            "--format",
            "json",
        ],
        output=output,
    )

    client = FakeClient.instances[0]
    assert exit_code == 0
    assert client.language == "en"
    assert client.country == "GB"
    assert client.search_query == "python"
    assert client.search_kwargs == {
        "after": None,
        "before": None,
        "when": "24h",
        "max_results": 5,
        "mode": "searchapi_light",
    }
    assert json.loads(output.getvalue()) == ARTICLES


def test_cli_top_writes_csv(monkeypatch):
    """The top command writes CSV output."""
    install_fake_client(monkeypatch)
    output = io.StringIO()

    exit_code = cli.main(
        [
            "top",
            "--topic",
            "TECHNOLOGY",
            "--max-results",
            "1",
            "--format",
            "csv",
        ],
        output=output,
    )

    assert exit_code == 0
    assert FakeClient.instances[0].top_news_kwargs == {
        "topic": "TECHNOLOGY",
        "max_results": 1,
        "mode": "default",
    }
    assert "title,source,published,link,summary,id,google_link" in output.getvalue()
    assert "Python News,Example,2026-07-09" in output.getvalue()


def test_cli_table_output_is_default(monkeypatch):
    """Table output is the default format."""
    install_fake_client(monkeypatch)
    output = io.StringIO()

    exit_code = cli.main(["search", "python"], output=output)

    assert exit_code == 0
    assert "TITLE" in output.getvalue()
    assert "Python News" in output.getvalue()


def test_cli_decode_links_preserves_google_link(monkeypatch):
    """Decoded output keeps the original Google News URL."""
    install_fake_client(monkeypatch)
    output = io.StringIO()

    exit_code = cli.main(
        ["search", "python", "--decode-links", "--format", "json"],
        output=output,
    )

    client = FakeClient.instances[0]
    articles = json.loads(output.getvalue())
    assert exit_code == 0
    assert client.decode_calls == [
        (["https://news.google.com/rss/articles/python"], {"delay": 0})
    ]
    assert articles[0]["link"] == "https://example.com/python"
    assert articles[0]["google_link"] == "https://news.google.com/rss/articles/python"
