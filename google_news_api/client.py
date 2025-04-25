"""Google News API client implementations."""

# Standard library imports
import logging
import platform
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

# Third-party imports
import feedparser
import httpx
from feedparser import FeedParserDict

# Local imports
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
    """Generate a recent Chrome version number."""
    major = 122  # Latest stable Chrome version
    build = random.randint(0, 5000)
    patch = random.randint(0, 300)
    return f"{major}.0.{build}.{patch}"


def _get_platform_info():
    """Get platform specific browser info."""
    system = platform.system()
    if system == "Windows":
        return "Windows NT 10.0; Win64; x64"
    elif system == "Darwin":
        return "Macintosh; Intel Mac OS X 10_15_7"
    else:
        return "X11; Linux x86_64"


# Chrome browser headers with detailed browser fingerprint
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

    BASE_URL = "https://news.google.com/"

    def __init__(
        self,
        language: str = "en",
        country: str = "US",
        requests_per_minute: int = 60,
        cache_ttl: int = 300,
    ) -> None:
        """Initialize the Google News client."""
        self._validate_language(language)
        self._validate_country(country)

        # Store full language code for hl parameter
        self.language_full = (
            language.upper() if "-" in language else f"{language.upper()}-{country}"
        )
        # Store base language for ceid parameter
        self.language_base = language.split("-")[0].lower()
        self.country = country.upper()
        self._setup_rate_limiter_and_cache(requests_per_minute, cache_ttl)

    @abstractmethod
    def _setup_rate_limiter_and_cache(
        self, requests_per_minute: int, cache_ttl: int
    ) -> None:
        """Set up rate limiter and cache implementations."""
        pass

    @staticmethod
    def _validate_language(language: str) -> None:
        """Validate the language code.

        Args:
            language: Language code (either 'en' or 'en-US' format)

        Raises:
            ConfigurationError: If language code is invalid
        """
        if not isinstance(language, str):
            raise ConfigurationError(
                "Language must be a string",
                field="language",
                value=language,
            )

        # Allow both "en" and "en-US" format
        parts = language.split("-")
        if len(parts) > 2 or len(parts[0]) != 2:
            raise ConfigurationError(
                "Language must be either a two-letter "
                "ISO 639-1 code or language-COUNTRY format",
                field="language",
                value=language,
            )

    @staticmethod
    def _validate_country(country: str) -> None:
        """Validate the country code.

        Args:
            country: Two-letter country code

        Raises:
            ConfigurationError: If country code is invalid
        """
        if not isinstance(country, str) or len(country) != 2:
            raise ConfigurationError(
                "Country must be a two-letter ISO 3166-1 alpha-2 code",
                field="country",
                value=country,
            )

    def _validate_query(self, query: str) -> None:
        """Validate the search query.

        Args:
            query: Search query string

        Raises:
            ValidationError: If query is empty or invalid
        """
        if not query or not isinstance(query, str):
            raise ValidationError(
                "Query must be a non-empty string",
                field="query",
                value=query,
            )

    def _build_url(self, path: str) -> str:
        """Build a URL with language and country parameters."""
        # For search queries, use the search endpoint
        if path.startswith("search"):
            query = path.split("q=")[1] if "q=" in path else ""
            base = f"{self.BASE_URL}rss/search"
            params = {
                "q": query.replace(
                    "+", " "
                ),  # Replace + with space for proper encoding
                "hl": self.language_full,
                "gl": self.country,
                "ceid": f"{self.country}:{self.language_base}",
            }
            return (
                f"{base}?{urlencode(params)}"  # Remove quote() to avoid double encoding
            )

        # For top news
        elif not path:
            base = f"{self.BASE_URL}rss/headlines/section/topic/WORLD"
            params = {
                "hl": self.language_full,
                "gl": self.country,
                "ceid": f"{self.country}:{self.language_base}",
            }
            return f"{base}?{urlencode(params)}"  # Remove quote()

        # For specific topics
        elif path.startswith("topic/"):
            base = f"{self.BASE_URL}rss/headlines/section/{path}"
            params = {
                "hl": self.language_full,
                "gl": self.country,
                "ceid": f"{self.country}:{self.language_base}",
            }
            return f"{base}?{urlencode(params)}"  # Remove quote()

        # For other paths
        base = f"{self.BASE_URL}rss/{path}"
        params = {
            "hl": self.language_full,
            "gl": self.country,
            "ceid": f"{self.country}:{self.language_base}",
        }
        return f"{base}?{urlencode(params)}"  # Remove quote()

    def _parse_articles(
        self, feed: FeedParserDict, max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Parse articles from a feed.

        Args:
            feed: Parsed feed dictionary
            max_results: Maximum number of results to return

        Returns:
            List of article dictionaries
        """
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
        """Get the path for a specific topic."""
        # Map common topics to their Google News paths
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
    """Synchronous client for the Google News RSS feed API."""

    def _setup_rate_limiter_and_cache(
        self, requests_per_minute: int, cache_ttl: int
    ) -> None:
        """Set up synchronous rate limiter and cache."""
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.cache = Cache(ttl=cache_ttl)
        self.client = httpx.Client(
            follow_redirects=True, timeout=30.0, headers=CHROME_HEADERS
        )

    def __del__(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    @retry_sync(exceptions=(HTTPError, RateLimitError), max_retries=3, backoff=2.0)
    def _fetch_feed(self, url: str) -> FeedParserDict:
        """Fetch and parse an RSS feed synchronously.

        Args:
            url: Feed URL to fetch

        Returns:
            Parsed feed dictionary

        Raises:
            HTTPError: If the HTTP request fails
            RateLimitError: If rate limit is exceeded
            ParsingError: If feed parsing fails
        """
        cached = self.cache.get(url)
        if cached is not None:
            return cached

        with self.rate_limiter:
            try:
                response = self.client.get(url)

                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", 60))
                    raise RateLimitError(
                        "Rate limit exceeded",
                        retry_after=retry_after,
                        response=response,
                    )

                if not response.is_success:
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

                self.cache.set(url, feed)
                return feed

            except httpx.RequestError as e:
                raise HTTPError(f"Request failed: {str(e)}")

    def search(
        self,
        query: str,
        *,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Search for news articles synchronously.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of article dictionaries

        Raises:
            ValidationError: If query is empty or invalid
            HTTPError: If the HTTP request fails
            RateLimitError: If rate limit is exceeded
            ParsingError: If response parsing fails
        """
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
        """Get top news articles synchronously for a specific topic."""
        path = self._get_topic_path(topic)
        url = self._build_url(path)
        feed = self._fetch_feed(url)
        return self._parse_articles(feed, max_results)


class AsyncGoogleNewsClient(BaseGoogleNewsClient):
    """Asynchronous client for the Google News RSS feed API."""

    def _setup_rate_limiter_and_cache(
        self, requests_per_minute: int, cache_ttl: int
    ) -> None:
        """Set up asynchronous rate limiter and cache."""
        self.rate_limiter = AsyncRateLimiter(requests_per_minute)
        self.cache = AsyncCache(ttl=cache_ttl)
        self.client = httpx.AsyncClient(
            follow_redirects=True, timeout=30.0, headers=CHROME_HEADERS
        )

    async def __aenter__(self) -> "AsyncGoogleNewsClient":
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context and close the client."""
        await self.client.aclose()

    async def aclose(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    @retry_async(exceptions=(HTTPError, RateLimitError), max_retries=3, backoff=2.0)
    async def _fetch_feed(self, url: str) -> FeedParserDict:
        """Fetch and parse an RSS feed asynchronously.

        Args:
            url: Feed URL to fetch

        Returns:
            Parsed feed dictionary

        Raises:
            HTTPError: If the HTTP request fails
            RateLimitError: If rate limit is exceeded
            ParsingError: If feed parsing fails
        """
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

                if not response.is_success:
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
        """Search for news articles asynchronously.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of article dictionaries

        Raises:
            ValidationError: If query is empty or invalid
            HTTPError: If the HTTP request fails
            RateLimitError: If rate limit is exceeded
            ParsingError: If response parsing fails
        """
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
        """Get top news articles asynchronously for a specific topic."""
        path = self._get_topic_path(topic)
        url = self._build_url(path)
        feed = await self._fetch_feed(url)
        return self._parse_articles(feed, max_results)
