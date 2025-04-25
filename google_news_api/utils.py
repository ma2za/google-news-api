"""Utility functions and classes for the Google News API client."""

import asyncio
import functools
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from .exceptions import RateLimitError
from .logging import logger

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class RateLimiter:
    """Synchronous rate limiter implementation using token bucket algorithm."""

    def __init__(self, requests_per_minute: int) -> None:
        """Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum number of requests per minute

        Raises:
            ValueError: If requests_per_minute is not positive
        """
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")

        self.requests_per_minute = requests_per_minute
        self.tokens = float(requests_per_minute)
        self.last_update = time.monotonic()
        self.lock = threading.Lock()

    def __enter__(self) -> None:
        """Acquire a token, waiting if necessary.

        Raises:
            RateLimitError: If rate limit is exceeded
        """
        with self.lock:
            now = time.monotonic()
            time_passed = now - self.last_update
            self.tokens = min(
                self.requests_per_minute,
                self.tokens + time_passed * (self.requests_per_minute / 60.0),
            )
            self.last_update = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) * (60.0 / self.requests_per_minute)
                logger.warning(
                    "Rate limit reached",
                    extra={
                        "wait_time": wait_time,
                        "requests_per_minute": self.requests_per_minute,
                    },
                )
                raise RateLimitError(
                    f"Rate limit exceeded. Try again in {wait_time:.2f} seconds",
                )

            self.tokens -= 1

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        pass


class AsyncRateLimiter:
    """Asynchronous rate limiter implementation using token bucket algorithm."""

    def __init__(self, requests_per_minute: int) -> None:
        """Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum number of requests per minute

        Raises:
            ValueError: If requests_per_minute is not positive
        """
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")

        self.requests_per_minute = requests_per_minute
        self.tokens = float(requests_per_minute)
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()

    async def __aenter__(self) -> None:
        """Acquire a token, waiting if necessary.

        Raises:
            RateLimitError: If rate limit is exceeded
        """
        async with self.lock:
            now = time.monotonic()
            time_passed = now - self.last_update
            self.tokens = min(
                self.requests_per_minute,
                self.tokens + time_passed * (self.requests_per_minute / 60.0),
            )
            self.last_update = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) * (60.0 / self.requests_per_minute)
                logger.warning(
                    "Rate limit reached",
                    extra={
                        "wait_time": wait_time,
                        "requests_per_minute": self.requests_per_minute,
                    },
                )
                raise RateLimitError(
                    f"Rate limit exceeded. Try again in {wait_time:.2f} seconds",
                )

            self.tokens -= 1

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        pass


class Cache:
    """Simple synchronous in-memory cache with TTL."""

    def __init__(self, ttl: int) -> None:
        """Initialize the cache.

        Args:
            ttl: Time to live in seconds

        Raises:
            ValueError: If ttl is not positive
        """
        if ttl <= 0:
            raise ValueError("ttl must be positive")

        self.ttl = ttl
        self.cache: Dict[str, tuple[Any, datetime]] = {}
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self.lock:
            if key not in self.cache:
                return None

            value, expiry = self.cache[key]
            if datetime.now() > expiry:
                del self.cache[key]
                return None

            return value

    def set(self, key: str, value: Any) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            expiry = datetime.now() + timedelta(seconds=self.ttl)
            self.cache[key] = (value, expiry)

    def clear(self) -> None:
        """Clear all cached values."""
        with self.lock:
            self.cache.clear()


class AsyncCache:
    """Simple asynchronous in-memory cache with TTL."""

    def __init__(self, ttl: int) -> None:
        """Initialize the cache.

        Args:
            ttl: Time to live in seconds

        Raises:
            ValueError: If ttl is not positive
        """
        if ttl <= 0:
            raise ValueError("ttl must be positive")

        self.ttl = ttl
        self.cache: Dict[str, tuple[Any, datetime]] = {}
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        async with self.lock:
            if key not in self.cache:
                return None

            value, expiry = self.cache[key]
            if datetime.now() > expiry:
                del self.cache[key]
                return None

            return value

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        async with self.lock:
            expiry = datetime.now() + timedelta(seconds=self.ttl)
            self.cache[key] = (value, expiry)

    async def clear(self) -> None:
        """Clear all cached values."""
        async with self.lock:
            self.cache.clear()


def retry_sync(
    max_retries: int = 3,
    backoff: float = 0.5,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Retry synchronous functions with exponential backoff.

    Args:
        max_retries: Maximum number of retries
        backoff: Initial backoff time in seconds
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorated function

    Raises:
        ValueError: If max_retries or backoff is not positive
    """
    if max_retries <= 0:
        raise ValueError("max_retries must be positive")
    if backoff <= 0:
        raise ValueError("backoff must be positive")

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise
                    wait_time = backoff * (2**attempt)
                    logger.warning(
                        "Request failed, retrying",
                        extra={
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "wait_time": wait_time,
                            "error": str(e),
                        },
                    )
                    time.sleep(wait_time)
            raise last_exception  # pragma: no cover

        return cast(F, wrapper)

    return decorator


def retry_async(
    max_retries: int = 3,
    backoff: float = 0.5,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Retry async functions with exponential backoff.

    Args:
        max_retries: Maximum number of retries
        backoff: Initial backoff time in seconds
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorated function

    Raises:
        ValueError: If max_retries or backoff is not positive
    """
    if max_retries <= 0:
        raise ValueError("max_retries must be positive")
    if backoff <= 0:
        raise ValueError("backoff must be positive")

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise
                    wait_time = backoff * (2**attempt)
                    logger.warning(
                        "Request failed, retrying",
                        extra={
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "wait_time": wait_time,
                            "error": str(e),
                        },
                    )
                    await asyncio.sleep(wait_time)
            raise last_exception  # pragma: no cover

        return cast(F, wrapper)

    return decorator
