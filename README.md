# Google News API Client

[![PyPI Downloads](https://static.pepy.tech/badge/google-news-api)](https://pepy.tech/projects/google-news-api)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![PyPI Version](https://img.shields.io/pypi/v/google-news-api)](https://pypi.org/project/google-news-api/)

A robust Python client library for the Google News RSS feed API that provides both synchronous and asynchronous implementations with built-in rate limiting, caching, and error handling.

## Features

- ✨ Comprehensive news search and retrieval functionality
  - Search by keywords with advanced filtering
  - Get top news by topic (WORLD, NATION, BUSINESS, TECHNOLOGY, etc.)
  - Batch search support for multiple queries
  - URL decoding for original article sources
- 🔄 Both synchronous and asynchronous APIs
  - `GoogleNewsClient` for synchronous operations
  - `AsyncGoogleNewsClient` for async/await support
- 🕒 Advanced time-based search capabilities
  - Date range filtering (after/before)
  - Relative time filtering (e.g., "1h", "24h", "7d")
  - Maximum 100 results for date-based searches
- 🚀 High performance features
  - In-memory caching with configurable TTL
  - Built-in rate limiting with token bucket algorithm
  - Automatic retries with exponential backoff
  - Concurrent batch searches in async mode
- 🌍 Multi-language and country support
  - ISO 639-1 language codes (e.g., "en", "fr", "de")
  - ISO 3166-1 country codes (e.g., "US", "GB", "DE")
  - Language-country combinations (e.g., "en-US", "fr-FR")
- 🛡️ Robust error handling
  - Specific exceptions for different error scenarios
  - Detailed error messages with context
  - Graceful fallbacks and retries
- 📦 Modern Python packaging with Poetry

## Requirements

- Python 3.9 or higher
- Poetry (recommended for installation)

## Installation

### Using Poetry (recommended)

```bash
# Install using Poetry
poetry add google-news-api

# Or clone and install from source
git clone https://github.com/ma2za/google-news-api.git
cd google-news-api
poetry install
```

### Using pip

```bash
pip install google-news-api
```

## Usage Examples

### Synchronous Client

```python
from google_news_api import GoogleNewsClient

# Initialize client with custom configuration
client = GoogleNewsClient(
    language="en",
    country="US",
    requests_per_minute=60,
    cache_ttl=300
)

try:
    # Get top news by topic
    world_news = client.top_news(topic="WORLD", max_results=5)
    tech_news = client.top_news(topic="TECHNOLOGY", max_results=3)
    
    # Search with date range
    date_articles = client.search(
        "Ukraine war",
        after="2024-01-01",
        before="2024-03-01",
        max_results=5
    )
    
    # Search with relative time
    recent_articles = client.search(
        "climate change",
        when="24h",  # Last 24 hours
        max_results=5
    )
    
    # Batch search multiple queries
    batch_results = client.batch_search(
        queries=["AI", "machine learning", "deep learning"],
        when="7d",  # Last 7 days
        max_results=3
    )
    
    # Process results
    for topic, articles in batch_results.items():
        print(f"\nTop {topic} news:")
        for article in articles:
            print(f"- {article['title']} ({article['source']})")
            print(f"  Published: {article['published']}")
            print(f"  Summary: {article['summary'][:100]}...")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Clean up resources
    del client
```

### Asynchronous Client

```python
from google_news_api import AsyncGoogleNewsClient
import asyncio

async def main():
    async with AsyncGoogleNewsClient(
        language="en",
        country="US",
        requests_per_minute=60
    ) as client:
        # Fetch multiple news categories concurrently
        world_news = await client.top_news(topic="WORLD", max_results=3)
        tech_news = await client.top_news(topic="TECHNOLOGY", max_results=3)
        
        # Batch search with concurrent execution
        batch_results = await client.batch_search(
            queries=["AI", "machine learning", "deep learning"],
            when="7d",
            max_results=3
        )
        
        # Decode Google News URLs to original sources
        for topic, articles in batch_results.items():
            print(f"\nTop {topic} news:")
            for article in articles:
                original_url = await client.decode_url(article['link'])
                print(f"- {article['title']} ({article['source']})")
                print(f"  Original URL: {original_url}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

The library provides extensive configuration options through the client initialization:

| Parameter | Description | Default | Example Values |
|-----------|-------------|---------|----------------|
| `language` | Two-letter language code (ISO 639-1) or language-country format | `"en"` | `"en"`, `"fr"`, `"de"`, `"en-US"`, `"fr-FR"` |
| `country` | Two-letter country code (ISO 3166-1 alpha-2) | `"US"` | `"US"`, `"GB"`, `"DE"`, `"JP"` |
| `requests_per_minute` | Rate limit threshold for API requests | `60` | `30`, `100`, `120` |
| `cache_ttl` | Cache duration in seconds for responses | `300` | `600`, `1800`, `3600` |

### Available Topics

The `top_news()` method supports the following topics:
- `"WORLD"` - World news
- `"NATION"` - National news
- `"BUSINESS"` - Business news
- `"TECHNOLOGY"` - Technology news
- `"ENTERTAINMENT"` - Entertainment news
- `"SPORTS"` - Sports news
- `"SCIENCE"` - Science news
- `"HEALTH"` - Health news

### Time-Based Search

The library supports two types of time-based search:

1. **Date Range Search**
   - Use `after` and `before` parameters
   - Format: `YYYY-MM-DD`
   - Maximum 100 results
   - Example: `after="2024-01-01", before="2024-03-01"`

2. **Relative Time Search**
   - Use the `when` parameter
   - Hours: `"1h"` to `"101h"`
   - Days: Any number of days (e.g., `"7d"`, `"30d"`)
   - Cannot be used with `after`/`before`
   - Example: `when="24h"` for last 24 hours

### Article Structure

Each article in the results contains the following fields:
- `title`: Article title
- `link`: Google News article URL
- `published`: Publication date and time
- `summary`: Article summary/description
- `source`: News source name

## Error Handling

The library provides specific exceptions for different error scenarios:

```python
from google_news_api.exceptions import (
    ConfigurationError,  # Invalid client configuration
    ValidationError,     # Invalid parameters
    HTTPError,          # Network or server issues
    RateLimitError,     # Rate limit exceeded
    ParsingError        # RSS feed parsing errors
)

try:
    articles = client.search("technology")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
except HTTPError as e:
    print(f"HTTP error {e.status_code}: {str(e)}")
except ValidationError as e:
    print(f"Invalid parameters: {str(e)}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")
```

## Best Practices

### Resource Management
- Use context managers (`async with`) for async clients
- Explicitly close synchronous clients when done
- Implement proper error handling and cleanup

### Performance Optimization
- Utilize caching for frequently accessed queries
- Use the async client for concurrent operations
- Batch related requests to maximize cache efficiency
- Configure appropriate cache TTL based on your needs

### Rate Limiting
- Set `requests_per_minute` based on your requirements
- Implement exponential backoff for rate limit errors
- Monitor rate limit usage in production

## Development

### Setting up the Development Environment

```bash
# Clone the repository
git clone https://github.com/ma2za/google-news-api.git
cd google-news-api

# Install development dependencies
poetry install --with dev

# Set up pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run tests with Poetry
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=google_news_api

# Run pre-commit on all files
pre-commit run --all-files
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`poetry run pytest` and `poetry run flake8`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Paolo Mazza (mazzapaolo2019@gmail.com)

## Acknowledgments

- The URL decoding functionality is based on the work of [SSujitX/google-news-url-decoder](https://github.com/SSujitX/google-news-url-decoder)

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Contact the author via email
- Check the [examples](examples/) directory for more usage scenarios

## Time-Based Search

The library supports two types of time-based search:

### Date Range Search

Use `after` and `before` parameters to search within a specific date range:

```python
articles = client.search(
    "Ukraine war",
    after="2024-01-01",  # Start date (YYYY-MM-DD)
    before="2024-03-01", # End date (YYYY-MM-DD)
    max_results=5
)
```

### Relative Time Search

Use the `when` parameter for relative time searches:

```python
# Last hour
articles = client.search("climate change", when="1h")

# Last 24 hours
articles = client.search("climate change", when="24h")

# Last 7 days
articles = client.search("climate change", when="7d")
```

Notes:
- Date range parameters (`after`/`before`) must be in YYYY-MM-DD format
- Relative time (`when`) supports:
  - Hours (h): 1-101 hours (e.g., "1h", "24h", "101h")
  - Days (d): Any number of days (e.g., "1d", "7d", "30d")
- `when` parameter cannot be used together with `after` or `before`
- All searches return articles sorted by relevance and recency
