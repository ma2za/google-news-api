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


def sync_example(client: Any = None) -> None:
    """Demonstrate synchronous client usage with examples."""
    print("\n=== Synchronous Client Example ===")

    def run_with(c: GoogleNewsClient) -> None:
        try:
            # Get top news
            print("\nFetching top news...")
            articles = c.top_news(max_results=3)
            for article in articles:
                print_article(article)

            # Search for a specific topic
            topic = "python programming"
            print(f"\nSearching for news about '{topic}'...")
            articles = c.search(topic, max_results=3, when="1h")
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

    if client is not None:
        run_with(client)
    else:
        with GoogleNewsClient(
            language="en", country="US", requests_per_minute=60, cache_ttl=300
        ) as new_client:
            run_with(new_client)


async def async_example(client: Any = None) -> None:
    """Demonstrate asynchronous client usage with examples."""
    print("\n=== Asynchronous Client Example ===")

    async def run_with(c: AsyncGoogleNewsClient) -> None:
        try:
            # Get top news
            print("\nFetching top news...")
            articles = await c.top_news(max_results=3)
            for article in articles:
                print_article(article)

            # Search for a specific topic
            topic = "python programming"
            print(f"\nSearching for news about '{topic}'...")
            articles = await c.search(topic, max_results=3)
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

    if client is not None:
        await run_with(client)
    else:
        async with AsyncGoogleNewsClient(
            language="en", country="US", requests_per_minute=60, cache_ttl=300
        ) as new_client:
            await run_with(new_client)


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
