"""Demonstrate basic usage of the Google News API client."""

import asyncio
import logging
import sys
from typing import Any, Dict

from google_news_api import AsyncGoogleNewsClient, GoogleNewsClient
from google_news_api.exceptions import HTTPError, RateLimitError

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def print_article(article: Dict[str, Any]) -> None:
    """Print an article's details in a formatted way."""
    print("\n=== Article ===")
    print(f"Title: {article['title']}")
    print(f"Source: {article['source'] or 'Unknown'}")
    print(f"Published: {article['published']}")
    print(f"Link: {article['link']}")
    if article.get("summary"):
        print(f"\nSummary: {article['summary']}")
    print("=" * 50)


def sync_example():
    """Demonstrate synchronous client usage with examples."""
    print("\n=== Synchronous Client Example ===")

    # Create a client
    client = GoogleNewsClient(
        language="en", country="US", requests_per_minute=60, cache_ttl=300
    )

    try:
        # Get top news
        print("\nFetching top news...")
        articles = client.top_news(max_results=3)
        for article in articles:
            print_article(article)

        # Search for a specific topic
        topic = "python programming"
        print(f"\nSearching for news about '{topic}'...")
        articles = client.search(topic, max_results=3)
        for article in articles:
            print_article(article)

    except RateLimitError as e:
        print(f"Rate limit exceeded: {e}")
        print(f"Please wait {e.retry_after} seconds before trying again")
    except HTTPError as e:
        print(f"HTTP error occurred: {e}")
        print(f"Status code: {e.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        del client


async def async_example():
    """Demonstrate asynchronous client usage with examples."""
    print("\n=== Asynchronous Client Example ===")

    async with AsyncGoogleNewsClient(
        language="en", country="US", requests_per_minute=60, cache_ttl=300
    ) as client:
        try:
            # Get top news
            print("\nFetching top news...")
            articles = await client.top_news(max_results=3)
            for article in articles:
                print_article(article)

            # Search for a specific topic
            topic = "python programming"
            print(f"\nSearching for news about '{topic}'...")
            articles = await client.search(topic, max_results=3)
            for article in articles:
                print_article(article)

        except RateLimitError as e:
            print(f"Rate limit exceeded: {e}")
            print(f"Please wait {e.retry_after} seconds before trying again")
        except HTTPError as e:
            print(f"HTTP error occurred: {e}")
            print(f"Status code: {e.status_code}")
        except Exception as e:
            print(f"An error occurred: {e}")


def main():
    """Run both sync and async examples."""
    # Run synchronous example
    sync_example()

    # Run asynchronous example
    asyncio.run(async_example())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting due to user interrupt...")
        sys.exit(0)
