"""Packaged MCP server for Google News API."""

import asyncio
import sys
from typing import Any, Dict, List, Optional

from google_news_api.client import AsyncGoogleNewsClient
from google_news_api.enrichment import AsyncArticleEnricher, _load_extractor

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


async def get_client(
    language: str = "en", country: str = "US"
) -> AsyncGoogleNewsClient:
    key = (language, country)
    if key not in _clients:
        _clients[key] = AsyncGoogleNewsClient(
            language=language, country=country, requests_per_minute=60, cache_ttl=300
        )
    return _clients[key]


async def _enrich_articles(
    client: AsyncGoogleNewsClient,
    articles: List[dict[str, Any]],
    *,
    decode_links: bool = True,
    extract_text: bool = True,
) -> List[dict[str, Any]]:
    if not decode_links:
        return [dict(article) for article in articles]
    return await AsyncArticleEnricher(client).enrich(
        articles,
        decode_links=True,
        extract_text=extract_text,
    )


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
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
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
            include_domains=include_domains,
            exclude_domains=exclude_domains,
        )
        return await _enrich_articles(
            client,
            articles,
            decode_links=decode_links,
            extract_text=extract_text,
        )
    except Exception as e:
        return [{"error": f"Failed to search news: {str(e)}"}]


async def batch_news_search(
    queries: List[str],
    max_results: Optional[int] = None,
    when: Optional[str] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    language: str = "en",
    country: str = "US",
    decode_links: bool = True,
    extract_text: bool = True,
    mode: str = "default",
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
) -> Dict[str, List[dict[str, Any]]]:
    client = await get_client(language, country)
    try:
        results = await client.batch_search(
            queries=queries,
            max_results=max_results,
            when=when,
            after=after,
            before=before,
            mode=mode,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
        )
        enriched = await asyncio.gather(
            *(
                _enrich_articles(
                    client,
                    articles,
                    decode_links=decode_links,
                    extract_text=extract_text,
                )
                for articles in results.values()
            )
        )
        return dict(zip(results, enriched))
    except Exception as e:
        return {"error": [{"error": f"Failed to batch search news: {str(e)}"}]}


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


async def location_news(
    location: str,
    max_results: Optional[int] = None,
    language: str = "en",
    country: str = "US",
    decode_links: bool = True,
    extract_text: bool = True,
) -> List[dict[str, Any]]:
    client = await get_client(language, country)
    try:
        articles = await client.location_news(
            location=location,
            max_results=max_results,
        )
        return await _enrich_articles(
            client,
            articles,
            decode_links=decode_links,
            extract_text=extract_text,
        )
    except Exception as e:
        return [{"error": f"Failed to fetch location news: {str(e)}"}]


def create_mcp_app():
    FastMCP = _load_fastmcp()
    mcp = FastMCP("googlenews")
    mcp.tool()(news_search)
    mcp.tool()(batch_news_search)
    mcp.tool()(top_news)
    mcp.tool()(location_news)
    return mcp


def main() -> None:
    try:
        _load_extractor()
        mcp = create_mcp_app()
    except (ImportError, RuntimeError) as e:
        print(MCP_EXTRA_INSTALL_MESSAGE, file=sys.stderr)
        raise SystemExit(1) from e
    mcp.run(transport="stdio")
