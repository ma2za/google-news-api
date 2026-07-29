"""Tests for the google-news command-line interface."""

import io
import json

import pytest

from google_news_api import cli
from google_news_api.exceptions import ValidationError

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
        self.batch_search_kwargs = None
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

    def batch_search(self, queries, **kwargs):
        self.batch_queries = queries
        self.batch_search_kwargs = kwargs
        return {query: [dict(ARTICLES[0])] for query in queries}

    def decode_urls(self, urls, **kwargs):
        self.decode_calls.append((urls, kwargs))
        return ["https://example.com/python"]


def install_fake_client(monkeypatch):
    """Install a no-network client test double."""
    FakeClient.instances = []
    monkeypatch.setattr(cli, "GoogleNewsClient", FakeClient)


def test_cli_version_reports_installed_package_version(monkeypatch, capsys):
    """The global version option reports installed distribution metadata."""
    monkeypatch.setattr(cli, "__version__", "1.2.3")

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out == "google-news 1.2.3\n"


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
        "include_domains": None,
        "exclude_domains": None,
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


def test_cli_search_passes_domain_filters(monkeypatch):
    install_fake_client(monkeypatch)

    exit_code = cli.main(
        [
            "search",
            "python",
            "--include-domain",
            "reuters.com",
            "--include-domain",
            "apnews.com",
            "--exclude-domain",
            "youtube.com",
            "--format",
            "json",
        ],
        output=io.StringIO(),
    )

    assert exit_code == 0
    assert FakeClient.instances[0].search_kwargs["include_domains"] == [
        "reuters.com",
        "apnews.com",
    ]
    assert FakeClient.instances[0].search_kwargs["exclude_domains"] == ["youtube.com"]


def test_cli_batch_writes_grouped_json(monkeypatch):
    install_fake_client(monkeypatch)
    output = io.StringIO()

    exit_code = cli.main(
        [
            "batch",
            "python",
            "rust",
            "--include-domain",
            "example.com",
            "--format",
            "json",
        ],
        output=output,
    )

    client = FakeClient.instances[0]
    assert exit_code == 0
    assert client.batch_queries == ["python", "rust"]
    assert client.batch_search_kwargs["include_domains"] == ["example.com"]
    assert list(json.loads(output.getvalue())) == ["python", "rust"]


def test_write_batch_articles_flattens_csv():
    output = io.StringIO()

    cli._write_batch_articles({"python": ARTICLES}, "csv", output)

    rows = output.getvalue().splitlines()
    assert rows[0].startswith("query,title,source,published")
    assert rows[1].startswith("python,Python News,Example,2026-07-09")


def test_write_batch_articles_labels_table_sections():
    output = io.StringIO()

    cli._write_batch_articles({"python": ARTICLES, "rust": ARTICLES}, "table", output)

    assert "QUERY: python" in output.getvalue()
    assert "QUERY: rust" in output.getvalue()


def test_cli_batch_decodes_each_result_group(monkeypatch):
    install_fake_client(monkeypatch)
    output = io.StringIO()

    exit_code = cli.main(
        ["batch", "python", "rust", "--decode-links", "--format", "json"],
        output=output,
    )

    client = FakeClient.instances[0]
    results = json.loads(output.getvalue())
    assert exit_code == 0
    assert len(client.decode_calls) == 2
    assert results["python"][0]["google_link"].startswith("https://news.google.com/")
    assert results["rust"][0]["link"] == "https://example.com/python"


@pytest.mark.parametrize(
    "arguments",
    [
        ["search", "python"],
        ["batch", "python", "rust"],
        ["top"],
    ],
)
def test_cli_commands_write_json_to_output_file(monkeypatch, tmp_path, arguments):
    install_fake_client(monkeypatch)
    output_path = tmp_path / "articles.json"

    exit_code = cli.main([*arguments, "--format", "json", "--output", str(output_path)])

    assert exit_code == 0
    assert output_path.read_text(encoding="utf-8").endswith("\n")
    assert json.loads(output_path.read_text(encoding="utf-8"))


def test_cli_output_dash_preserves_stdout_behavior(monkeypatch):
    install_fake_client(monkeypatch)
    output = io.StringIO()

    exit_code = cli.main(
        ["search", "python", "--format", "json", "--output", "-"],
        output=output,
    )

    assert exit_code == 0
    assert json.loads(output.getvalue()) == ARTICLES


def test_cli_refuses_to_overwrite_existing_output(monkeypatch, tmp_path):
    install_fake_client(monkeypatch)
    output_path = tmp_path / "articles.json"
    output_path.write_text("keep me", encoding="utf-8")
    error = io.StringIO()

    exit_code = cli.main(
        ["search", "python", "--output", str(output_path)],
        error=error,
    )

    assert exit_code == 1
    assert output_path.read_text(encoding="utf-8") == "keep me"
    assert (
        error.getvalue() == f"google-news: output file already exists: {output_path}\n"
    )
    assert FakeClient.instances == []


def test_cli_force_replaces_existing_output(monkeypatch, tmp_path):
    install_fake_client(monkeypatch)
    output_path = tmp_path / "articles.json"
    output_path.write_text("old content", encoding="utf-8")

    exit_code = cli.main(
        [
            "search",
            "python",
            "--format",
            "json",
            "--output",
            str(output_path),
            "--force",
        ]
    )

    assert exit_code == 0
    assert json.loads(output_path.read_text(encoding="utf-8")) == ARTICLES
    assert not list(tmp_path.glob(".articles.json.*"))


def test_cli_force_failure_preserves_existing_output(monkeypatch, tmp_path):
    install_fake_client(monkeypatch)
    output_path = tmp_path / "articles.json"
    output_path.write_text("old content", encoding="utf-8")
    error = io.StringIO()

    def fail_replace(_source, _destination):
        raise OSError("replace failed")

    monkeypatch.setattr(cli.os, "replace", fail_replace)

    exit_code = cli.main(
        [
            "search",
            "python",
            "--output",
            str(output_path),
            "--force",
        ],
        error=error,
    )

    assert exit_code == 1
    assert output_path.read_text(encoding="utf-8") == "old content"
    assert not list(tmp_path.glob(".articles.json.*"))
    assert error.getvalue() == "google-news: replace failed\n"


def test_cli_failed_command_does_not_create_output(monkeypatch, tmp_path):
    output_path = tmp_path / "articles.json"
    error = io.StringIO()

    def fail(_args, _output):
        raise ValidationError("invalid query")

    monkeypatch.setattr(cli, "_run", fail)

    exit_code = cli.main(
        ["search", "python", "--output", str(output_path)],
        error=error,
    )

    assert exit_code == 1
    assert not output_path.exists()
    assert error.getvalue() == "google-news: invalid query\n"


def test_cli_output_file_uses_utf8_and_valid_csv(monkeypatch, tmp_path):
    install_fake_client(monkeypatch)
    output_path = tmp_path / "articles.csv"
    monkeypatch.setitem(ARTICLES[0], "title", "Știri Python")

    exit_code = cli.main(
        [
            "search",
            "python",
            "--format",
            "csv",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    content = output_path.read_bytes()
    assert "Știri Python".encode() in content
    assert b"\r\r\n" not in content


def test_cli_output_reports_filesystem_error(monkeypatch, tmp_path):
    install_fake_client(monkeypatch)
    output_path = tmp_path / "missing" / "articles.json"
    error = io.StringIO()

    exit_code = cli.main(
        ["search", "python", "--output", str(output_path)],
        error=error,
    )

    assert exit_code == 1
    assert not output_path.exists()
    assert error.getvalue().startswith("google-news: ")
