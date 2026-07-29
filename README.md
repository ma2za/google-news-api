# Google News API Python Client

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/google-news-api?period=monthly&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads%2Fmonth)](https://pepy.tech/projects/google-news-api)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![PyPI Version](https://img.shields.io/pypi/v/google-news-api)](https://pypi.org/project/google-news-api/)

Unofficial Python client for Google News RSS. Search trusted publishers, run
batch research, fetch top stories, decode article URLs, and use the same tools
from async code, the command line, or an MCP server.

This package is not an official Google API. It uses Google News RSS feeds by
default and offers optional SearchAPI-backed modes when you need provider URLs
or richer snippets.

## Install

```bash
pip install google-news-api
```

Verify the installed command and package version:

```bash
google-news --version
```

## Quickstart

```python
from google_news_api import GoogleNewsClient

with GoogleNewsClient(language="en", country="US") as client:
    articles = client.search("artificial intelligence", when="24h", max_results=5)

for article in articles:
    print(article["title"])
    print(article["source"])
    print(article["published"])
    print(article["link"])
```

## Command Line

The package also installs a `google-news` command for quick searches and
exports:

```bash
google-news search "artificial intelligence" --when 24h --max-results 5
```

Limit results to trusted publishers and exclude unwanted domains:

```bash
google-news search "artificial intelligence" \
  --include-domain reuters.com \
  --include-domain apnews.com \
  --exclude-domain youtube.com \
  --when 7d
```

Run several research queries with the same filters:

```bash
google-news batch "AI regulation" "semiconductor supply chain" \
  --include-domain reuters.com \
  --format json
```

Export machine-readable results as JSON or CSV:

```bash
google-news search "python" --format json
google-news top --topic TECHNOLOGY --max-results 10 --format csv
```

Write any command directly to a UTF-8 file:

```bash
google-news search "python" --format json --output python-news.json
google-news batch "AI regulation" "semiconductors" \
  --format csv \
  --output research.csv
```

Existing files are protected by default. Pass `--force` to replace one, or use
`--output -` to write explicitly to standard output.

Decode Google News RSS links to publisher URLs when exporting:

```bash
google-news search "climate change" --when 7d --decode-links --format json
```

Use the same SearchAPI modes as the Python client:

```bash
google-news search "artificial intelligence regulation" \
  --mode searchapi_light \
  --format json
```

## What You Get

| Capability | Support |
|------------|---------|
| Google News search | Keyword search through Google News RSS |
| Top stories | Topic feeds for world, nation, business, technology, sports, science, health, and entertainment |
| Date filters | `after`, `before`, and relative `when` filters |
| Domain filters | Include trusted publishers or exclude unwanted domains |
| Sync and async clients | `GoogleNewsClient` and `AsyncGoogleNewsClient` |
| URL decoding | Decode Google News RSS article links to publisher URLs |
| Batch search | Search several queries with shared filters |
| SearchAPI modes | Optional direct publisher URLs and richer snippets |
| CLI exports | Table, JSON, and CSV output from the `google-news` command |
| MCP server | `google-news-mcp` for agent and AI tool workflows |

## Article Results

Default Google News RSS results use this shape:

```python
{
    "title": "Article title",
    "link": "https://news.google.com/rss/articles/...",
    "published": "Tue, 16 Jun 2026 12:00:00 GMT",
    "summary": "Article summary",
    "source": "Publisher name",
    "id": "Google News article ID",
}
```

Notes:

- In default mode, `link` is the Google News RSS article URL.
- In SearchAPI modes, `link` is usually the provider or publisher URL returned
  by SearchAPI.
- `id` is always present in normalized results. It is a Google News article ID
  when available, and `None` when the provider does not return one.

## Common Usage

### Top News

```python
from google_news_api import GoogleNewsClient

with GoogleNewsClient(country="US", language="en") as client:
    articles = client.top_news(topic="TECHNOLOGY", max_results=10)
```

### Search With Time Filters

```python
with GoogleNewsClient() as client:
    recent = client.search("climate change", when="24h", max_results=10)
    dated = client.search(
        "Ukraine war",
        after="2024-01-01",
        before="2024-03-01",
        max_results=10,
    )
```

Use `when` for relative time filters such as `"1h"`, `"24h"`, or `"7d"`.
Use `after` and `before` for `YYYY-MM-DD` date range searches. `when` cannot be
combined with `after` or `before`.

### Search Trusted Domains

```python
with GoogleNewsClient() as client:
    articles = client.search(
        "artificial intelligence",
        include_domains=["reuters.com", "apnews.com"],
        exclude_domains=["youtube.com"],
        when="7d",
    )
```

Domain filters are optional and work with `search()` and `batch_search()` on
both synchronous and asynchronous clients. Existing query strings and result
dictionaries are unchanged.

### Decode Google News URLs

```python
with GoogleNewsClient() as client:
    article = client.search("python", max_results=1)[0]
    publisher_url = client.decode_url(article["link"])
```

### Async Client

```python
import asyncio

from google_news_api import AsyncGoogleNewsClient


async def main():
    async with AsyncGoogleNewsClient() as client:
        articles = await client.search("machine learning", when="7d", max_results=5)
        urls = await client.decode_urls([article["link"] for article in articles])
        return urls


asyncio.run(main())
```

## Search Modes

The `search()`, `batch_search()`, and `top_news()` methods support these modes:

| Mode | Backend | Use When |
|------|---------|----------|
| `"default"` | Google News RSS | You want fast Google News RSS results with no API key |
| `"searchapi_portal"` | [SearchAPI Google News Portal](https://www.searchapi.io/docs/google-news-portal-api) | You want direct publisher URLs |
| `"searchapi_light"` | [SearchAPI Google News Light](https://www.searchapi.io/docs/google-news-light-api) | You want recent results and snippets from SearchAPI |

SearchAPI modes require an API key:

```bash
export SEARCHAPI_API_KEY="your-api-key"
```

PowerShell:

```powershell
$env:SEARCHAPI_API_KEY = "your-api-key"
```

```python
with GoogleNewsClient(language="en", country="US") as client:
    articles = client.search(
        "artificial intelligence regulation",
        max_results=10,
        mode="searchapi_light",
    )
```

Use `"default"` first unless you specifically need SearchAPI data.

## MCP Server

Install optional MCP dependencies on Python 3.10 or newer:

```bash
pip install "google-news-api[mcp]"
```

Run the packaged stdio server:

```bash
google-news-mcp
```

The packaged entrypoints are the `google-news-mcp` command and the
`google_news_api.mcp_server` module. The source-tree
`mcp_server/googlenews.py` script remains as a local development compatibility
wrapper.

The MCP server exposes `news_search`, `batch_news_search`, and `top_news`. By default, the tools
decode Google News links to publisher URLs, store the original URL in
`google_link`, and extract article text when possible. The tools also accept
`mode` for the same search modes as the Python client.

For faster headline-only calls:

```python
result = await client.news_search(
    query="artificial intelligence",
    when="24h",
    max_results=10,
    decode_links=False,
    extract_text=False,
)
```

MCP tools accept the same search modes as the Python client. See
[mcp_server/README.md](mcp_server/README.md) for tool parameters and response
format.

## Configuration

| Parameter | Description | Default | Examples |
|-----------|-------------|---------|----------|
| `language` | ISO 639-1 language code or language-country code | `"en"` | `"en"`, `"fr"`, `"en-US"` |
| `country` | ISO 3166-1 alpha-2 country code | `"US"` | `"US"`, `"GB"`, `"DE"` |
| `requests_per_minute` | Client-side request rate limit | `60` | `30`, `100` |
| `cache_ttl` | In-memory cache TTL in seconds | `300` | `600`, `1800` |

Available topics:

- `"WORLD"`
- `"NATION"`
- `"BUSINESS"`
- `"TECHNOLOGY"`
- `"ENTERTAINMENT"`
- `"SPORTS"`
- `"SCIENCE"`
- `"HEALTH"`

## Errors

```python
from google_news_api.exceptions import (
    ConfigurationError,
    HTTPError,
    ParsingError,
    RateLimitError,
    ValidationError,
)
```

The client raises specific exceptions for invalid configuration, invalid query
parameters, HTTP failures, rate limits, and feed parsing failures.

## Development

```bash
git clone https://github.com/ma2za/google-news-api.git
cd google-news-api
poetry install --with dev
pre-commit install
```

Run the same checks as the GitHub Actions workflow before opening a pull
request:

```bash
poetry run black --check google_news_api tests examples mcp_server
poetry run isort --check-only google_news_api tests examples mcp_server
poetry run flake8 google_news_api tests examples mcp_server
poetry run pytest
```

The default test command skips tests that make live network calls. To include
live Google News integration tests:

```bash
poetry run pytest --run-integration
```

## Contributing

1. Fork the repository.
2. Create a branch.
3. Make the smallest useful change.
4. Run the same checks as CI.
5. Open a pull request with the behavior change and test coverage clearly
   described.

## Support The Project

If this Google News API Python client saves you time, consider sponsoring the
project:

[Sponsor ma2za on GitHub](https://github.com/sponsors/ma2za)

Stars, bug reports, and focused pull requests also help maintain the project.

## License

MIT License. See [LICENSE](LICENSE).

## Acknowledgments

URL decoding is based on the work of
[SSujitX/google-news-url-decoder](https://github.com/SSujitX/google-news-url-decoder).
