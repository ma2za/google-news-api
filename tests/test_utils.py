"""Tests for the utility functions and classes."""

import asyncio
import time

import pytest

from google_news_api.exceptions import RateLimitError
from google_news_api.utils import (
    AsyncCache,
    AsyncRateLimiter,
    Cache,
    RateLimiter,
    retry_async,
    retry_sync,
)


def test_sync_cache():
    """Test synchronous cache functionality."""
    cache = Cache(ttl=1)  # 1 second TTL

    # Test setting and getting
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    # Test TTL
    time.sleep(1.1)  # Wait for TTL to expire
    assert cache.get("key1") is None

    # Test overwriting
    cache.set("key2", "value2")
    cache.set("key2", "new_value2")
    assert cache.get("key2") == "new_value2"


@pytest.mark.asyncio
async def test_async_cache():
    """Test asynchronous cache functionality."""
    cache = AsyncCache(ttl=1)  # 1 second TTL

    # Test setting and getting
    await cache.set("key1", "value1")
    assert await cache.get("key1") == "value1"

    # Test TTL
    await asyncio.sleep(1.1)  # Wait for TTL to expire
    assert await cache.get("key1") is None

    # Test overwriting
    await cache.set("key2", "value2")
    await cache.set("key2", "new_value2")
    assert await cache.get("key2") == "new_value2"


def test_sync_rate_limiter():
    """Test synchronous rate limiter functionality."""
    limiter = RateLimiter(requests_per_minute=60)

    start_time = time.time()
    with limiter:
        pass  # First request should be immediate
    elapsed = time.time() - start_time
    assert elapsed < 0.1  # Should be near-instant

    # Test rapid requests
    for _ in range(3):
        with limiter:
            pass

    # Test rate limit error
    with pytest.raises(RateLimitError):
        for _ in range(61):  # Exceed rate limit
            with limiter:
                pass


@pytest.mark.asyncio
async def test_async_rate_limiter():
    """Test asynchronous rate limiter functionality."""
    limiter = AsyncRateLimiter(requests_per_minute=60)

    start_time = time.time()
    async with limiter:
        pass  # First request should be immediate
    elapsed = time.time() - start_time
    assert elapsed < 0.1  # Should be near-instant

    # Test rapid requests
    for _ in range(3):
        async with limiter:
            pass

    # Test rate limit error
    with pytest.raises(RateLimitError):
        for _ in range(61):  # Exceed rate limit
            async with limiter:
                await asyncio.sleep(0)  # Small delay to allow other tasks


def test_retry_sync():
    """Test synchronous retry decorator."""
    attempts = 0

    @retry_sync(exceptions=(ValueError,), max_retries=3, backoff=0.1)
    def failing_function():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Temporary error")
        return "success"

    result = failing_function()
    assert result == "success"
    assert attempts == 3

    # Test max retries exceeded
    attempts = 0

    @retry_sync(exceptions=(ValueError,), max_retries=2, backoff=0.1)
    def always_fails():
        nonlocal attempts
        attempts += 1
        raise ValueError("Always fails")

    with pytest.raises(ValueError):
        always_fails()
    assert attempts == 3  # Initial attempt + 2 retries


@pytest.mark.asyncio
async def test_retry_async():
    """Test asynchronous retry decorator."""
    attempts = 0

    @retry_async(exceptions=(ValueError,), max_retries=3, backoff=0.1)
    async def failing_function():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Temporary error")
        return "success"

    result = await failing_function()
    assert result == "success"
    assert attempts == 3

    # Test max retries exceeded
    attempts = 0

    @retry_async(exceptions=(ValueError,), max_retries=2, backoff=0.1)
    async def always_fails():
        nonlocal attempts
        attempts += 1
        raise ValueError("Always fails")

    with pytest.raises(ValueError):
        await always_fails()
    assert attempts == 3  # Initial attempt + 2 retries
