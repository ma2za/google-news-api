"""Packaged MCP server for Google News API."""

import asyncio
import sys
from typing import Any, List, Optional

from google_news_api.client import AsyncGoogleNewsClient

MCP_EXTRA_INSTALL_MESSAGE = (
    'MCP support is not installed. Install it with: '
    'pip install "google-news-api[mcp]"'
)

_clients: dict[tuple[str, str], AsyncGoogleNewsClient] = {}


def _missing_mcp_extra(error: ImportError) -> RuntimeError:
    missing_extra = RuntimeError(MCP_EXTRA_INSTALL_MESSAGE)
    missing_extra.__cause__ = error
    return missing_extra


def _load_fastmcp():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as e:
        raise _missing_mcp_extra(e)
    return FastMCP


def _load_article_dependencies():
    try:
        import aiohttp
        import trafilatura
    except ImportError as e:
        raise _missing_mcp_extra(e)
    return aiohttp, trafilatura


async def get_client(
    language: str = "en", country: str = "US"
) -> AsyncGoogleNewsClient:
    key = (language, country)
    if key not in _clients:
        _clients[key] = AsyncGoogleNewsClient(
            language=language, country=country, requests_per_minute=60, cache_ttl=300
        )
    return _clients[key]


async def extract_article_text(url: str, session: Any) -> Optional[str]:
    _, trafilatura = _load_article_dependencies()
    try:
        async with session.get(url) as response:
            if response.status == 200:
                html_content = await response.text()
                return trafilatura.extract(html_content)
            return None
    except Exception:
        return None


def _attach_extracted_text(
    articles: List[dict[str, Any]],
    decoded_urls: List[Optional[str]],
    extracted_texts: List[Optional[str]],
    include_text: bool = True,
) -> List[dict[str, Any]]:
    for article, decoded_url, text in zip(articles, decoded_urls, extracted_texts):
        if decoded_url:
            article["google_link"] = article["link"]
            article["link"] = decoded_url
            if include_text:
                article["text"] = text or ""
    return articles


async def _enrich_articles(
    client: AsyncGoogleNewsClient,
    articles: List[dict[str, Any]],
    *,
    decode_links: bool = True,
    extract_text: bool = True,
) -> List[dict[str, Any]]:
    if not decode_links:
        return articles

    urls_to_decode = [article["link"] for article in articles]
    decoded_urls = await client.decode_urls(
        urls_to_decode, max_concurrent=5, timeout=30.0, delay=1.0
    )

    if not extract_text:
        return _attach_extracted_text(
            articles,
            decoded_urls,
            [None] * len(articles),
            include_text=False,
        )

    aiohttp, _ = _load_article_dependencies()
    async with aiohttp.ClientSession() as session:

        async def maybe_extract(decoded_url: Optional[str]) -> Optional[str]:
            if not decoded_url:
                return None
            return await extract_article_text(decoded_url, session)

        extracted_texts = await asyncio.gather(
            *(maybe_extract(url) for url in decoded_urls)
        )

    return _attach_extracted_text(articles, decoded_urls, extracted_texts)


async def news_search(
    query: str,
    max_results: Optional[int] = None,
    when: Optional[str] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    language: str = "en",
    country: str = "US",
    decode_links: bool = True,
    extract_text: bool = True,
    mode: str = "default",
) -> List[dict[str, Any]]:
    client = await get_client(language, country)
    try:
        articles = await client.search(
            query=query,
            max_results=max_results,
            when=when,
            after=after,
            before=before,
            mode=mode,
        )
        return await _enrich_articles(
            client,
            articles,
            decode_links=decode_links,
            extract_text=extract_text,
        )
    except Exception as e:
        return [{"error": f"Failed to search news: {str(e)}"}]


async def top_news(
    topic: str = "WORLD",
    max_results: Optional[int] = None,
    language: str = "en",
    country: str = "US",
    decode_links: bool = True,
    extract_text: bool = True,
    mode: str = "default",
) -> List[dict[str, Any]]:
    client = await get_client(language, country)
    try:
        articles = await client.top_news(
            topic=topic,
            max_results=max_results,
            mode=mode,
        )
        return await _enrich_articles(
            client,
            articles,
            decode_links=decode_links,
            extract_text=extract_text,
        )
    except Exception as e:
        return [{"error": f"Failed to fetch top news: {str(e)}"}]


def create_mcp_app():
    FastMCP = _load_fastmcp()
    mcp = FastMCP("googlenews")
    mcp.tool()(news_search)
    mcp.tool()(top_news)
    return mcp


def main() -> None:
    try:
        _load_article_dependencies()
        mcp = create_mcp_app()
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        raise SystemExit(1) from e
    mcp.run(transport="stdio")
