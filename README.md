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
git clone https://github.com/yourusername/google-news-api.git
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
    # Get top news
    top_articles = client.top_news(max_results=3)
    for article in top_articles:
        print(f"Top News: {article['title']} - {article['source']}")

    # Search for specific topics
    search_articles = client.search("artificial intelligence", max_results=5)
    for article in search_articles:
        print(f"AI News: {article['title']} - {article['source']}")

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
        tech_news = await client.search("technology", max_results=3)
        science_news = await client.search("science", max_results=3)
        
        print(f"Found {len(tech_news)} technology articles")
        print(f"Found {len(science_news)} science articles")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

| Parameter | Description | Default | Example Values |
|-----------|-------------|---------|----------------|
| `language` | Two-letter language code (ISO 639-1) | `"en"` | `"es"`, `"fr"`, `"de"` |
| `country` | Two-letter country code (ISO 3166-1) | `"US"` | `"GB"`, `"DE"`, `"JP"` |
| `requests_per_minute` | Rate limit threshold | `60` | `30`, `100`, `120` |
| `cache_ttl` | Cache duration in seconds | `300` | `600`, `1800`, `3600` |

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
git clone https://github.com/yourusername/google-news-api.git
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

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Contact the author via email
- Check the [examples](examples/) directory for more usage scenarios
