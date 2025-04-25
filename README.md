# Google News API Client

A robust Python client library for the Google News RSS feed API that provides both synchronous and asynchronous implementations with built-in rate limiting, caching, and error handling.

## Features

- ✨ Comprehensive news search and retrieval functionality
- 🔄 Both synchronous and asynchronous APIs
- 🚀 High performance with in-memory caching (TTL-based)
- 🛡️ Built-in rate limiting with token bucket algorithm
- 🔁 Automatic retries with exponential backoff
- 🌍 Multi-language and country support
- 🛠️ Robust error handling and validation

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from google_news_api import GoogleNewsClient

# Initialize client
client = GoogleNewsClient(language="en", country="US")

# Search for news
articles = client.search("artificial intelligence", max_results=5)
for article in articles:
    print(f"{article['title']} - {article['source']}")

# Get top headlines
top_news = client.top_news(max_results=3)
```

For async usage:

```python
from google_news_api import AsyncGoogleNewsClient
import asyncio

async def main():
    async with AsyncGoogleNewsClient() as client:
        articles = await client.search("python programming")
        print(f"Found {len(articles)} articles")

asyncio.run(main())
```

## Configuration Options

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `language` | Two-letter language code (ISO 639-1) | `"en"` | `"es"`, `"fr"` |
| `country` | Two-letter country code (ISO 3166-1) | `"US"` | `"GB"`, `"DE"` |
| `requests_per_minute` | Rate limit threshold | `60` | `30`, `100` |
| `cache_ttl` | Cache duration in seconds | `300` | `600`, `1800` |

## Error Handling

```python
from google_news_api.exceptions import (
    ConfigurationError,
    ValidationError,
    HTTPError,
    RateLimitError,
    ParsingError
)

try:
    articles = client.search("technology")
except ValidationError:
    # Handle invalid search parameters
except RateLimitError:
    # Handle rate limit exceeded
except HTTPError:
    # Handle network/server issues
```

## Best Practices

### Resource Management
- Use context managers for async clients
- Properly close sync clients when done
- Implement appropriate error handling

### Performance Optimization
- Leverage caching for frequently accessed data
- Use async client for concurrent operations
- Group related requests to maximize cache hits

### Rate Limiting
- Configure `requests_per_minute` based on needs
- Handle rate limit errors gracefully
- Implement backoff strategies for retries

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Paolo Mazza (mazzapaolo2019@gmail.com)

## Support

For issues and feature requests, please use the GitHub issue tracker.
