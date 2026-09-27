"""Compatibility wrapper for the packaged Google News MCP server."""

from google_news_api.mcp_server import (
    batch_news_search,
    create_mcp_app,
    get_client,
    location_news,
    main,
    news_search,
    server_info,
    shutdown,
    top_news,
    top_news_clusters,
)

__all__ = [
    "batch_news_search",
    "create_mcp_app",
    "get_client",
    "location_news",
    "main",
    "mcp",
    "news_search",
    "server_info",
    "shutdown",
    "top_news",
    "top_news_clusters",
]

try:
    mcp = create_mcp_app()
except RuntimeError:
    mcp = None


if __name__ == "__main__":
    main()
