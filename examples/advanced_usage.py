"""Demonstrate advanced usage of the Google News API client."""

import asyncio
import logging

from google_news_api import AsyncGoogleNewsClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def print_news_section(title: str, articles: list) -> None:
    """Print a section of news articles with formatting."""
    print(f"\n{title}:")
    print("-" * len(title))
    for article in articles:
        print(f"Title: {article['title']}")
        print(f"Source: {article['source']}")
        print(f"Link: {article['link']}")
        if "published" in article:
            print(f"Published: {article['published']}")
        print("-" * len(title))


async def main():
    """Execute the main async function to demonstrate Google News API usage."""
    # Initialize the client with Spanish language and Spain as country
    async with AsyncGoogleNewsClient(language="es", country="ES") as client:
        try:
            # Get top news from Spain
            top_news = await client.top_news(max_results=5)
            print_news_section("Top News from Spain", top_news)

            # Search for AI news in Spanish
            search_results = await client.search(
                "inteligencia artificial",
                when="7d",
                max_results=5,
            )
            print_news_section("AI News Search Results", search_results)

        except Exception as e:
            print(f"Error: {e}")

    async with AsyncGoogleNewsClient(language="en", country="US") as client:
        try:
            # Get technology news
            tech_news = await client.top_news(topic="TECHNOLOGY", max_results=5)
            print_news_section("Technology News", tech_news)

            # Batch search related topics
            batch_results = await client.batch_search(
                ["artificial intelligence", "machine learning"],
                when="7d",
                max_results=3,
            )
            for query, articles in batch_results.items():
                print_news_section(f"Search Results: {query}", articles)

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
