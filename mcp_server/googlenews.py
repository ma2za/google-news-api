"""Google News API server implementation using FastMCP.

This module provides a server implementation for accessing Google News using FastMCP.
It offers functionality to search news articles and get top news by topic.
"""

import asyncio
from typing import Any, List, Optional

import aiohttp
import trafilatura
from mcp.server.fastmcp import FastMCP

from google_news_api.client import AsyncGoogleNewsClient

# Initialize FastMCP server
mcp = FastMCP("googlenews")

# Global client instances - keyed by language and country
_clients: dict[tuple[str, str], AsyncGoogleNewsClient] = {}


async def get_client(
    language: str = "en", country: str = "US"
) -> AsyncGoogleNewsClient:
    """Get or create the AsyncGoogleNewsClient instance.

    For the given language and country.

    Args:
        language: Language code (e.g., "en", "fr")
        or language-country format (e.g., "en-US")
        country: Country code (e.g., "US", "FR")
    """
    key = (language, country)
    if key not in _clients:
        _clients[key] = AsyncGoogleNewsClient(
            language=language, country=country, requests_per_minute=60, cache_ttl=300
        )
    return _clients[key]


async def extract_article_text(
    url: str, session: aiohttp.ClientSession
) -> Optional[str]:
    """Extract the main text content from an article URL.

    Args:
        url: The article URL to extract text from
        session: Aiohttp session to use for requests

    Returns:
        Extracted text content or None if extraction failed
    """
    try:
        async with session.get(url) as response:
            if response.status == 200:
                html_content = await response.text()
                # Use trafilatura to extract clean text
                text = trafilatura.extract(html_content)
                return text
            return None
    except Exception:
        return None


def _attach_extracted_text(
    articles: List[dict[str, Any]],
    decoded_urls: List[Optional[str]],
    extracted_texts: List[Optional[str]],
) -> List[dict[str, Any]]:
    """Attach the decoded link and extracted text to each article.

    ``decoded_urls`` and ``extracted_texts`` are positionally aligned with
    ``articles`` (one entry each; ``None`` where decoding was skipped/failed).
    For a successfully decoded article the original Google link is preserved in
    ``google_link`` *before* ``link`` is overwritten. Articles whose URL could
    not be decoded are left untouched.
    """
    for article, decoded_url, text in zip(articles, decoded_urls, extracted_texts):
        if decoded_url:  # Only update if decoding was successful
            article["google_link"] = article["link"]
            article["link"] = decoded_url
            article["text"] = text or ""
    return articles


@mcp.tool()
async def news_search(
    query: str,
    max_results: Optional[int] = None,
    when: Optional[str] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    language: str = "en",
    country: str = "US",
) -> List[dict[str, Any]]:
    """Search for news articles.

    Args:
        query: Search query string
        max_results: Maximum number of results to return
        when: Relative time range (e.g., "1h", "7d")
        after: Start date in YYYY-MM-DD format
        before: End date in YYYY-MM-DD format
        language: Language code (e.g., "en", "fr") or language-country format
            (e.g., "en-US")
        country: Country code (e.g., "US", "FR")

    Returns:
        List of article dictionaries containing title, link, published date, and summary
    """
    client = await get_client(language, country)
    try:
        # First get the articles
        articles = await client.search(
            query=query, max_results=max_results, when=when, after=after, before=before
        )

        # Decode the URLs
        urls_to_decode = [article["link"] for article in articles]
        decoded_urls = await client.decode_urls(
            urls_to_decode, max_concurrent=5, timeout=30.0, delay=1.0
        )

        # Update articles with decoded URLs and extract their text. Build one
        # extraction coroutine per article (None when the URL was not decoded)
        # so gather() returns texts positionally aligned with `articles`: a
        # single failed decode must not shift the rest or raise IndexError.
        async with aiohttp.ClientSession() as session:

            async def maybe_extract(decoded_url: Optional[str]) -> Optional[str]:
                if not decoded_url:
                    return None
                return await extract_article_text(decoded_url, session)

            extracted_texts = await asyncio.gather(
                *(maybe_extract(url) for url in decoded_urls)
            )

            _attach_extracted_text(articles, decoded_urls, extracted_texts)

        return articles
    except Exception as e:
        return [{"error": f"Failed to search news: {str(e)}"}]


@mcp.tool()
async def top_news(
    topic: str = "WORLD",
    max_results: Optional[int] = None,
    language: str = "en",
    country: str = "US",
) -> List[dict[str, Any]]:
    """Get top news articles for a topic.

    Args:
        topic: News topic (WORLD, NATION, BUSINESS, TECHNOLOGY,
        ENTERTAINMENT, SPORTS, SCIENCE, HEALTH)
        max_results: Maximum number of results to return
        language: Language code (e.g., "en", "fr")
        or language-country format (e.g., "en-US")
        country: Country code (e.g., "US", "FR")

    Returns:
        List of article dictionaries containing title, link, published date, and summary
    """
    client = await get_client(language, country)
    try:
        # First get the articles
        articles = await client.top_news(topic=topic, max_results=max_results)

        # Decode the URLs
        urls_to_decode = [article["link"] for article in articles]
        decoded_urls = await client.decode_urls(
            urls_to_decode, max_concurrent=5, timeout=30.0, delay=1.0
        )

        # Update articles with decoded URLs and extract their text. Build one
        # extraction coroutine per article (None when the URL was not decoded)
        # so gather() returns texts positionally aligned with `articles`: a
        # single failed decode must not shift the rest or raise IndexError.
        async with aiohttp.ClientSession() as session:

            async def maybe_extract(decoded_url: Optional[str]) -> Optional[str]:
                if not decoded_url:
                    return None
                return await extract_article_text(decoded_url, session)

            extracted_texts = await asyncio.gather(
                *(maybe_extract(url) for url in decoded_urls)
            )

            _attach_extracted_text(articles, decoded_urls, extracted_texts)

        return articles
    except Exception as e:
        return [{"error": f"Failed to fetch top news: {str(e)}"}]


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
