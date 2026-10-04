# Guide: Clean Dataset Export

When processing news for machine learning datasets, sentiment models, or
reporting databases, raw RSS feeds require deduplication, timestamp normalization,
and clean domain resolution.

## Normalizing and Enriching Articles

The top-level `normalize_articles` utility processes raw feed dictionaries into
strongly-typed `NormalizedArticle` objects:

```python
from google_news_api import (
    GoogleNewsClient,
    deduplicate_articles,
    normalize_articles,
    sort_articles,
)

with GoogleNewsClient() as client:
    raw_articles = client.search("renewable infrastructure", max_results=20)

    # 1. Normalize dates into UTC datetimes and extract publisher source_domain
    normalized = normalize_articles(raw_articles)

    # 2. Deduplicate identical stories across syndicated feeds
    unique = deduplicate_articles(normalized, by="title")

    # 3. Sort chronologically (newest first)
    sorted_articles = sort_articles(unique, newest_first=True)

    for article in sorted_articles[:5]:
        print(f"Title: {article['title']}")
        if "source_domain" in article:
            print(f"  Domain: {article['source_domain']}")
        if "published_datetime" in article:
            print(f"  Datetime (UTC): {article['published_datetime']}")
```

## Exporting via CLI

The CLI provides built-in formats for piping clean data to downstream analytics
tools:

```bash
# Export JSON array to a file
google-news search "biotech discoveries" --max-results 50 --format json > articles.json

# Export CSV format
google-news search "electric vehicles" --max-results 50 --format csv > ev_news.csv

# Render formatted terminal table
google-news top-news --topic BUSINESS --max-results 10 --format table
```
