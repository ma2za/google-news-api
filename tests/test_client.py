"""Tests for the Google News client."""

import json
import os
import tempfile

import pytest

from google_news_api.client import AsyncGoogleNewsClient, GoogleNewsClient
from google_news_api.exceptions import (
    ConfigurationError,
    HTTPError,
    ParsingError,
    RateLimitError,
    ValidationError,
)
from google_news_api.logging import setup_logging


def test_client_initialization():
    """Test that the client initializes with default values."""
    client = GoogleNewsClient()
    assert client.language_base == "en"
    assert client.language_full == "EN-US"
    assert client.country == "US"


def test_client_custom_initialization():
    """Test that the client initializes with custom values."""
    client = GoogleNewsClient(language="es", country="ES")
    assert client.language_base == "es"
    assert client.language_full == "ES-ES"
    assert client.country == "ES"


def test_client_invalid_language():
    """Test that invalid language raises ConfigurationError."""
    with pytest.raises(ConfigurationError) as exc_info:
        GoogleNewsClient(language="invalid")
    assert "Language must be" in str(exc_info.value)


def test_client_invalid_country():
    """Test that invalid country raises ConfigurationError."""
    with pytest.raises(ConfigurationError) as exc_info:
        GoogleNewsClient(language="en", country="INVALID")
    assert "Country must be" in str(exc_info.value)


def test_client_language_country_format():
    """Test language-country format initialization."""
    client = GoogleNewsClient(language="en-GB", country="GB")
    assert client.language_base == "en"
    assert client.language_full == "EN-GB"
    assert client.country == "GB"


def test_client_empty_query():
    """Test that empty search query raises ValidationError."""
    client = GoogleNewsClient()
    with pytest.raises(ValidationError) as exc_info:
        client.search("")
    assert "Query must be" in str(exc_info.value)


def test_client_invalid_topic():
    """Test that invalid topic raises ValidationError."""
    client = GoogleNewsClient()
    with pytest.raises(ValidationError) as exc_info:
        client.top_news("INVALID_TOPIC")
    assert "Invalid topic" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_top_news():
    """Test getting top news articles."""
    async with AsyncGoogleNewsClient() as client:
        news = await client.top_news(max_results=5)
        assert isinstance(news, list)
        assert len(news) <= 5
        if news:
            assert all(isinstance(article, dict) for article in news)
            assert all("title" in article for article in news)
            assert all("link" in article for article in news)
            assert all("source" in article for article in news)
            assert all("published" in article for article in news)
            assert all("summary" in article for article in news)


@pytest.mark.asyncio
async def test_get_topic_news():
    """Test getting topic-specific news."""
    async with AsyncGoogleNewsClient() as client:
        news = await client.top_news("TECHNOLOGY", max_results=5)
        assert isinstance(news, list)
        assert len(news) <= 5
        if news:
            assert all(isinstance(article, dict) for article in news)
            assert all("title" in article for article in news)
            assert all("link" in article for article in news)
            assert all("source" in article for article in news)
            assert all("published" in article for article in news)
            assert all("summary" in article for article in news)


@pytest.mark.asyncio
async def test_search():
    """Test searching for news articles."""
    async with AsyncGoogleNewsClient() as client:
        news = await client.search("python programming", max_results=5)
        assert isinstance(news, list)
        assert len(news) <= 5
        if news:
            assert all(isinstance(article, dict) for article in news)
            assert all("title" in article for article in news)
            assert all("link" in article for article in news)
            assert all("source" in article for article in news)
            assert all("published" in article for article in news)
            assert all("summary" in article for article in news)


@pytest.mark.asyncio
async def test_search_with_dates():
    """Test searching with dates."""
    async with AsyncGoogleNewsClient() as client:
        news = await client.search("python programming", max_results=5)
        assert isinstance(news, list)
        assert len(news) <= 5
        if news:
            # Verify each article has a published date
            for article in news:
                assert "published" in article
                # Could add date parsing validation here if needed


def test_sync_client_search():
    """Test synchronous client search."""
    client = GoogleNewsClient()
    news = client.search("python programming", max_results=5)
    assert isinstance(news, list)
    assert len(news) <= 5
    if news:
        assert all(isinstance(article, dict) for article in news)
        assert all("title" in article for article in news)
        assert all("link" in article for article in news)
        assert all("source" in article for article in news)
        assert all("published" in article for article in news)
        assert all("summary" in article for article in news)


def test_sync_client_top_news():
    """Test synchronous client top news."""
    client = GoogleNewsClient()
    news = client.top_news(max_results=5)
    assert isinstance(news, list)
    assert len(news) <= 5
    if news:
        assert all(isinstance(article, dict) for article in news)
        assert all("title" in article for article in news)
        assert all("link" in article for article in news)
        assert all("source" in article for article in news)
        assert all("published" in article for article in news)
        assert all("summary" in article for article in news)


def test_client_cleanup():
    """Test that client cleanup works properly."""
    client = GoogleNewsClient()
    del client  # Should close the client without errors


@pytest.mark.asyncio
async def test_async_client_cleanup():
    """Test that async client cleanup works properly."""
    client = AsyncGoogleNewsClient()
    await client.aclose()  # Should close without errors


def test_max_results_validation():
    """Test that max_results is properly handled."""
    client = GoogleNewsClient()

    # Test with zero
    news = client.top_news(max_results=0)
    assert isinstance(news, list)
    assert len(news) == 0

    # Test with negative number (should be treated as None)
    news = client.top_news(max_results=-1)
    assert isinstance(news, list)

    # Test with None
    news = client.top_news(max_results=None)
    assert isinstance(news, list)


def test_logging_setup():
    """Test that logging setup works properly."""
    import json
    import logging
    import os
    import tempfile

    from google_news_api.logging import setup_logging

    # Test structured logging
    setup_logging(level="DEBUG", structured=True)
    logger = logging.getLogger("google_news_api")

    # Create temp file and ensure it's closed after use
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp_name = tmp.name
    tmp.close()

    try:
        # Add file handler
        setup_logging(level="DEBUG", structured=True, log_file=tmp_name)

        # Test logging
        logger.info("Test message", extra={"test_prop": "test_value"})

        # Read log file
        with open(tmp_name, "r") as f:
            log_line = f.readline().strip()

        # Parse JSON log
        log_data = json.loads(log_line)
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["test_prop"] == "test_value"
    finally:
        # Remove all handlers to release file
        logger.handlers = []
        # Cleanup
        os.unlink(tmp_name)

    # Test non-structured logging
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp_name = tmp.name
    tmp.close()

    try:
        setup_logging(level="DEBUG", structured=False, log_file=tmp_name)
        logger.info("Test message")

        with open(tmp_name, "r") as f:
            log_line = f.readline().strip()

        assert "INFO" in log_line
        assert "Test message" in log_line
    finally:
        # Remove all handlers to release file
        logger.handlers = []
        # Cleanup
        os.unlink(tmp_name)


@pytest.mark.asyncio
async def test_rate_limiter_logging():
    """Test that rate limiter logs warnings when limit is reached."""
    import logging

    from google_news_api.utils import AsyncRateLimiter

    # Setup logging to capture warnings
    logger = logging.getLogger("google_news_api")

    # Create temp file and ensure it's closed after use
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp_name = tmp.name
    tmp.close()

    try:
        setup_logging(level="WARNING", structured=True, log_file=tmp_name)

        # Create rate limiter with very low limit
        limiter = AsyncRateLimiter(requests_per_minute=1)

        # First request should work
        async with limiter:
            pass

        # Second immediate request should fail and log warning
        try:
            async with limiter:
                pytest.fail("Should have raised RateLimitError")
        except RateLimitError:
            pass

        # Check log file
        with open(tmp_name, "r") as f:
            log_line = f.readline().strip()

        log_data = json.loads(log_line)
        assert log_data["level"] == "WARNING"
        assert "Rate limit reached" in log_data["message"]
    finally:
        # Remove all handlers to release file
        logger.handlers = []
        # Cleanup
        os.unlink(tmp_name)


def test_log_with_props():
    """Test the log_with_props decorator."""
    import json
    import tempfile

    from google_news_api.logging import log_with_props, logger

    @log_with_props(operation="test", component="decorator")
    def test_function():
        logger.info("Test message")

    # Create temp file and ensure it's closed after use
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp_name = tmp.name
    tmp.close()

    try:
        # Setup logging to capture decorated logs
        setup_logging(level="INFO", structured=True, log_file=tmp_name)

        # Call decorated function
        test_function()

        # Check log file
        with open(tmp_name, "r") as f:
            log_line = f.readline().strip()

        log_data = json.loads(log_line)
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["operation"] == "test"
        assert log_data["component"] == "decorator"
    finally:
        # Remove all handlers to release file
        logger.handlers = []
        # Cleanup
        os.unlink(tmp_name)


def test_chrome_headers():
    """Test that Chrome headers are properly generated."""
    from google_news_api.client import CHROME_HEADERS, _generate_chrome_version

    # Test version generation
    version = _generate_chrome_version()
    assert version.startswith("122.0.")
    parts = version.split(".")
    assert len(parts) == 4
    assert 0 <= int(parts[2]) <= 5000
    assert 0 <= int(parts[3]) <= 300

    # Test headers
    assert "User-Agent" in CHROME_HEADERS
    assert "Chrome" in CHROME_HEADERS["User-Agent"]
    assert "Mozilla/5.0" in CHROME_HEADERS["User-Agent"]
    assert "Accept" in CHROME_HEADERS
    assert "Accept-Language" in CHROME_HEADERS
    assert "Accept-Encoding" in CHROME_HEADERS


def test_cache_operations():
    """Test cache operations in detail."""
    import time

    from google_news_api.utils import Cache

    # Test initialization with invalid TTL
    with pytest.raises(ValueError):
        Cache(ttl=0)

    # Test basic operations
    cache = Cache(ttl=1)  # 1 second TTL

    # Test set and get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    # Test expiration
    time.sleep(1.1)  # Wait for TTL to expire
    assert cache.get("key1") is None

    # Test clear
    cache.set("key2", "value2")
    cache.clear()
    assert cache.get("key2") is None


@pytest.mark.asyncio
async def test_async_cache_operations():
    """Test async cache operations."""
    import asyncio

    from google_news_api.utils import AsyncCache

    # Test initialization with invalid TTL
    with pytest.raises(ValueError):
        AsyncCache(ttl=0)

    # Test basic operations
    cache = AsyncCache(ttl=1)  # 1 second TTL

    # Test set and get
    await cache.set("key1", "value1")
    assert await cache.get("key1") == "value1"

    # Test expiration
    await asyncio.sleep(1.1)  # Wait for TTL to expire
    assert await cache.get("key1") is None

    # Test clear
    await cache.set("key2", "value2")
    await cache.clear()
    assert await cache.get("key2") is None


def test_retry_sync_validation():
    """Test retry decorator validation."""
    from google_news_api.utils import retry_sync

    # Test invalid max_retries
    with pytest.raises(ValueError):

        @retry_sync(max_retries=0)
        def test_func1():
            pass

    # Test invalid backoff
    with pytest.raises(ValueError):

        @retry_sync(backoff=0)
        def test_func2():
            pass


@pytest.mark.asyncio
async def test_retry_async_validation():
    """Test async retry decorator validation."""
    from google_news_api.utils import retry_async

    # Test invalid max_retries
    with pytest.raises(ValueError):

        @retry_async(max_retries=0)
        async def test_func1():
            pass

    # Test invalid backoff
    with pytest.raises(ValueError):

        @retry_async(backoff=0)
        async def test_func2():
            pass


def test_client_url_building():
    """Test URL building for different scenarios."""
    client = GoogleNewsClient()

    # Test search URL
    search_url = client._build_url("search?q=test")
    assert "q=test" in search_url
    assert "hl=EN-US" in search_url
    assert "gl=US" in search_url

    # Test empty path (default to WORLD)
    default_url = client._build_url("")
    assert "topic/WORLD" in default_url

    # Test topic path
    topic_url = client._build_url("topic/TECHNOLOGY")
    assert "topic/TECHNOLOGY" in topic_url

    # Test custom path
    custom_url = client._build_url("custom/path")
    assert "custom/path" in custom_url
    assert "hl=EN-US" in custom_url
    assert "gl=US" in custom_url


def test_client_error_handling():
    """Test error handling in the client."""
    import httpx

    client = GoogleNewsClient()

    # Test request error
    with pytest.raises(HTTPError) as exc_info:
        response = httpx.Response(
            404, request=httpx.Request("GET", "http://example.com")
        )
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(client._client, "get", lambda _: response)
            client.search("test")
    assert "HTTP 404" in str(exc_info.value)

    # Test parsing error
    with pytest.raises(ParsingError) as exc_info:
        response = httpx.Response(
            200, request=httpx.Request("GET", "http://example.com")
        )
        response._content = b"invalid feed content"
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(client._client, "get", lambda _: response)
            client.search("test")
    assert "Failed to parse feed" in str(exc_info.value)

    # Test request network error
    with pytest.raises(HTTPError) as exc_info:
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                client._client,
                "get",
                lambda _: (_ for _ in ()).throw(httpx.RequestError("Network error")),
            )
            client.search("test")
    assert "Request failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_client_error_handling():
    """Test error handling in the async client."""
    import httpx

    async with AsyncGoogleNewsClient() as client:
        # Test request error
        with pytest.raises(HTTPError) as exc_info:
            response = httpx.Response(
                404, request=httpx.Request("GET", "http://example.com")
            )

            async def mock_get(_):
                return response

            with pytest.MonkeyPatch.context() as mp:
                mp.setattr(client.client, "get", mock_get)
                await client.search("test")
        assert "HTTP 404" in str(exc_info.value)

        # Test parsing error
        with pytest.raises(ParsingError) as exc_info:
            response = httpx.Response(
                200, request=httpx.Request("GET", "http://example.com")
            )
            response._content = b"invalid feed content"

            async def mock_get(_):
                return response

            with pytest.MonkeyPatch.context() as mp:
                mp.setattr(client.client, "get", mock_get)
                await client.search("test")
        assert "Failed to parse feed" in str(exc_info.value)

        # Test request network error
        with pytest.raises(HTTPError) as exc_info:

            async def mock_get(_):
                raise httpx.RequestError("Network error")

            with pytest.MonkeyPatch.context() as mp:
                mp.setattr(client.client, "get", mock_get)
                await client.search("test")
        assert "Request failed" in str(exc_info.value)


def test_parse_articles():
    """Test article parsing with different inputs."""
    from feedparser import FeedParserDict

    client = GoogleNewsClient()

    # Test empty feed
    feed = FeedParserDict()
    feed.entries = []
    articles = client._parse_articles(feed)
    assert len(articles) == 0

    # Test feed with max_results=0
    feed = FeedParserDict()
    feed.entries = [{"title": "Test"}]
    articles = client._parse_articles(feed, max_results=0)
    assert len(articles) == 0

    # Test feed with missing optional fields
    feed = FeedParserDict()
    entry = FeedParserDict()
    entry.title = "Test"
    entry.link = "http://test.com"
    entry.published = "2024-01-01"
    entry.summary = ""
    feed.entries = [entry]
    articles = client._parse_articles(feed)
    assert len(articles) == 1
    assert articles[0]["title"] == "Test"
    assert articles[0]["link"] == "http://test.com"
    assert articles[0]["published"] == "2024-01-01"
    assert articles[0]["summary"] == ""
    assert articles[0]["source"] is None
