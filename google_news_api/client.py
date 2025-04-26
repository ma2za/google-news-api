"""Google News API client implementations.

Provides synchronous and asynchronous clients for
Google News RSS feed API with rate limiting, caching,
and automatic retries. See GoogleNewsClient and
AsyncGoogleNewsClient for usage.
"""

import logging
import platform
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import feedparser
import httpx
from feedparser import FeedParserDict

from .exceptions import (
    ConfigurationError,
    HTTPError,
    ParsingError,
    RateLimitError,
    ValidationError,
)
from .utils import (
    AsyncCache,
    AsyncRateLimiter,
    Cache,
    RateLimiter,
    retry_async,
    retry_sync,
)

logger = logging.getLogger(__name__)


def _generate_chrome_version():
    """Generate a plausible Chrome version number."""
    major = 122
    build = random.randint(0, 5000)
    patch = random.randint(0, 300)
    return f"{major}.0.{build}.{patch}"


def _get_platform_info():
    """Get platform-specific browser info string."""
    system = platform.system()
    if system == "Windows":
        return "Windows NT 10.0; Win64; x64"
    elif system == "Darwin":
        return "Macintosh; Intel Mac OS X 10_15_7"
    else:
        return "X11; Linux x86_64"


CHROME_HEADERS = {
    "User-Agent": (
        f"Mozilla/5.0 ({_get_platform_info()}) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{_generate_chrome_version()} Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": ('"Not A(Brand";v="99", "Google Chrome";v="122", "Chromium";v="122"'),
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": f'"{platform.system()}"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Priority": "u=0, i",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
}


class BaseGoogleNewsClient(ABC):
    """Base class for Google News API clients."""

    BASE_URL = "https://news.google.com/rss/"

    def __init__(
        self,
        language: str = "en",
        country: str = "US",
        requests_per_minute: int = 60,
        cache_ttl: int = 300,
    ) -> None:
        """
        Initialize the Google News API client.

        Args:
            language (str): Language code (e.g., "en", "fr", "de") or
                            language-country format (e.g., "en-US", "fr-FR")
            country (str): Country code (e.g., "US", "FR", "DE")
            requests_per_minute (int): Number of requests per minute
            cache_ttl (int): Cache time-to-live in seconds
        """
        self._validate_language(language)
        self._validate_country(country)

        self.language_full = (
            language.upper() if "-" in language else f"{language.upper()}-{country}"
        )
        self.language_base = language.split("-")[0].lower()
        self.country = country.upper()
        self._setup_rate_limiter_and_cache(requests_per_minute, cache_ttl)

    @abstractmethod
    def _setup_rate_limiter_and_cache(
        self, requests_per_minute: int, cache_ttl: int
    ) -> None:
        pass

    @staticmethod
    def _validate_language(language: str) -> None:
        parts = language.split("-")
        if len(parts) > 2 or len(parts[0]) != 2:
            raise ConfigurationError(
                "Language must be a two-letter ISO 639-1 "
                "code or language-COUNTRY format",
                field="language",
                value=language,
            )

    @staticmethod
    def _validate_country(country: str) -> None:
        if not isinstance(country, str) or len(country) != 2:
            raise ConfigurationError(
                "Country must be a two-letter ISO 3166-1 alpha-2 code",
                field="country",
                value=country,
            )

    def _validate_query(self, query: str) -> None:
        if not query or not isinstance(query, str):
            raise ValidationError(
                "Query must be a non-empty string",
                field="query",
                value=query,
            )

    def _build_url(self, path: str) -> str:
        """Build the URL for the request.

        Args:
            path: The path to append to the base URL

        Returns:
            The complete URL
        """
        if path.startswith("search"):
            query = path.split("q=")[1] if "q=" in path else ""
            params = {
                "q": query.replace("+", " "),
                "hl": self.language_full,
                "gl": self.country,
                "ceid": f"{self.country}:{self.language_base}",
            }
            return f"{self.BASE_URL}search?{urlencode(params)}"

        elif not path:
            params = {
                "hl": self.language_full,
                "gl": self.country,
                "ceid": f"{self.country}:{self.language_base}",
            }
            return f"{self.BASE_URL}headlines/section/topic/WORLD?{urlencode(params)}"

        elif path.startswith("topic/"):
            params = {
                "hl": self.language_full,
                "gl": self.country,
                "ceid": f"{self.country}:{self.language_base}",
            }
            return f"{self.BASE_URL}headlines/section/{path}?{urlencode(params)}"

        params = {
            "hl": self.language_full,
            "gl": self.country,
            "ceid": f"{self.country}:{self.language_base}",
        }
        return f"{self.BASE_URL}{path}?{urlencode(params)}"

    def _parse_articles(
        self, feed: FeedParserDict, max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        if max_results == 0:
            return []
        articles = feed.entries[:max_results] if max_results else feed.entries
        return [
            {
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
                "summary": entry.get("summary", ""),
                "source": entry.source.title if "source" in entry else None,
            }
            for entry in articles
        ]

    def _get_topic_path(self, topic: str) -> str:
        topic_map = {
            "WORLD": "WORLD",
            "NATION": "NATION",
            "BUSINESS": "BUSINESS",
            "TECHNOLOGY": "TECHNOLOGY",
            "ENTERTAINMENT": "ENTERTAINMENT",
            "SPORTS": "SPORTS",
            "SCIENCE": "SCIENCE",
            "HEALTH": "HEALTH",
        }

        topic = topic.upper()
        if topic not in topic_map:
            raise ValidationError(
                f"Invalid topic. Must be one of: {', '.join(topic_map.keys())}",
                field="topic",
                value=topic,
            )

        return f"topic/{topic_map[topic]}"


class GoogleNewsClient(BaseGoogleNewsClient):
    """Synchronous client for Google News RSS feed API."""

    def _setup_rate_limiter_and_cache(
        self, requests_per_minute: int, cache_ttl: int
    ) -> None:
        """Set up rate limiter and cache.

        Args:
            requests_per_minute: Maximum number of requests per minute
            cache_ttl: Cache time-to-live in seconds
        """
        self._rate_limiter = RateLimiter(requests_per_minute)
        self._cache = Cache(ttl=cache_ttl)
        self._client = httpx.Client(
            follow_redirects=True, timeout=30.0, headers=CHROME_HEADERS
        )

    def __init__(
        self,
        language: str = "en",
        country: str = "US",
        requests_per_minute: int = 60,
        cache_ttl: int = 300,
    ) -> None:
        """Initialize the client.

        Args:
            language: Two-letter language code (ISO 639-1) or language-country code
            country: Two-letter country code (ISO 3166-1 alpha-2)
            requests_per_minute: Maximum number of requests per minute
            cache_ttl: Cache time-to-live in seconds
        """
        super().__init__(language, country, requests_per_minute, cache_ttl)

    def __del__(self) -> None:
        """Clean up resources."""
        if hasattr(self, "_client"):
            self._client.close()

    @retry_sync(exceptions=(HTTPError, RateLimitError), max_retries=3, backoff=2.0)
    def _fetch_feed(self, url: str) -> FeedParserDict:
        cached = self._cache.get(url)
        if cached is not None:
            return cached

        with self._rate_limiter:
            try:
                response = self._client.get(url)

                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", 60))
                    raise RateLimitError(
                        "Rate limit exceeded",
                        retry_after=retry_after,
                        response=response,
                    )

                if not (200 <= response.status_code < 400):
                    raise HTTPError(
                        f"HTTP {response.status_code}: {response.reason_phrase}",
                        status_code=response.status_code,
                        response_text=response.text,
                    )

                feed = feedparser.parse(response.text)

                if feed.bozo:
                    raise ParsingError(
                        "Failed to parse feed",
                        data=response.text,
                        error=feed.bozo_exception,
                    )

                self._cache.set(url, feed)
                return feed

            except httpx.RequestError as e:
                raise HTTPError(f"Request failed: {str(e)}")

    def search(
        self,
        query: str,
        *,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Search for news articles."""
        self._validate_query(query)
        url = self._build_url(f"search?q={query}")
        feed = self._fetch_feed(url)
        return self._parse_articles(feed, max_results)

    def top_news(
        self,
        topic: str = "WORLD",
        *,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get top news articles for a topic."""
        path = self._get_topic_path(topic)
        url = self._build_url(path)
        feed = self._fetch_feed(url)
        return self._parse_articles(feed, max_results)


class AsyncGoogleNewsClient(BaseGoogleNewsClient):
    """Asynchronous client for Google News RSS feed API."""

    def _setup_rate_limiter_and_cache(
        self, requests_per_minute: int, cache_ttl: int
    ) -> None:
        self.rate_limiter = AsyncRateLimiter(requests_per_minute)
        self.cache = AsyncCache(ttl=cache_ttl)
        self.client = httpx.AsyncClient(
            follow_redirects=True, timeout=30.0, headers=CHROME_HEADERS
        )

    async def __aenter__(self) -> "AsyncGoogleNewsClient":
        """Enter the context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        await self.client.aclose()

    async def aclose(self) -> None:
        """Close the client."""
        await self.client.aclose()

    @retry_async(exceptions=(HTTPError, RateLimitError), max_retries=3, backoff=2.0)
    async def _fetch_feed(self, url: str) -> FeedParserDict:
        cached = await self.cache.get(url)
        if cached is not None:
            return cached

        async with self.rate_limiter:
            try:
                response = await self.client.get(url)

                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", 60))
                    raise RateLimitError(
                        "Rate limit exceeded",
                        retry_after=retry_after,
                        response=response,
                    )

                if not (200 <= response.status_code < 400):
                    raise HTTPError(
                        f"HTTP {response.status_code}: {response.reason_phrase}",
                        status_code=response.status_code,
                        response_text=response.text,
                    )

                feed = feedparser.parse(response.text)

                if feed.bozo:
                    raise ParsingError(
                        "Failed to parse feed",
                        data=response.text,
                        error=feed.bozo_exception,
                    )

                await self.cache.set(url, feed)
                return feed

            except httpx.RequestError as e:
                raise HTTPError(f"Request failed: {str(e)}")

    async def search(
        self,
        query: str,
        *,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Search for news articles asynchronously."""
        self._validate_query(query)
        url = self._build_url(f"search?q={query}")
        feed = await self._fetch_feed(url)
        return self._parse_articles(feed, max_results)

    async def top_news(
        self,
        topic: str = "WORLD",
        *,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get top news articles for a topic asynchronously."""
        path = self._get_topic_path(topic)
        url = self._build_url(path)
        feed = await self._fetch_feed(url)
        return self._parse_articles(feed, max_results)
