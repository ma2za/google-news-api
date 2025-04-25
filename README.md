# Google News API Client

A Python client library for the Google News RSS feed API, providing both synchronous and asynchronous implementations.

## Features

- Search for news articles by query
- Get top news articles
- Rate limiting with token bucket algorithm
- In-memory caching with TTL
- Automatic retries with exponential backoff
- Both synchronous and asynchronous APIs

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Synchronous Client

```python
from google_news_api import GoogleNewsClient
from google_news_api.exceptions import HTTPError, RateLimitError, ValidationError

def print_article(article):
    """Helper to print article details."""
    print(f"Title: {article['title']}")
    print(f"Source: {article['source']}")
    print(f"Published: {article['published']}")
    print(f"Link: {article['link']}")
    if article['summary']:
        print(f"Summary: {article['summary']}")
    print("---")

# Initialize the client
client = GoogleNewsClient(
    language="en",
    country="US",
    requests_per_minute=60,  # Adjust based on your needs
    cache_ttl=300,  # Cache results for 5 minutes
)

try:
    # Search for multiple topics
    topics = ["python programming", "artificial intelligence", "data science"]
    for topic in topics:
        try:
            print(f"\nNews about {topic}:")
            articles = client.search(topic, max_results=5)
            for article in articles:
                print_article(article)
        except ValidationError as e:
            print(f"Invalid search query '{topic}': {e}")
        except (HTTPError, RateLimitError) as e:
            print(f"Failed to fetch news for '{topic}': {e}")

    # Get top news from different categories
    print("\nTop World News:")
    top_articles = client.top_news(max_results=3)
    for article in top_articles:
        print_article(article)

except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    # Cleanup
    del client
```

### Asynchronous Client

```python
import asyncio
from typing import List, Dict, Any
from google_news_api import AsyncGoogleNewsClient
from google_news_api.exceptions import HTTPError, RateLimitError, ValidationError

async def fetch_topic_news(
    client: AsyncGoogleNewsClient,
    topic: str,
    max_results: int = 5
) -> List[Dict[str, Any]]:
    """Fetch news for a specific topic with error handling."""
    try:
        return await client.search(topic, max_results=max_results)
    except ValidationError as e:
        print(f"Invalid search query '{topic}': {e}")
    except (HTTPError, RateLimitError) as e:
        print(f"Failed to fetch news for '{topic}': {e}")
    return []

def print_article(article: Dict[str, Any]) -> None:
    """Helper to print article details."""
    print(f"Title: {article['title']}")
    print(f"Source: {article['source']}")
    print(f"Published: {article['published']}")
    print(f"Link: {article['link']}")
    if article['summary']:
        print(f"Summary: {article['summary']}")
    print("---")

async def main():
    # Initialize the client using async context manager
    async with AsyncGoogleNewsClient(
        language="en",
        country="US",
        requests_per_minute=60,  # Adjust based on your needs
        cache_ttl=300,  # Cache results for 5 minutes
    ) as client:
        try:
            # Fetch news for multiple topics concurrently
            topics = ["python programming", "artificial intelligence", "data science"]
            tasks = [
                fetch_topic_news(client, topic, max_results=5)
                for topic in topics
            ]
            results = await asyncio.gather(*tasks)

            # Print results for each topic
            for topic, articles in zip(topics, results):
                if articles:
                    print(f"\nNews about {topic}:")
                    for article in articles:
                        print_article(article)

            # Get top news
            print("\nTop World News:")
            top_articles = await client.top_news(max_results=3)
            for article in top_articles:
                print_article(article)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")

# Alternative usage without context manager
async def alternative_example():
    client = AsyncGoogleNewsClient()
    try:
        # Single topic search
        articles = await client.search(
            "python async programming",
            max_results=5
        )
        for article in articles:
            print_article(article)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.aclose()

if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())

    # Run the alternative example
    # asyncio.run(alternative_example())
```

## Configuration

Both clients accept the following parameters:

- `language`: Two-letter language code (ISO 639-1)
- `country`: Two-letter country code (ISO 3166-1 alpha-2)
- `requests_per_minute`: Maximum number of requests per minute (default: 60)
- `cache_ttl`: Cache time-to-live in seconds (default: 300)

## Error Handling

The library can raise the following exceptions:

- `ConfigurationError`: Invalid language or country codes
- `ValidationError`: Invalid search query
- `HTTPError`: HTTP request failed
- `RateLimitError`: Rate limit exceeded
- `ParsingError`: Failed to parse RSS feed

## Best Practices

1. Always properly close the clients:
   - For sync client: use `del client` or ensure it goes out of scope
   - For async client: use async context manager or call `await client.aclose()`

2. Handle rate limits and errors:
   - Catch `RateLimitError` to handle rate limiting
   - Catch `HTTPError` for network/server issues
   - Catch `ValidationError` for invalid inputs

3. Use caching effectively:
   - Set appropriate `cache_ttl` for your use case
   - Higher values reduce API calls but may return stale data
   - Lower values ensure fresh data but increase API usage

4. Concurrent requests:
   - Async client supports concurrent requests via `asyncio.gather`
   - Set appropriate `requests_per_minute` to avoid rate limits
   - Group related requests to maximize cache usage

## License

MIT License

## Author

Paolo Mazza (mazzapaolo2019@gmail.com)
