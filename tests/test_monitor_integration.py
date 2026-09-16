import pytest
import io
import json
from pathlib import Path
from google_news_api import cli
from google_news_api.client import GoogleNewsClient
from google_news_api.monitor import ArticleTracker


@pytest.mark.integration
def test_live_tracker_deduplication(tmp_path: Path):
    """Test that ArticleTracker correctly identifies and deduplicates real live articles."""
    state_file = tmp_path / "state.json"
    tracker = ArticleTracker(str(state_file), max_seen=100)

    with GoogleNewsClient() as client:
        # Fetch some real articles
        articles = client.search("technology", max_results=10)

        assert len(articles) > 0, "Expected live search to return articles"

        # First run: seed state
        new_articles = tracker.filter_new(
            articles, fingerprint="test-fingerprint", emit_existing=False
        )
        assert (
            len(new_articles) == 0
        ), "First run with emit_existing=False should return nothing"

        assert state_file.exists(), "State file should have been created"

        # Second run: exact same articles
        new_articles_2 = tracker.filter_new(articles, fingerprint="test-fingerprint")
        assert (
            len(new_articles_2) == 0
        ), "Second run with identical live articles should emit nothing"

        # Third run: simulate a new article by mutating an existing one
        mutated_article = articles[0].copy()
        mutated_article["id"] = "fake-live-id-99999"
        mutated_article["link"] = "https://example.com/fake-live-news"
        mutated_article["title"] = "Fake Live Title That Nobody Has Seen"

        new_articles_3 = tracker.filter_new(
            [mutated_article], fingerprint="test-fingerprint"
        )
        assert len(new_articles_3) == 1, "Should emit the new mutated article"
        assert new_articles_3[0]["title"] == "Fake Live Title That Nobody Has Seen"


@pytest.mark.integration
def test_live_cli_watch_deduplication(tmp_path: Path, monkeypatch):
    """Test the CLI watch --once command using live data."""
    state_file = tmp_path / "cli_state.json"

    # Run first poll, emit existing
    output1 = io.StringIO()
    exit_code1 = cli.main(
        [
            "watch",
            "artificial intelligence",
            "--once",
            "--state",
            str(state_file),
            "--emit-existing",
            "--format",
            "jsonl",
            "--max-results",
            "5",
        ],
        output=output1,
    )

    assert exit_code1 == 0
    lines1 = output1.getvalue().strip().split("\n")
    assert len(lines1) > 0
    assert lines1[0] != ""

    # Run second poll immediately, should emit nothing
    output2 = io.StringIO()
    exit_code2 = cli.main(
        [
            "watch",
            "artificial intelligence",
            "--once",
            "--state",
            str(state_file),
            "--format",
            "jsonl",
            "--max-results",
            "5",
        ],
        output=output2,
    )

    assert exit_code2 == 0
    # The output should be completely empty since we just fetched these exact results
    assert output2.getvalue().strip() == ""
