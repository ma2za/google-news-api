# Guide: Geographic Headlines

Google News provides localized news sections for specific cities, regions, and
territories. Use `location_news` to retrieve geographic headlines.

## Querying Local News

`location_news` accepts a city or geographic area name:

```python
from google_news_api import GoogleNewsClient

with GoogleNewsClient(language="en", country="US") as client:
    # Query city news
    articles = client.location_news("Chicago", max_results=5)
    print(f"Found {len(articles)} articles for Chicago:")
    for article in articles:
        print(f"- {article['title']} ({article['source']})")
```

## Async Geographic News

`AsyncGoogleNewsClient.location_news` offers an identical asynchronous interface:

```python
import asyncio
from google_news_api import AsyncGoogleNewsClient

async def get_local_news():
    async with AsyncGoogleNewsClient(language="ro", country="RO") as client:
        articles = await client.location_news("Bucharest", max_results=5)
        for article in articles:
            print(f"[{article['source']}] {article['title']}")

if __name__ == "__main__":
    asyncio.run(get_local_news())
```

## CLI Usage

Geographic headlines can also be fetched directly via the CLI:

```bash
# JSON output for local news
google-news location "Seattle" --max-results 5 --format json

# Human-readable table
google-news location "London" --country GB --language en --format table
```

## Validation Constraints

- `location` must be a non-empty string. Passing empty, whitespace-only, or
  non-string values raises `ValidationError(field="location")`.
- City names containing special characters or spaces are automatically URL-encoded.
