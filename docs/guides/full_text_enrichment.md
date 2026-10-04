# Guide: Full-Text Enrichment

Google News RSS feeds provide redirects (`https://news.google.com/rss/articles/...`)
rather than original publisher URLs. `ArticleEnricher` decodes Google News links
into real publisher URLs and optionally downloads the full article text.

## Optional Dependency Installation

Full-text extraction requires the `extract` extra:

```bash
pip install "google-news-api[extract]"
```

## Synchronous Enrichment

```python
from google_news_api import ArticleEnricher, GoogleNewsClient

with GoogleNewsClient() as client:
    # 1. Fetch search results
    raw_articles = client.search("aerospace engineering", max_results=3)

    # 2. Enrich with decoded publisher URLs and extracted full text
    enricher = ArticleEnricher(client=client, max_concurrent=3, delay=0.5)
    enriched = enricher.enrich(
        raw_articles,
        decode_links=True,
        extract_text=True,
    )

    for article in enriched:
        print(f"Title: {article['title']}")
        print(f"  Publisher URL: {article['link']}")
        print(f"  Google Redirect: {article.get('google_link')}")
        if "text" in article:
            print(f"  Body length: {len(article['text'])} characters")
```

## Asynchronous Enrichment

For async applications, `AsyncArticleEnricher` coordinates decoding and text
extraction concurrently:

```python
import asyncio
from google_news_api import AsyncArticleEnricher, AsyncGoogleNewsClient

async def run_enrichment():
    async with AsyncGoogleNewsClient() as client:
        articles = await client.search("neuroscience breakthroughs", max_results=3)

        enricher = AsyncArticleEnricher(client=client, max_concurrent=3, delay=0.2)
        enriched = await enricher.enrich(
            articles,
            decode_links=True,
            extract_text=True,
        )

        for article in enriched:
            print(f"Decoded: {article['link']}")
            if article.get("text"):
                print(f"Preview: {article['text'][:120]}...\n")

if __name__ == "__main__":
    asyncio.run(run_enrichment())
```

## URL Decoding Only

If you only need real publisher URLs without downloading full article bodies,
pass `extract_text=False`:

```python
with GoogleNewsClient() as client:
    articles = client.search("robotics", max_results=5)
    enricher = ArticleEnricher(client=client)
    decoded_articles = enricher.enrich(articles, decode_links=True, extract_text=False)
```
