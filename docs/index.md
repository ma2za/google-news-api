# Google News API

Unofficial Python client for Google News RSS with sync, async, URL decoding,
caching, full-text enrichment, and Model Context Protocol (MCP) support.

## Key Features

- **Sync & Async Parity:** Complete feature parity across `GoogleNewsClient` and
  `AsyncGoogleNewsClient`.
- **Zero API Keys Required:** Default operations leverage free Google News RSS
  feeds.
- **Real URL Decoding:** Resolves Google News redirect URLs into direct canonical
  publisher links (`decode_url` / `decode_urls`).
- **Resilient Network Engine:** Automatic exponential backoff, RFC 9110 HTTP-date
  `Retry-After` parsing, and rate limiting.
- **In-Memory Caching:** Built-in TTL caching prevents duplicate feed requests.
- **Model Context Protocol (MCP):** Built-in server for Claude Desktop, Cursor,
  and AI agent integration via stdio or streamable HTTP.
- **Full-Text Enrichment:** Optional article extraction using Trafilatura.
- **Type Safety:** PEP 561 `py.typed` marker and strongly-typed dictionary definitions.

## Installation

```bash
# Core package
pip install google-news-api

# With article text extraction
pip install "google-news-api[extract]"

# With MCP server support
pip install "google-news-api[mcp]"

# With all optional dependencies
pip install "google-news-api[all]"
```

## Quick Start

```python
from google_news_api import GoogleNewsClient

with GoogleNewsClient(language="en", country="US") as client:
    # Top headlines
    headlines = client.top_news(topic="TECHNOLOGY", max_results=5)
    for article in headlines:
        print(f"[{article['source']}] {article['title']}")

    # Search with time window
    articles = client.search("space exploration", when="24h", max_results=5)
    for article in articles:
        print(f"• {article['title']}")
```

## Documentation Structure

- **[Compatibility Policy](compatibility.md):** Semantic versioning and API stability guarantees.
- **[Guides](guides/first_search.md):** 9 practical, executable guides for every library capability.
- **[API Reference](reference/client.md):** Full class and module signatures.
- **[Releasing](releasing.md):** Maintainer release procedures.
