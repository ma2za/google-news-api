"""Compatibility wrapper for the packaged Google News MCP server."""

from google_news_api.mcp_server import (
    _attach_extracted_text,
    create_mcp_app,
    extract_article_text,
    get_client,
    main,
    news_search,
    top_news,
)

__all__ = [
    "_attach_extracted_text",
    "create_mcp_app",
    "extract_article_text",
    "get_client",
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
