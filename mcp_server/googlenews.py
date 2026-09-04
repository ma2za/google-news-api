"""Compatibility wrapper for the packaged Google News MCP server."""

from google_news_api.mcp_server import (
    batch_news_search,
    create_mcp_app,
    get_client,
    location_news,
    main,
    news_search,
    top_news,
)

__all__ = [
    "batch_news_search",
    "create_mcp_app",
    "get_client",
    "location_news",
    "main",
    "mcp",
    "news_search",
    "top_news",
]

try:
    mcp = create_mcp_app()
except RuntimeError:
    mcp = None


if __name__ == "__main__":
    main()
