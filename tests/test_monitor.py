import json
import os
import tempfile
from unittest import mock

import pytest

from google_news_api.monitor import ArticleTracker


@pytest.fixture
def temp_state_path():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    os.unlink(path)
    yield path
    if os.path.exists(path):
        os.unlink(path)


def test_first_run_seed_silent(temp_state_path):
    tracker = ArticleTracker(temp_state_path)
    articles = [{"id": "1"}, {"id": "2"}]

    new_articles = tracker.filter_new(articles, fingerprint="test1")

    # Should seed silently and return empty
    assert len(new_articles) == 0

    with open(temp_state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    assert state["fingerprint"] == "test1"
    assert state["identities"] == ["id:1", "id:2"]


def test_first_run_emit_existing(temp_state_path):
    tracker = ArticleTracker(temp_state_path)
    articles = [{"id": "1"}, {"id": "2"}]

    new_articles = tracker.filter_new(articles, fingerprint="test1", emit_existing=True)

    assert new_articles == articles

    with open(temp_state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    assert state["identities"] == ["id:1", "id:2"]


def test_second_run_emits_unseen(temp_state_path):
    tracker = ArticleTracker(temp_state_path)
    articles = [{"id": "1"}, {"id": "2"}]
    tracker.filter_new(articles, fingerprint="test1")

    articles_second = [{"id": "2"}, {"id": "3"}]
    new_articles = tracker.filter_new(articles_second, fingerprint="test1")

    assert new_articles == [{"id": "3"}]

    with open(temp_state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    assert state["identities"] == ["id:1", "id:2", "id:3"]


def test_identity_fallback(temp_state_path):
    tracker = ArticleTracker(temp_state_path)
    articles = [
        {"id": "1"},  # id
        {
            "link": "http://decoded",
            "google_link": "http://orig",
        },  # Enriched (link=decoded, google_link=original) -> Uses decoded link
        {"link": "http://onlyorig"},  # Only original link
        {"title": "  SOME Title  ", "published": "today"},  # title fallback
        {"title": "No Published"},  # title fallback no published
        {},  # Cannot identify
    ]

    new_articles = tracker.filter_new(
        articles, fingerprint="identities", emit_existing=True
    )
    assert len(new_articles) == 6

    with open(temp_state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    assert state["identities"] == [
        "id:1",
        "link:http://decoded",
        "link:http://onlyorig",
        "title:some title:today",
        "title:no published:",
    ]


def test_bounded_state_eviction(temp_state_path):
    tracker = ArticleTracker(temp_state_path, max_seen=3)
    articles = [{"id": str(i)} for i in range(1, 6)]

    tracker.filter_new(articles, fingerprint="test_evict", emit_existing=True)

    with open(temp_state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    # Should only keep the last 3 items: "id:3", "id:4", "id:5"
    assert state["identities"] == ["id:3", "id:4", "id:5"]

    # If we filter again, "id:1" is not in the seen set anymore,
    # so it should be emitted as new!
    new_articles = tracker.filter_new(
        [{"id": "1"}, {"id": "4"}, {"id": "6"}], fingerprint="test_evict"
    )
    assert new_articles == [{"id": "1"}, {"id": "6"}]

    with open(temp_state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    assert (
        state["identities"] == ["id:4", "id:5", "id:1", "id:6"][-3:]
    )  # ["id:5", "id:1", "id:6"]


def test_fingerprint_mismatch(temp_state_path):
    tracker = ArticleTracker(temp_state_path)
    tracker.filter_new([{"id": "1"}], fingerprint="test1")

    with pytest.raises(ValueError, match="Fingerprint mismatch"):
        tracker.filter_new([{"id": "2"}], fingerprint="test2")


def test_atomic_state_write_failure(temp_state_path):
    tracker = ArticleTracker(temp_state_path)
    tracker.filter_new([{"id": "1"}], fingerprint="test1")

    with open(temp_state_path, "r", encoding="utf-8") as f:
        original_state = f.read()

    with mock.patch("os.replace", side_effect=OSError("Disk full")):
        with pytest.raises(OSError, match="Disk full"):
            tracker.filter_new([{"id": "2"}], fingerprint="test1")

    # The state should remain readable and unchanged
    with open(temp_state_path, "r", encoding="utf-8") as f:
        failed_state = f.read()

    assert original_state == failed_state
