"""Tests for the MCP server article post-processing."""

import googlenews


def test_compatibility_wrapper_exports_all_mcp_tools():
    assert googlenews.news_search
    assert googlenews.batch_news_search
    assert googlenews.top_news
    assert googlenews.location_news
