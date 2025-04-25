"""Tests for the Google News client."""

from datetime import datetime, timedelta

import pytest

from google_news_api.client import GoogleNewsClient


def test_client_initialization():
    """Test that the client initializes with default values."""
    client = GoogleNewsClient()
    assert client.language == "en"
    assert client.country == "US"


def test_client_custom_initialization():
    """Test that the client initializes with custom values."""
    client = GoogleNewsClient(language="es", country="ES")
    assert client.language == "es"
    assert client.country == "ES"


@pytest.mark.asyncio
async def test_get_top_news():
    """Test getting top news articles."""
    async with GoogleNewsClient() as client:
        news = await client.get_top_news(max_results=5)
        assert isinstance(news, list)
        assert len(news) <= 5
        if news:
            assert all(isinstance(article, dict) for article in news)
            assert all("title" in article for article in news)
            assert all("link" in article for article in news)
            assert all("source" in article for article in news)


@pytest.mark.asyncio
async def test_get_topic_news():
    """Test getting topic-specific news."""
    async with GoogleNewsClient() as client:
        news = await client.get_topic_news("TECHNOLOGY", max_results=5)
        assert isinstance(news, list)
        assert len(news) <= 5
        if news:
            assert all(isinstance(article, dict) for article in news)
            assert all("title" in article for article in news)
            assert all("link" in article for article in news)
            assert all("source" in article for article in news)


@pytest.mark.asyncio
async def test_search():
    """Test searching for news articles."""
    async with GoogleNewsClient() as client:
        news = await client.search("python programming", max_results=5)
        assert isinstance(news, list)
        assert len(news) <= 5
        if news:
            assert all(isinstance(article, dict) for article in news)
            assert all("title" in article for article in news)
            assert all("link" in article for article in news)
            assert all("source" in article for article in news)


@pytest.mark.asyncio
async def test_search_with_dates():
    """Test searching with date parameters."""
    async with GoogleNewsClient() as client:
        from_date = datetime.now() - timedelta(days=7)
        to_date = datetime.now()
        news = await client.search(
            "python programming", max_results=5, from_date=from_date, to_date=to_date
        )
        assert isinstance(news, list)
        assert len(news) <= 5


@pytest.mark.asyncio
async def test_get_sources():
    """Test getting news sources."""
    async with GoogleNewsClient() as client:
        sources = await client.get_sources()
        assert isinstance(sources, list)
        if sources:
            assert all(isinstance(source, dict) for source in sources)
            assert all("name" in source for source in sources)
            assert all("url" in source for source in sources)
            assert all("language" in source for source in sources)
            assert all("country" in source for source in sources)
