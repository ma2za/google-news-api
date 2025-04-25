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
        if "published_at" in article:
            print(f"Published: {article['published_at']}")
        print("-" * len(title))


async def main():
    """Execute the main async function to demonstrate Google News API usage."""
    # Initialize the client with Spanish language and Spain as country
    async with AsyncGoogleNewsClient(language="es", country="ES") as client:
        try:
            # Get top news from Spain
            top_news = await client.get_top_news()
            print_news_section("Top News from Spain", top_news)

            # Switch to English/US for technology news
            client.language = "en"
            client.country = "US"

            # Get technology news
            tech_news = await client.get_topic_news("TECHNOLOGY")
            print_news_section("Technology News", tech_news)

            # Search for AI news
            search_results = await client.search("artificial intelligence")
            print_news_section("AI News Search Results", search_results)

            # Get available sources
            sources = await client.get_sources()
            print("\nAvailable Sources:")
            print("-----------------")
            for source in sources:
                print(f"Name: {source['name']}")
                print(f"URL: {source['url']}")
                print(f"Language: {source['language']}")
                print(f"Country: {source['country']}")
                print("-----------------")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
