"""Google News API client implementations.

Provides synchronous and asynchronous clients for
Google News RSS feed API with rate limiting, caching,
and automatic retries. See GoogleNewsClient and
AsyncGoogleNewsClient for usage.
"""

import asyncio
import json
import logging
import platform
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlencode, urlparse

import feedparser
import httpx
from feedparser import FeedParserDict
from selectolax.parser import HTMLParser
from tqdm import tqdm

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

    @staticmethod
    def _validate_date(date: str, param_name: str) -> None:
        """Validate date string format (YYYY-MM-DD).

        Args:
            date: Date string to validate
            param_name: Parameter name for error messages

        Raises:
            ValidationError: If date format is invalid
        """
        import re

        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            raise ValidationError(
                f"{param_name} must be in YYYY-MM-DD format",
                field=param_name,
                value=date,
            )

    @staticmethod
    def _validate_when(when: str) -> None:
        """Validate relative time range format.

        Args:
            when: Time range string (e.g., "1h", "7d")
                 Supports hours (h) up to 101h and days (d)

        Raises:
            ValidationError: If time range format is invalid
        """
        import re

        if not re.match(r"^\d+[hd]$", when):
            raise ValidationError(
                "Time range must be in format: <number>[h|d] "
                "(e.g., '12h' for 12 hours, '7d' for 7 days)",
                field="when",
                value=when,
            )

        # Extract number and unit
        number = int(when[:-1])
        unit = when[-1]

        # Validate limits
        if unit == "h" and number > 101:
            raise ValidationError(
                "Hour range must be <= 101",
                field="when",
                value=when,
            )

    def _build_url(self, path: str) -> str:
        """Build the URL for the request.

        Args:
            path: The path to append to the base URL

        Returns:
            The complete URL
        """
        if path.startswith("search"):
            # Extract query parameters
            query_parts = path.split("q=")[1].split("&")[0] if "q=" in path else ""

            # Build base parameters
            params = {
                "q": query_parts.replace("+", " "),
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
        after: Optional[str] = None,
        before: Optional[str] = None,
        when: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Search for news articles.

        Args:
            query: Search query string
            after: Start date in YYYY-MM-DD format
            before: End date in YYYY-MM-DD format
            when: Relative time range (e.g., "1h", "7d")
            max_results: Maximum number of results to return

        Returns:
            List of article dictionaries

        Note:
            - The after/before parameters allow date-based filtering (max 100 results)
            - The when parameter allows relative time filtering
            (e.g. "12h" for last 12 hours)
            - after/before and when parameters are mutually exclusive
        """
        self._validate_query(query)

        # Build query with time parameters
        query_parts = [query]

        if when is not None:
            if after is not None or before is not None:
                raise ValidationError(
                    "Cannot use 'when' parameter together with 'after' or 'before'",
                    field="when",
                    value=when,
                )
            self._validate_when(when)
            query_parts.append(f"when:{when}")
        else:
            if after is not None:
                self._validate_date(after, "after")
                query_parts.append(f"after:{after}")
            if before is not None:
                self._validate_date(before, "before")
                query_parts.append(f"before:{before}")

        final_query = " ".join(query_parts)
        url = self._build_url(f"search?q={final_query}")
        feed = self._fetch_feed(url)
        return self._parse_articles(feed, max_results)

    def batch_search(
        self,
        queries: List[str],
        *,
        after: Optional[str] = None,
        before: Optional[str] = None,
        when: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform multiple searches in batch.

        Args:
            queries: List of search query strings
            after: Start date in YYYY-MM-DD format
            before: End date in YYYY-MM-DD format
            when: Relative time range (e.g., "1h", "7d")
            max_results: Maximum number of results to return per query

        Returns:
            Dictionary mapping each query to its list of article results

        Note:
            - The after/before parameters allow date-based filtering (max 100 results)
            - The when parameter allows relative time filtering
            (e.g. "12h" for last 12 hours)
            - after/before and when parameters are mutually exclusive
        """
        if not queries:
            return {}

        if not isinstance(queries, list):
            raise ValidationError(
                "queries must be a list of strings",
                field="queries",
                value=queries,
            )

        # Validate time parameters once before running searches
        if when is not None:
            if after is not None or before is not None:
                raise ValidationError(
                    "Cannot use 'when' parameter together with 'after' or 'before'",
                    field="when",
                    value=when,
                )
            self._validate_when(when)
        else:
            if after is not None:
                self._validate_date(after, "after")
            if before is not None:
                self._validate_date(before, "before")

        results = {}
        for query in queries:
            try:
                results[query] = self.search(
                    query,
                    after=after,
                    before=before,
                    when=when,
                    max_results=max_results,
                )
            except ValidationError as e:
                logger.error(f"Error searching for query '{query}': {str(e)}")
                results[query] = []

        return results

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
        after: Optional[str] = None,
        before: Optional[str] = None,
        when: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Search for news articles asynchronously.

        Args:
            query: Search query string
            after: Start date in YYYY-MM-DD format
            before: End date in YYYY-MM-DD format
            when: Relative time range (e.g., "1h", "7d")
            max_results: Maximum number of results to return

        Returns:
            List of article dictionaries

        Note:
            - The after/before parameters allow date-based filtering (max 100 results)
            - The when parameter allows relative time filtering
            (e.g. "12h" for last 12 hours)
            - after/before and when parameters are mutually exclusive
        """
        self._validate_query(query)

        # Build query with time parameters
        query_parts = [query]

        if when is not None:
            if after is not None or before is not None:
                raise ValidationError(
                    "Cannot use 'when' parameter together with 'after' or 'before'",
                    field="when",
                    value=when,
                )
            self._validate_when(when)
            query_parts.append(f"when:{when}")
        else:
            if after is not None:
                self._validate_date(after, "after")
                query_parts.append(f"after:{after}")
            if before is not None:
                self._validate_date(before, "before")
                query_parts.append(f"before:{before}")

        final_query = " ".join(query_parts)
        url = self._build_url(f"search?q={final_query}")
        feed = await self._fetch_feed(url)
        return self._parse_articles(feed, max_results)

    async def batch_search(
        self,
        queries: List[str],
        *,
        after: Optional[str] = None,
        before: Optional[str] = None,
        when: Optional[str] = None,
        max_results: Optional[int] = None,
        max_concurrent: int = 5,
        timeout: float = 30.0,
        delay: float = 1.0,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform multiple searches in batch asynchronously.

        Args:
            queries: List of search query strings
            after: Start date in YYYY-MM-DD format
            before: End date in YYYY-MM-DD format
            when: Relative time range (e.g., "1h", "7d")
            max_results: Maximum number of results to return per query
            max_concurrent: Maximum number of concurrent requests
            timeout: Timeout in seconds for each request
            delay: Delay in seconds between requests to avoid rate limiting

        Returns:
            Dictionary mapping each query to its list of article results

        Note:
            - The after/before parameters allow date-based filtering (max 100 results)
            - The when parameter allows relative time filtering
            (e.g. "12h" for last 12 hours)
            - after/before and when parameters are mutually exclusive
            - Searches are performed concurrently for better performance
            - Shows a progress bar during searching
        """
        if not queries:
            return {}

        if not isinstance(queries, list):
            raise ValidationError(
                "queries must be a list of strings",
                field="queries",
                value=queries,
            )

        # Validate time parameters once before running searches
        if when is not None:
            if after is not None or before is not None:
                raise ValidationError(
                    "Cannot use 'when' parameter together with 'after' or 'before'",
                    field="when",
                    value=when,
                )
            self._validate_when(when)
        else:
            if after is not None:
                self._validate_date(after, "after")
            if before is not None:
                self._validate_date(before, "before")

        pbar = tqdm(total=len(queries), desc="Searching news articles")
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _search_with_progress(
            query: str,
        ) -> Tuple[str, List[Dict[str, Any]]]:
            try:
                async with semaphore:
                    await asyncio.sleep(delay)
                    results = await self.search(
                        query,
                        after=after,
                        before=before,
                        when=when,
                        max_results=max_results,
                    )
                    pbar.update(1)
                    return query, results
            except ValidationError as e:
                logger.error(f"Error searching for query '{query}': {str(e)}")
                pbar.update(1)
                return query, []

        try:
            # Run searches concurrently
            tasks = [_search_with_progress(query) for query in queries]
            results_list = await asyncio.gather(*tasks)

            # Convert results list to dictionary
            return dict(results_list)
        finally:
            pbar.close()

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

    async def decode_url(self, source_url: str, timeout: float = 30.0) -> str:
        """Decode a Google News article URL into its original source URL.

        Args:
            source_url: The Google News article URL to decode
            timeout: Timeout in seconds for the request

        Returns:
            The decoded source URL

        Raises:
            ValidationError: If the URL is invalid
            HTTPError: If the request fails
            ParsingError: If the response cannot be parsed

        Note:
            This implementation is based on the work of SSujitX/google-news-url-decoder
            (https://github.com/SSujitX/google-news-url-decoder)
        """
        try:
            url = urlparse(source_url)
            if not url.netloc.endswith("news.google.com"):
                raise ValidationError(
                    "URL must be a Google News article URL",
                    field="source_url",
                    value=source_url,
                )

            path = url.path.split("/")
            # Check for required path segments: /rss/articles/{base64_id}
            if len(path) < 4 or path[1] != "rss" or path[2] != "articles":
                raise ValidationError(
                    "Invalid Google News URL format",
                    field="source_url",
                    value=source_url,
                )

            base64_str = path[-1]
            url = f"{self.BASE_URL}articles/{base64_str}"

            async with self.rate_limiter:
                response = await self.client.get(
                    url,
                    params={
                        "hl": self.language_full,
                        "gl": self.country,
                        "ceid": f"{self.country}:{self.language_base}",
                    },
                    headers={
                        "User-Agent": "python-requests/2.32.3",
                        "Accept-Encoding": "gzip, deflate",
                        "Accept": "*/*",
                        "Connection": "keep-alive",
                    },
                    timeout=timeout,
                )

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

                parser = HTMLParser(response.text)
                data_element = parser.css_first("c-wiz > div[jscontroller]")
                if not data_element:
                    raise ParsingError(
                        "Could not find required data element in response",
                        data=response.text,
                    )

                signature = data_element.attributes.get("data-n-a-sg")
                timestamp = data_element.attributes.get("data-n-a-ts")
                if not signature or not timestamp:
                    raise ParsingError(
                        "Missing required attributes in response",
                        data=response.text,
                    )

                url = "https://news.google.com/_/DotsSplashUi/data/batchexecute"
                payload = [
                    "Fbv4je",
                    (
                        "["
                        '"garturlreq",'
                        "["
                        '["X","X",["X","X"],null,null,1,1,'
                        f'"{self.country}:{self.language_base}",'
                        "null,1,null,null,null,null,null,0,1],"
                        '"X","X",1,[1,1,1],1,1,null,0,0,null,0],'
                        f'"{base64_str}",{timestamp},"{signature}"'
                        "]"
                    ),
                ]

                response = await self.client.post(
                    url,
                    headers={
                        "Content-Type": (
                            "application/x-www-form-urlencoded;charset=UTF-8"
                        ),
                    },
                    content=f"f.req={quote(json.dumps([[payload]]))}",
                    timeout=timeout,
                )

                if not (200 <= response.status_code < 400):
                    raise HTTPError(
                        f"HTTP {response.status_code}: {response.reason_phrase}",
                        status_code=response.status_code,
                        response_text=response.text,
                    )

                try:
                    parsed_data = json.loads(response.text.split("\n\n")[1])[:-2]
                    decoded_url = json.loads(parsed_data[0][2])[1]
                    return decoded_url
                except (json.JSONDecodeError, IndexError, KeyError) as e:
                    raise ParsingError(
                        "Failed to parse decoded URL from response",
                        data=response.text,
                        error=e,
                    )

        except Exception as e:
            if isinstance(
                e, (ValidationError, HTTPError, ParsingError, RateLimitError)
            ):
                raise
            logger.error(f"Error decoding Google News URL {source_url}: {e}")
            return source_url

    async def decode_urls(
        self,
        urls: List[str],
        *,
        max_concurrent: int = 5,
        timeout: float = 30.0,
        delay: float = 1.0,
    ) -> List[str]:
        """Decode multiple Google News URLs in parallel.

        Args:
            urls: List of Google News URLs to decode
            max_concurrent: Maximum number of concurrent requests
            timeout: Timeout in seconds for each request
            delay: Delay in seconds between requests to avoid rate limiting

        Returns:
            List of decoded URLs in the same order as input.
            Invalid URLs will return None.

        Note:
            - Invalid URLs will return None
            - Uses rate limiting to avoid overwhelming the server
            - Shows a progress bar during decoding
        """
        if not urls:
            return []

        if not isinstance(urls, list):
            raise ValidationError(
                "urls must be a list of strings",
                field="urls",
                value=urls,
            )

        pbar = tqdm(total=len(urls), desc="Decoding Google News URLs")
        semaphore = asyncio.Semaphore(max_concurrent)

        async def decode_with_progress(url: str) -> Optional[str]:
            try:
                async with semaphore:
                    await asyncio.sleep(delay)
                    result = await self.decode_url(url, timeout)
                    pbar.update(1)
                    return result
            except (ValidationError, HTTPError, ParsingError, RateLimitError) as e:
                logger.warning(f"Failed to decode URL {url}: {str(e)}")
                pbar.update(1)
                return None
            except Exception as e:
                logger.error(f"Unexpected error decoding URL {url}: {e}")
                pbar.update(1)
                return None

        try:
            results = await asyncio.gather(*[decode_with_progress(url) for url in urls])
            return results
        finally:
            pbar.close()
