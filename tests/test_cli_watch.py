"""Tests for the watch command in the google-news command-line interface."""

import io
import json
import os
import argparse
from pathlib import Path
from unittest import mock

import pytest

from google_news_api import cli
from google_news_api.monitor import ArticleTracker
from google_news_api.exceptions import GoogleNewsError

# Define some dummy articles
ARTICLES_1 = [
    {
        "title": "Python News",
        "link": "https://news.google.com/rss/articles/python1",
        "published": "2026-07-09",
        "source": "Example",
    },
    {
        "title": "Rust News",
        "link": "https://news.google.com/rss/articles/rust1",
        "published": "2026-07-09",
        "source": "Example",
    },
]

ARTICLES_2 = [
    {
        "title": "Go News",
        "link": "https://news.google.com/rss/articles/go1",
        "published": "2026-07-09",
        "source": "Example",
    },
    # Duplicate from previous poll
    {
        "title": "Python News",
        "link": "https://news.google.com/rss/articles/python1",
        "published": "2026-07-09",
        "source": "Example",
    },
]


class FakeWatchClient:
    instances = []

    def __init__(self, language="en", country="US"):
        self.language = language
        self.country = country
        self.polls = 0
        self.responses = [ARTICLES_1, ARTICLES_2]
        self.errors = []
        FakeWatchClient.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def search(self, query, **kwargs):
        self.polls += 1
        if (
            self.errors
            and len(self.errors) >= self.polls
            and self.errors[self.polls - 1]
        ):
            raise self.errors[self.polls - 1]

        if self.polls <= len(self.responses):
            return self.responses[self.polls - 1]
        return []


def install_fake_watch_client(monkeypatch):
    FakeWatchClient.instances = []
    monkeypatch.setattr(cli, "GoogleNewsClient", FakeWatchClient)


def test_watch_jsonl_output(monkeypatch):
    install_fake_watch_client(monkeypatch)
    output = io.StringIO()
    error = io.StringIO()

    exit_code = cli.main(
        [
            "watch",
            "programming",
            "--once",
            "--emit-existing",  # Emit on first poll
            "--interval",
            "10",
        ],
        output=output,
        error=error,
    )

    assert exit_code == 0, f"Exit code {exit_code}, error: {error.getvalue()}"
    lines = output.getvalue().strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["title"] == "Python News"
    assert json.loads(lines[1])["title"] == "Rust News"


def test_watch_default_no_emit_existing(monkeypatch):
    install_fake_watch_client(monkeypatch)
    output = io.StringIO()

    exit_code = cli.main(["watch", "programming", "--once"], output=output)

    assert exit_code == 0
    assert output.getvalue() == ""  # Should emit nothing on first poll silently


def test_watch_second_poll_emits_unseen(monkeypatch, tmp_path):
    install_fake_watch_client(monkeypatch)

    # We will raise KeyboardInterrupt on the sleep of the second poll
    def fake_sleep(seconds):
        client = FakeWatchClient.instances[0]
        if client.polls == 2:
            raise KeyboardInterrupt()

    monkeypatch.setattr(cli.time, "sleep", fake_sleep)

    output = io.StringIO()
    state_file = tmp_path / "state.db"

    exit_code = cli.main(
        ["watch", "programming", "--state", str(state_file)], output=output
    )

    assert exit_code == 130  # Exit code for KeyboardInterrupt

    lines = output.getvalue().strip().split("\n")
    assert len(lines) == 1
    # First poll had Python and Rust (emitted nothing because first_poll=True).
    # Second poll had Go and Python. Go is new, Python is duplicate.
    # So it should only emit Go.
    assert json.loads(lines[0])["title"] == "Go News"


def test_watch_failed_poll_does_not_stop_loop(monkeypatch, tmp_path):
    install_fake_watch_client(monkeypatch)

    def fake_sleep(seconds):
        client = FakeWatchClient.instances[0]
        if client.polls == 3:
            raise KeyboardInterrupt()

    monkeypatch.setattr(cli.time, "sleep", fake_sleep)

    output = io.StringIO()
    error = io.StringIO()
    state_file = tmp_path / "state.db"

    # Set up client to fail on the second poll
    client_init_called = False
    original_init = FakeWatchClient.__init__

    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.errors = [None, GoogleNewsError("Network issue"), None]
        # Poll 1: returns ARTICLES_1
        # Poll 2: raises GoogleNewsError
        # Poll 3: returns ARTICLES_2
        # Poll 3's sleep: KeyboardInterrupt
        self.responses = [ARTICLES_1, [], ARTICLES_2]

    monkeypatch.setattr(FakeWatchClient, "__init__", new_init)

    exit_code = cli.main(
        ["watch", "programming", "--state", str(state_file)], output=output, error=error
    )

    assert exit_code == 130
    assert "google-news: poll error: Network issue" in error.getvalue()

    lines = output.getvalue().strip().split("\n")
    assert len(lines) == 1
    assert json.loads(lines[0])["title"] == "Go News"


def test_watch_fingerprint_mismatch_and_reset(monkeypatch, tmp_path):
    install_fake_watch_client(monkeypatch)
    state_file = tmp_path / "state.db"

    # First run to populate state with a different query
    cli.main(["watch", "python", "--once", "--state", str(state_file)])

    # Second run with different query should fail due to mismatch
    error = io.StringIO()
    exit_code = cli.main(
        ["watch", "rust", "--once", "--state", str(state_file)], error=error
    )
    assert exit_code == 1
    assert "Fingerprint mismatch" in error.getvalue()

    # Third run with --reset-state should succeed
    error = io.StringIO()
    exit_code = cli.main(
        ["watch", "rust", "--once", "--reset-state", "--state", str(state_file)],
        error=error,
    )
    assert exit_code == 0


def test_watch_appends_to_output_file(monkeypatch, tmp_path):
    install_fake_watch_client(monkeypatch)
    output_file = tmp_path / "out.jsonl"
    output_file.write_text("existing line\n", encoding="utf-8")

    error = io.StringIO()
    exit_code = cli.main(
        ["watch", "python", "--once", "--emit-existing", "--output", str(output_file)],
        error=error,
    )

    # It should fail because it exists and we didn't provide --force
    assert exit_code == 1
    assert "already exists" in error.getvalue()

    # Now with --force
    exit_code = cli.main(
        [
            "watch",
            "python",
            "--once",
            "--emit-existing",
            "--output",
            str(output_file),
            "--force",
        ]
    )

    assert exit_code == 0
    lines = output_file.read_text(encoding="utf-8").strip().split("\n")
    # With --force it should truncate the file, so only 2 lines
    assert len(lines) == 2
    assert json.loads(lines[0])["title"] == "Python News"
