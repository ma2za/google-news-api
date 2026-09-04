"""Article link decoding and optional full-text extraction."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from .client import AsyncGoogleNewsClient, GoogleNewsClient
from .exceptions import ValidationError
from .types import Article, EnrichedArticle

EXTRACT_EXTRA_INSTALL_MESSAGE = (
    'Article extraction is not installed. Install it with: '
    'pip install "google-news-api[extract]"'
)


def _load_extractor() -> Callable[[str], Optional[str]]:
    try:
        from trafilatura import extract
    except ImportError as e:
        error = RuntimeError(EXTRACT_EXTRA_INSTALL_MESSAGE)
        error.__cause__ = e
        raise error
    return extract


def _is_google_news_url(url: str) -> bool:
    try:
        hostname = urlparse(url).hostname or ""
    except ValueError:
        return False
    return hostname == "news.google.com" or hostname.endswith(".news.google.com")


def _is_publisher_url(url: Any) -> bool:
    if not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.hostname)
        and not _is_google_news_url(url)
    )


def _validate_options(max_concurrent: int, timeout: float, delay: float) -> None:
    if isinstance(max_concurrent, bool) or not isinstance(max_concurrent, int):
        raise ValidationError(
            "max_concurrent must be a positive integer",
            field="max_concurrent",
            value=max_concurrent,
        )
    if max_concurrent <= 0:
        raise ValidationError(
            "max_concurrent must be a positive integer",
            field="max_concurrent",
            value=max_concurrent,
        )
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise ValidationError(
            "timeout must be a positive number", field="timeout", value=timeout
        )
    if timeout <= 0:
        raise ValidationError(
            "timeout must be a positive number", field="timeout", value=timeout
        )
    if isinstance(delay, bool) or not isinstance(delay, (int, float)):
        raise ValidationError(
            "delay must be a non-negative number", field="delay", value=delay
        )
    if delay < 0:
        raise ValidationError(
            "delay must be a non-negative number", field="delay", value=delay
        )


def _copy_articles(articles: Iterable[Article]) -> List[EnrichedArticle]:
    return [dict(article) for article in articles]


def _decode_targets(
    articles: List[EnrichedArticle],
) -> Tuple[List[int], List[str]]:
    indices = []
    urls = []
    for index, article in enumerate(articles):
        link = article.get("link")
        if isinstance(link, str) and _is_google_news_url(link):
            indices.append(index)
            urls.append(link)
    return indices, urls


def _apply_decoded_urls(
    articles: List[EnrichedArticle],
    indices: List[int],
    source_urls: List[str],
    decoded_urls: List[Optional[str]],
) -> None:
    for index, source_url, decoded_url in zip(indices, source_urls, decoded_urls):
        if decoded_url and decoded_url != source_url and _is_publisher_url(decoded_url):
            articles[index]["google_link"] = source_url
            articles[index]["link"] = decoded_url


class ArticleEnricher:
    def __init__(
        self,
        client: GoogleNewsClient,
        *,
        max_concurrent: int = 5,
        timeout: float = 30.0,
        delay: float = 1.0,
    ):
        _validate_options(max_concurrent, timeout, delay)
        self.client = client
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.delay = delay

    def enrich(
        self,
        articles: Iterable[Article],
        *,
        decode_links: bool = True,
        extract_text: bool = False,
    ) -> List[EnrichedArticle]:
        extractor = _load_extractor() if extract_text else None
        enriched = _copy_articles(articles)

        if decode_links or extract_text:
            indices, urls = _decode_targets(enriched)
            if urls:
                try:
                    decoded_urls = self.client.decode_urls(
                        urls,
                        timeout=self.timeout,
                        delay=self.delay,
                    )
                except Exception:
                    decoded_urls = [None] * len(urls)
                _apply_decoded_urls(enriched, indices, urls, decoded_urls)

        if extractor is None:
            return enriched

        targets = [
            (index, article["link"])
            for index, article in enumerate(enriched)
            if _is_publisher_url(article.get("link"))
        ]
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            extracted = list(
                executor.map(
                    lambda target: self._extract(target[1], extractor),
                    targets,
                )
            )
        for (index, _), (succeeded, text) in zip(targets, extracted):
            if succeeded:
                enriched[index]["text"] = text or ""
        return enriched

    def _extract(
        self, url: str, extractor: Callable[[str], Optional[str]]
    ) -> Tuple[bool, Optional[str]]:
        try:
            time.sleep(self.delay)
            response = self.client._client.get(url, timeout=self.timeout)
            if response.status_code != 200:
                return False, None
            return True, extractor(response.text)
        except Exception:
            return False, None


class AsyncArticleEnricher:
    def __init__(
        self,
        client: AsyncGoogleNewsClient,
        *,
        max_concurrent: int = 5,
        timeout: float = 30.0,
        delay: float = 1.0,
    ):
        _validate_options(max_concurrent, timeout, delay)
        self.client = client
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.delay = delay

    async def enrich(
        self,
        articles: Iterable[Article],
        *,
        decode_links: bool = True,
        extract_text: bool = False,
    ) -> List[EnrichedArticle]:
        extractor = _load_extractor() if extract_text else None
        enriched = _copy_articles(articles)

        if decode_links or extract_text:
            indices, urls = _decode_targets(enriched)
            if urls:
                try:
                    decoded_urls = await self.client.decode_urls(
                        urls,
                        max_concurrent=self.max_concurrent,
                        timeout=self.timeout,
                        delay=self.delay,
                    )
                except Exception:
                    decoded_urls = [None] * len(urls)
                _apply_decoded_urls(enriched, indices, urls, decoded_urls)

        if extractor is None:
            return enriched

        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def extract(index: int, url: str):
            async with semaphore:
                try:
                    await asyncio.sleep(self.delay)
                    response = await self.client.client.get(url, timeout=self.timeout)
                    if response.status_code != 200:
                        return index, False, None
                    return index, True, extractor(response.text)
                except Exception:
                    return index, False, None

        targets = [
            (index, article["link"])
            for index, article in enumerate(enriched)
            if _is_publisher_url(article.get("link"))
        ]
        extracted = await asyncio.gather(
            *(extract(index, url) for index, url in targets)
        )
        for index, succeeded, text in extracted:
            if succeeded:
                enriched[index]["text"] = text or ""
        return enriched
