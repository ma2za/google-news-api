"""Tests for the Google News client."""

import asyncio
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone

import dateutil.parser
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
        assert (
            len(news) > 0
        ), "Expected to find top news articles but none were returned"

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
        assert (
            len(news) > 0
        ), "Expected to find technology news articles but none were returned"

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
        assert len(news) > 0, "Expected to find articles but none were returned"

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
        assert len(news) > 0, "Expected to find articles but none were returned"

        # Verify each article has a published date
        for article in news:
            assert "published" in article
            # Could add date parsing validation here if needed


def test_search_with_date_range():
    """Test searching with date range parameters."""
    client = GoogleNewsClient()

    # Test with valid date range
    start_date = "2024-01-01"
    end_date = "2024-03-01"
    news = client.search(
        "Ukraine war", after=start_date, before=end_date, max_results=5
    )
    assert isinstance(news, list)
    assert len(news) <= 5


def test_search_with_date_range_content():
    """Test that articles from date range search fall within the specified range."""
    client = GoogleNewsClient()

    start_date = "2024-01-01"
    end_date = "2024-03-01"
    news = client.search(
        "Ukraine war", after=start_date, before=end_date, max_results=5
    )

    # We expect to find at least one article
    assert len(news) > 0, (
        f"Expected to find articles between {start_date} and {end_date} "
        "but none were returned"
    )

    # Verify articles fall within the date range
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    # Add one day to end_dt to make it inclusive
    end_dt = end_dt + timedelta(days=1)

    for article in news:
        pub_date = dateutil.parser.parse(article["published"])
        # Convert to UTC if timezone is present, otherwise assume UTC
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)
        assert start_dt <= pub_date <= end_dt, (
            f"Article date {pub_date} outside range " f"{start_dt} to {end_dt}"
        )


def test_search_with_date_range_validation():
    """Test date range parameter validation."""
    client = GoogleNewsClient()

    # Test invalid date format
    with pytest.raises(ValidationError) as exc_info:
        client.search("AI technology", after="2024/01/01")
    assert "must be in YYYY-MM-DD format" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        client.search("AI technology", before="24-1-1")
    assert "must be in YYYY-MM-DD format" in str(exc_info.value)


def test_search_with_relative_time():
    """Test searching with relative time parameters."""
    client = GoogleNewsClient()

    # Test valid relative time formats
    for when, _ in [
        ("1h", timedelta(hours=1)),
        ("24h", timedelta(hours=24)),
        ("7d", timedelta(days=7)),
    ]:
        news = client.search("climate change", when=when, max_results=5)
        assert isinstance(news, list)
        assert len(news) <= 5


def test_search_with_relative_time_content():
    """Test that articles from relative time search fall within the specified range."""
    client = GoogleNewsClient()

    # Test valid relative time formats
    for when, delta in [
        ("1h", timedelta(hours=1)),
        ("24h", timedelta(hours=24)),
        ("7d", timedelta(days=7)),
    ]:
        news = client.search("climate change", when=when, max_results=5)

        # We expect to find at least one article for each time range
        assert len(news) > 0, (
            f"Expected to find articles within last {when} " "but none were returned"
        )

        # Verify articles are within the time range
        now = datetime.now(timezone.utc)
        earliest = now - delta
        for article in news:
            pub_date = dateutil.parser.parse(article["published"])
            # Convert to UTC if timezone is present, otherwise assume UTC
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            assert earliest <= pub_date <= now, (
                f"Article date {pub_date} outside range "
                f"{earliest} to {now} for when={when}"
            )


def test_search_with_relative_time_validation():
    """Test relative time parameter validation."""
    client = GoogleNewsClient()

    # Test invalid relative time format
    with pytest.raises(ValidationError) as exc_info:
        client.search("AI technology", when="1x")
    assert "must be in format: <number>[h|d]" in str(exc_info.value)

    # Test hour limit
    with pytest.raises(ValidationError) as exc_info:
        client.search("AI technology", when="102h")
    assert "Hour range must be <= 101" in str(exc_info.value)

    # Test invalid unit
    with pytest.raises(ValidationError) as exc_info:
        client.search("AI technology", when="1m")
    assert "must be in format: <number>[h|d]" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_search_with_time_parameters():
    """Test time-based search parameters with async client."""
    async with AsyncGoogleNewsClient() as client:
        # Test date range
        start_date = "2024-01-01"
        end_date = "2024-03-01"
        news = await client.search(
            "Ukraine war", after=start_date, before=end_date, max_results=5
        )
        assert isinstance(news, list)
        assert len(news) <= 5


@pytest.mark.asyncio
async def test_async_search_with_time_parameters_content():
    """Test content of time-based search results with async client."""
    async with AsyncGoogleNewsClient() as client:
        # Test date range
        start_date = "2024-01-01"
        end_date = "2024-03-01"
        news = await client.search(
            "Ukraine war", after=start_date, before=end_date, max_results=5
        )

        # We expect to find at least one article
        assert len(news) > 0, (
            f"Expected to find articles between {start_date} and {end_date} "
            "but none were returned"
        )

        # Verify articles fall within the date range
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        # Add one day to end_dt to make it inclusive
        end_dt = end_dt + timedelta(days=1)

        for article in news:
            pub_date = dateutil.parser.parse(article["published"])
            # Convert to UTC if timezone is present, otherwise assume UTC
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            assert start_dt <= pub_date <= end_dt, (
                f"Article date {pub_date} outside range " f"{start_dt} to {end_dt}"
            )

        # Test relative time
        when = "24h"
        delta = timedelta(hours=24)
        news = await client.search("climate change", when=when, max_results=5)

        # We expect to find at least one article
        assert len(news) > 0, (
            f"Expected to find articles within last {when} " "but none were returned"
        )

        # Verify articles are within the time range
        now = datetime.now(timezone.utc)
        earliest = now - delta
        for article in news:
            pub_date = dateutil.parser.parse(article["published"])
            # Convert to UTC if timezone is present, otherwise assume UTC
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            assert earliest <= pub_date <= now, (
                f"Article date {pub_date} outside range "
                f"{earliest} to {now} for when={when}"
            )


@pytest.mark.asyncio
async def test_async_search_with_time_parameters_validation():
    """Test validation of time-based search parameters with async client."""
    async with AsyncGoogleNewsClient() as client:
        # Test validation
        with pytest.raises(ValidationError) as exc_info:
            await client.search("AI technology", when="1h", after="2024-01-01")
        assert "Cannot use 'when' parameter together with" in str(exc_info.value)


def test_sync_client_search():
    """Test synchronous client search."""
    client = GoogleNewsClient()
    news = client.search("python programming", max_results=5)
    assert isinstance(news, list)
    assert len(news) <= 5
    assert len(news) > 0, "Expected to find articles but none were returned"

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
    assert len(news) > 0, "Expected to find top news articles but none were returned"

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


def test_batch_search():
    """Test synchronous batch search functionality."""
    client = GoogleNewsClient()
    queries = ["python programming", "artificial intelligence"]

    # Test basic functionality
    results = client.batch_search(queries, max_results=5)
    assert isinstance(results, dict)
    assert set(results.keys()) == set(queries)

    for query, articles in results.items():
        assert isinstance(articles, list)
        assert len(articles) <= 5
        assert len(articles) > 0, f"Expected to find articles for query '{query}'"

        # Verify article structure
        for article in articles:
            assert isinstance(article, dict)
            assert all(
                key in article
                for key in ["title", "link", "published", "source", "summary"]
            )


def test_batch_search_with_time_params():
    """Test synchronous batch search with time parameters."""
    client = GoogleNewsClient()
    queries = ["python programming", "artificial intelligence"]

    # Test with relative time
    results = client.batch_search(queries, when="24h", max_results=5)
    now = datetime.now(timezone.utc)
    earliest = now - timedelta(hours=24)

    for articles in results.values():
        for article in articles:
            pub_date = dateutil.parser.parse(article["published"])
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            assert earliest <= pub_date <= now

    # Test with date range
    start_date = "2024-01-01"
    end_date = "2024-03-01"
    results = client.batch_search(
        queries, after=start_date, before=end_date, max_results=5
    )

    start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    ) + timedelta(days=1)

    for articles in results.values():
        for article in articles:
            pub_date = dateutil.parser.parse(article["published"])
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            assert start_dt <= pub_date <= end_dt


def test_batch_search_validation():
    """Test batch search input validation."""
    client = GoogleNewsClient()

    # Test empty queries list
    assert client.batch_search([]) == {}

    # Test invalid queries parameter type
    with pytest.raises(ValidationError) as exc_info:
        client.batch_search("not a list")
    assert "queries must be a list" in str(exc_info.value)

    # Test invalid date format
    with pytest.raises(ValidationError) as exc_info:
        client.batch_search(["query"], after="2024/01/01")
    assert "must be in YYYY-MM-DD format" in str(exc_info.value)

    # Test invalid when parameter
    with pytest.raises(ValidationError) as exc_info:
        client.batch_search(["query"], when="invalid")
    assert "Time range must be in format" in str(exc_info.value)

    # Test mixing when with date parameters
    with pytest.raises(ValidationError) as exc_info:
        client.batch_search(["query"], when="24h", after="2024-01-01")
    assert "Cannot use 'when' parameter together with" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_batch_search():
    """Test asynchronous batch search functionality."""
    async with AsyncGoogleNewsClient() as client:
        queries = ["python programming", "artificial intelligence"]

        # Test basic functionality
        results = await client.batch_search(queries, max_results=5)
        assert isinstance(results, dict)
        assert set(results.keys()) == set(queries)

        for query, articles in results.items():
            assert isinstance(articles, list)
            assert len(articles) <= 5
            assert len(articles) > 0, f"Expected to find articles for query '{query}'"

            # Verify article structure
            for article in articles:
                assert isinstance(article, dict)
                assert all(
                    key in article
                    for key in ["title", "link", "published", "source", "summary"]
                )


@pytest.mark.asyncio
async def test_async_batch_search_with_time_params():
    """Test asynchronous batch search with time parameters."""
    async with AsyncGoogleNewsClient() as client:
        queries = ["python programming", "artificial intelligence"]

        # Test with relative time
        results = await client.batch_search(queries, when="24h", max_results=5)
        now = datetime.now(timezone.utc)
        earliest = now - timedelta(hours=24)

        for articles in results.values():
            for article in articles:
                pub_date = dateutil.parser.parse(article["published"])
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                assert earliest <= pub_date <= now

        # Test with date range
        start_date = "2024-01-01"
        end_date = "2024-03-01"
        results = await client.batch_search(
            queries, after=start_date, before=end_date, max_results=5
        )

        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        ) + timedelta(days=1)

        for articles in results.values():
            for article in articles:
                pub_date = dateutil.parser.parse(article["published"])
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                assert start_dt <= pub_date <= end_dt


@pytest.mark.asyncio
async def test_async_batch_search_validation():
    """Test asynchronous batch search input validation."""
    async with AsyncGoogleNewsClient() as client:
        # Test empty queries list
        assert await client.batch_search([]) == {}

        # Test invalid queries parameter type
        with pytest.raises(ValidationError) as exc_info:
            await client.batch_search("not a list")
        assert "queries must be a list" in str(exc_info.value)

        # Test invalid date format
        with pytest.raises(ValidationError) as exc_info:
            await client.batch_search(["query"], after="2024/01/01")
        assert "must be in YYYY-MM-DD format" in str(exc_info.value)

        # Test invalid when parameter
        with pytest.raises(ValidationError) as exc_info:
            await client.batch_search(["query"], when="invalid")
        assert "Time range must be in format" in str(exc_info.value)

        # Test mixing when with date parameters
        with pytest.raises(ValidationError) as exc_info:
            await client.batch_search(["query"], when="24h", after="2024-01-01")
        assert "Cannot use 'when' parameter together with" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_batch_search_error_handling():
    """Test error handling in asynchronous batch search."""
    async with AsyncGoogleNewsClient() as client:
        # Test with a mix of valid and invalid queries
        queries = ["valid query", "", "another valid query"]
        results = await client.batch_search(queries, max_results=5)

        # Should still get results for valid queries
        assert "valid query" in results
        assert len(results["valid query"]) > 0
        assert "another valid query" in results
        assert len(results["another valid query"]) > 0

        # Invalid query should return empty list
        assert "" in results
        assert results[""] == []


@pytest.mark.asyncio
async def test_decode_url():
    """Test decoding a single Google News URL."""
    async with AsyncGoogleNewsClient() as client:
        # Test with a valid Google News URL
        article_id = "CBMirgFBVV95cUxQWnRVLVptT01vMkdUWFhfTC1Ia1ROU1JDaE84T2RkRTgwemRFRUQxMkhUSXc1ZHowLWJGRjlaLVp4YmhMZ0FQRUpoU2hiY3dsbDBtMExBRmp6OFRtVHVCeGMwcTFMVlQwV0F6Yy1ILS05eXQ5a2p3ZHJ1NVJqWXlOZHd2TU9wS1lZUk5FS1RMVnhwYXhrNkVVdVFYRUFNVGpfc29qR0FfTXF0eVoyU2c"  # noqa: E501
        google_news_url = f"https://news.google.com/rss/articles/{article_id}"
        decoded_url = await client.decode_url(google_news_url)

        # Verify the decoded URL is different from the original
        assert decoded_url != google_news_url
        # Verify it's a valid URL
        assert decoded_url.startswith(("http://", "https://"))
        # Verify it's not a Google News URL
        assert "news.google.com" not in decoded_url

        # Test with an invalid URL format
        with pytest.raises(ValidationError) as exc_info:
            await client.decode_url("not-a-valid-url")
        assert "URL must be a Google News article URL" in str(exc_info.value)

        # Test with a non-Google News URL
        with pytest.raises(ValidationError) as exc_info:
            await client.decode_url("https://example.com/article")
        assert "URL must be a Google News article URL" in str(exc_info.value)

        # Test with a malformed Google News URL
        with pytest.raises(ValidationError) as exc_info:
            await client.decode_url("https://news.google.com/invalid")
        assert "Invalid Google News URL format" in str(exc_info.value)


@pytest.mark.asyncio
async def test_decode_urls():
    """Test batch decoding of multiple Google News URLs."""
    async with AsyncGoogleNewsClient() as client:
        # Test with multiple valid URLs
        article_ids = [
            "CBMirgFBVV95cUxQWnRVLVptT01vMkdUWFhfTC1Ia1ROU1JDaE84T2RkRTgwemRFRUQxMkhUSXc1ZHowLWJGRjlaLVp4YmhMZ0FQRUpoU2hiY3dsbDBtMExBRmp6OFRtVHVCeGMwcTFMVlQwV0F6Yy1ILS05eXQ5a2p3ZHJ1NVJqWXlOZHd2TU9wS1lZUk5FS1RMVnhwYXhrNkVVdVFYRUFNVGpfc29qR0FfTXF0eVoyU2c",  # noqa: E501
            "CBMiggFBVV95cUxQdGhKdXAtalhPUWRwSTlkSWpHUWVaX0doU2pFMXJBQ2MwSzY5TWw0TkdHcTM3YVU4VGtNWk1faDY3OE5IczJWVXlTbWNwcldsMGlGb3pKbXktMDM0aU0xeVBGZnd6WkxRekhKUExlYmlJMkJ3anBXd25iSThYckEtNEpn",  # noqa: E501
        ]
        urls = [f"https://news.google.com/rss/articles/{id}" for id in article_ids]

        decoded_urls = await client.decode_urls(urls)

        # Verify we got the same number of URLs back
        assert len(decoded_urls) == len(urls)
        # Verify all decoded URLs are different from originals
        assert all(decoded != original for decoded, original in zip(decoded_urls, urls))
        # Verify all decoded URLs are valid
        assert all(url.startswith(("http://", "https://")) for url in decoded_urls)
        # Verify none are Google News URLs
        assert all("news.google.com" not in url for url in decoded_urls)

        # Test with empty list
        assert await client.decode_urls([]) == []

        # Test with invalid input type
        with pytest.raises(ValidationError) as exc_info:
            await client.decode_urls("not-a-list")
        assert "urls must be a list of strings" in str(exc_info.value)

        # Test with mixed valid and invalid URLs
        mixed_article_ids = [
            "CBMirgFBVV95cUxQWnRVLVptT01vMkdUWFhfTC1Ia1ROU1JDaE84T2RkRTgwemRFRUQxMkhUSXc1ZHowLWJGRjlaLVp4YmhMZ0FQRUpoU2hiY3dsbDBtMExBRmp6OFRtVHVCeGMwcTFMVlQwV0F6Yy1ILS05eXQ5a2p3ZHJ1NVJqWXlOZHd2TU9wS1lZUk5FS1RMVnhwYXhrNkVVdVFYRUFNVGpfc29qR0FfTXF0eVoyU2c",  # noqa: E501
            "not-a-valid-url",
            "https://example.com/article",
        ]
        mixed_urls = [
            f"https://news.google.com/rss/articles/{id}" if "CBM" in id else id
            for id in mixed_article_ids
        ]

        # Should process valid URLs and handle invalid ones gracefully
        decoded_mixed = await client.decode_urls(mixed_urls)
        assert len(decoded_mixed) == len(mixed_urls)

        # First URL should be decoded successfully
        assert decoded_mixed[0] != mixed_urls[0]
        assert decoded_mixed[0].startswith(("http://", "https://"))
        assert "news.google.com" not in decoded_mixed[0]

        # Invalid URLs should be logged but not cause the entire batch to fail
        # They should be returned as None or empty string to indicate failure
        assert decoded_mixed[1] is None or decoded_mixed[1] == ""
        assert decoded_mixed[2] is None or decoded_mixed[2] == ""


@pytest.mark.asyncio
async def test_decode_urls_concurrency():
    """Test concurrent URL decoding with different concurrency limits."""
    async with AsyncGoogleNewsClient() as client:
        # Create a list of identical URLs to test concurrency
        article_id = "CBMirgFBVV95cUxQWnRVLVptT01vMkdUWFhfTC1Ia1ROU1JDaE84T2RkRTgwemRFRUQxMkhUSXc1ZHowLWJGRjlaLVp4YmhMZ0FQRUpoU2hiY3dsbDBtMExBRmp6OFRtVHVCeGMwcTFMVlQwV0F6Yy1ILS05eXQ5a2p3ZHJ1NVJqWXlOZHd2TU9wS1lZUk5FS1RMVnhwYXhrNkVVdVFYRUFNVGpfc29qR0FfTXF0eVoyU2c"  # noqa: E501
        base_url = f"https://news.google.com/rss/articles/{article_id}"
        urls = [base_url] * 10  # Test with 10 identical URLs

        # Test with different concurrency limits
        for max_concurrent in [1, 2, 5, 10]:
            start_time = asyncio.get_event_loop().time()
            decoded_urls = await client.decode_urls(urls, max_concurrent=max_concurrent)
            end_time = asyncio.get_event_loop().time()

            # Verify all URLs were decoded
            assert len(decoded_urls) == len(urls)
            assert all(url.startswith(("http://", "https://")) for url in decoded_urls)
            assert all("news.google.com" not in url for url in decoded_urls)

            # Verify all decoded URLs are the same (since input URLs were identical)
            assert len(set(decoded_urls)) == 1

            # Log the time taken for each concurrency level
            print(
                f"Time taken with max_concurrent={max_concurrent}: "
                f"{end_time - start_time:.2f}s"
            )
