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

        # Update articles with decoded URLs and extract text
        async with aiohttp.ClientSession() as session:
            extraction_tasks = []
            for article, decoded_url in zip(articles, decoded_urls):
                if decoded_url:  # Only update if decoding was successful
                    article["link"] = decoded_url
                    # Preserve original Google link
                    article["google_link"] = article["link"]
                    # Add text extraction task
                    task = extract_article_text(decoded_url, session)
                    extraction_tasks.append(task)
                else:
                    extraction_tasks.append(None)

            # Wait for all text extractions to complete
            extracted_texts = await asyncio.gather(
                *[task for task in extraction_tasks if task is not None]
            )

            # Add extracted texts to articles
            text_idx = 0
            for article in articles:
                if "error" not in article and article.get("link"):
                    article["text"] = extracted_texts[text_idx] or ""
                    text_idx += 1

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

        # Update articles with decoded URLs and extract text
        async with aiohttp.ClientSession() as session:
            extraction_tasks = []
            for article, decoded_url in zip(articles, decoded_urls):
                if decoded_url:  # Only update if decoding was successful
                    article["link"] = decoded_url
                    # Preserve original Google link
                    article["google_link"] = article["link"]
                    # Add text extraction task
                    task = extract_article_text(decoded_url, session)
                    extraction_tasks.append(task)
                else:
                    extraction_tasks.append(None)

            # Wait for all text extractions to complete
            extracted_texts = await asyncio.gather(
                *[task for task in extraction_tasks if task is not None]
            )

            # Add extracted texts to articles
            text_idx = 0
            for article in articles:
                if "error" not in article and article.get("link"):
                    article["text"] = extracted_texts[text_idx] or ""
                    text_idx += 1

        return articles
    except Exception as e:
        return [{"error": f"Failed to fetch top news: {str(e)}"}]


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
