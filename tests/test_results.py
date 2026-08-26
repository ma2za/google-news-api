"""Tests for the results normalization and deduplication helpers."""

from datetime import datetime, timezone
import pytest

from google_news_api.exceptions import ValidationError
from google_news_api.results import (
    deduplicate_articles,
    normalize_article,
    normalize_articles,
    parse_published,
    sort_articles,
    source_domain,
)


def test_parse_published_valid_rfc2822():
    dt = parse_published("Wed, 21 Aug 2026 12:34:56 GMT")
    assert dt == datetime(2026, 8, 21, 12, 34, 56, tzinfo=timezone.utc)


def test_parse_published_naive_becomes_utc():
    # email.utils can parse this but might yield naive depending on format.
    # If it's naive, we expect it to be forced to UTC.
    dt = parse_published("21 Aug 2026 12:34:56")
    assert dt is not None
    assert dt.tzinfo == timezone.utc
    assert dt.year == 2026


def test_parse_published_invalid_or_missing():
    assert parse_published(None) is None
    assert parse_published("") is None
    assert parse_published("Not a real date") is None


def test_source_domain_valid_link():
    article = {"link": "https://www.example.com/some/path"}
    assert source_domain(article) == "www.example.com"


def test_source_domain_undecoded_google_link():
    article = {"link": "https://news.google.com/rss/articles/CBMi..."}
    assert source_domain(article) is None


def test_source_domain_invalid_or_missing_link():
    assert source_domain({}) is None
    assert source_domain({"link": None}) is None
    assert source_domain({"link": ""}) is None


def test_deduplicate_articles_by_id():
    articles = [
        {"id": "1", "title": "A"},
        {"id": "2", "title": "B"},
        {"id": "1", "title": "C"},
    ]
    deduped = deduplicate_articles(articles, by="id")
    assert len(deduped) == 2
    assert deduped[0]["title"] == "A"
    assert deduped[1]["title"] == "B"


def test_deduplicate_articles_by_link():
    articles = [
        {"link": "x", "title": "A"},
        {"link": "y", "title": "B"},
        {"link": "x", "title": "C"},
    ]
    deduped = deduplicate_articles(articles, by="link")
    assert len(deduped) == 2
    assert deduped[0]["title"] == "A"
    assert deduped[1]["title"] == "B"


def test_deduplicate_articles_by_title_normalized():
    articles = [
        {"title": "  Same   Title "},
        {"title": "Different Title"},
        {"title": "Same Title"},
    ]
    deduped = deduplicate_articles(articles, by="title")
    assert len(deduped) == 2
    assert deduped[0]["title"] == "  Same   Title "


def test_deduplicate_articles_fallback_chain():
    # Requests dedupe by link, but links are missing.
    # Should fall back to title.
    articles = [
        {"title": "Title A"},
        {"title": "Title A"},
    ]
    deduped = deduplicate_articles(articles, by="link")
    assert len(deduped) == 1


def test_deduplicate_articles_missing_identity():
    # Articles with no id, link, or title should remain distinct
    articles = [
        {"summary": "A"},
        {"summary": "B"},
        {"summary": "C"},
    ]
    deduped = deduplicate_articles(articles)
    assert len(deduped) == 3


def test_deduplicate_articles_invalid_key():
    with pytest.raises(ValidationError):
        deduplicate_articles([], by="summary")


def test_sort_articles():
    articles = [
        {"title": "B", "published": "Wed, 21 Aug 2026 12:00:00 GMT"},
        {"title": "A", "published": "Wed, 21 Aug 2026 13:00:00 GMT"},
        {"title": "C", "published": "Wed, 21 Aug 2026 11:00:00 GMT"},
        {"title": "Undated"},
    ]
    
    # Newest first
    sorted_newest = sort_articles(articles, newest_first=True)
    assert sorted_newest[0]["title"] == "A"
    assert sorted_newest[1]["title"] == "B"
    assert sorted_newest[2]["title"] == "C"
    assert sorted_newest[3]["title"] == "Undated"
    
    # Oldest first
    sorted_oldest = sort_articles(articles, newest_first=False)
    assert sorted_oldest[0]["title"] == "C"
    assert sorted_oldest[1]["title"] == "B"
    assert sorted_oldest[2]["title"] == "A"
    assert sorted_oldest[3]["title"] == "Undated"


def test_normalize_article_immutability():
    original = {
        "title": "A", 
        "published": "Wed, 21 Aug 2026 12:00:00 GMT",
        "link": "https://example.com"
    }
    normalized = normalize_article(original)
    
    assert "published_datetime" in normalized
    assert "source_domain" in normalized
    assert "published_datetime" not in original
    assert "source_domain" not in original


def test_normalize_articles():
    articles = [{"published": "Wed, 21 Aug 2026 12:00:00 GMT"}]
    normalized = normalize_articles(articles)
    assert len(normalized) == 1
    assert "published_datetime" in normalized[0]
