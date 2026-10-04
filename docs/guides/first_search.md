# Guide: First Search

This guide covers basic search and top news retrieval using both synchronous and
asynchronous clients.

## Synchronous Search

The synchronous `GoogleNewsClient` is ideal for scripts, data analysis notebooks,
and CLI utilities.

```python
from google_news_api import GoogleNewsClient

# Initialize client for US English news
with GoogleNewsClient(language="en", country="US") as client:
    # Basic keyword search
    articles = client.search("artificial intelligence", max_results=5)
    for article in articles:
        print(f"[{article['source']}] {article['title']}")
        print(f"  Link: {article['link']}")
        print(f"  Date: {article['published']}")

    # Top headlines for a curated topic (e.g., TECHNOLOGY, BUSINESS, WORLD)
    tech_news = client.top_news(topic="TECHNOLOGY", max_results=3)
    for article in tech_news:
        print(f"Headline: {article['title']}")
```

## Asynchronous Search

For high-throughput applications, web services, or data pipelines, use
`AsyncGoogleNewsClient`.

```python
import asyncio
from google_news_api import AsyncGoogleNewsClient

async def main():
    async with AsyncGoogleNewsClient(language="en", country="US") as client:
        # Search asynchronously
        articles = await client.search("climate tech", max_results=5)
        for article in articles:
            print(f"- {article['title']} ({article['source']})")

        # Top news clusters with primary and related stories
        clusters = await client.top_news_clusters("BUSINESS", max_results=3)
        for cluster in clusters:
            primary = cluster["primary"]
            print(f"Main story: {primary['title']}")
            print(f"Related coverage: {len(cluster['related'])} sources")

if __name__ == "__main__":
    asyncio.run(main())
```

## Article Data Model

Every search and headline method returns a list of dictionaries with guaranteed
canonical keys:

- `title`: Article headline string.
- `link`: Google News redirect URL.
- `published`: RFC 822 publication date string (e.g. `Mon, 05 Oct 2026 12:00:00 GMT`).
- `summary`: Short summary or snippet provided in the feed.
- `source`: Publisher name string.
- `id`: Stable unique identifier parsed from the Google News entry.
