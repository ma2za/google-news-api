"""Tests for public typing exports."""

import google_news_api
from google_news_api import Article, EnrichedArticle


def test_article_types_are_public_exports():
    """Article result types are exported from the package."""
    assert "Article" in google_news_api.__all__
    assert "EnrichedArticle" in google_news_api.__all__
    assert "title" in Article.__annotations__
    assert "google_link" in EnrichedArticle.__annotations__
