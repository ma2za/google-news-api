# Google News MCP Server

## Overview
This MCP server provides a bridge to the Google News service, offering tools to search for news articles and fetch top news across different topics. It's built using FastMCP and supports multiple languages and countries with built-in rate limiting and caching.

## Features
- News article search with flexible filtering options
- Top news retrieval by topic
- URL decoding for direct article access
- Automatic rate limiting (60 requests per minute)
- Response caching (5 minutes TTL)
- Multi-language and multi-country support

## Tools

### 1. news_search
Search for news articles with customizable parameters.

Parameters:
- `query`: Search query string
- `max_results`: (Optional) Maximum number of results to return
- `when`: (Optional) Relative time range (e.g., "1h", "7d")
- `after`: (Optional) Start date in YYYY-MM-DD format
- `before`: (Optional) End date in YYYY-MM-DD format
- `language`: Language code (default: "en")
- `country`: Country code (default: "US")
- `decode_links`: Whether to decode Google News URLs to publisher URLs (default: `True`)
- `extract_text`: Whether to fetch decoded URLs and extract article text (default: `True`)
- `mode`: Search backend: `default`, `searchapi_light`, or `searchapi_portal` (default: `default`)

### 2. top_news
Get top news articles for a specific topic.

Parameters:
- `topic`: News category (Options: WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SPORTS, SCIENCE, HEALTH)
- `max_results`: (Optional) Maximum number of results to return
- `language`: Language code (default: "en")
- `country`: Country code (default: "US")
- `decode_links`: Whether to decode Google News URLs to publisher URLs (default: `True`)
- `extract_text`: Whether to fetch decoded URLs and extract article text (default: `True`)
- `mode`: Search backend: `default`, `searchapi_light`, or `searchapi_portal` (default: `default`)

## Response Format
Both tools return a list of article dictionaries containing:
- `title`: Article title
- `link`: Direct article URL (decoded from Google redirect URL)
- `google_link`: Original Google News URL when URL decoding succeeds
- `published`: Article publication date
- `summary`: Article summary
- `source`: News source name
- `text`: Extracted article text when URL decoding and extraction succeed

## Error Handling
If an error occurs, the response will contain a single dictionary with an "error" key describing the issue.

## Configuration
The server includes built-in configurations for:
- Rate limiting: 60 requests per minute
- Cache TTL: 300 seconds (5 minutes)
- URL decoding: 5 concurrent requests maximum with 1-second delay
- Enrichment defaults: `decode_links=True` and `extract_text=True`

## Usage Example
```python
# Example MCP client call for news search
result = await client.news_search(
    query="artificial intelligence",
    when="7d",
    language="en",
    country="US",
    decode_links=False,
    extract_text=False,
)

# Example MCP client call for top news
result = await client.top_news(
    topic="TECHNOLOGY",
    max_results=10,
    mode="searchapi_light",
)
```

## Dependencies
- FastMCP
- AsyncGoogleNewsClient

## Running the Server
On Python 3.10 or newer, install the package with MCP dependencies and run the
packaged stdio server:

```bash
pip install "google-news-api[mcp]"
google-news-mcp
```

The packaged Python module is `google_news_api.mcp_server`.

The source-tree compatibility wrapper still works for local development:

```python
python mcp_server/googlenews.py
```
