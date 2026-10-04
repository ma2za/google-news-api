# Guide: Async Batch Research

When analyzing multiple topics, competitors, or research queries simultaneously,
`AsyncGoogleNewsClient.batch_search` processes queries concurrently with
tunable throttling and rate limits.

## Concurrent Batch Querying

```python
import asyncio
from google_news_api import AsyncGoogleNewsClient

async def run_batch():
    queries = [
        "autonomous driving",
        "solid state batteries",
        "quantum computing",
        "fusion energy",
    ]

    async with AsyncGoogleNewsClient(language="en", country="US") as client:
        # Execute with a maximum of 2 concurrent HTTP workers and 0.5s inter-request delay
        results = await client.batch_search(
            queries,
            max_concurrent=2,
            delay=0.5,
            show_progress=True,
        )

        for query, articles in results.items():
            print(f"\n--- Results for: {query} ({len(articles)} articles) ---")
            for article in articles[:3]:
                print(f"  • {article['title']}")

if __name__ == "__main__":
    asyncio.run(run_batch())
```

## Batch Parameter Reference

- `queries` (`List[str]`): List of search query strings.
- `max_concurrent` (`int`, default: `5`): Maximum number of concurrent tasks.
- `delay` (`float`, default: `1.0`): Pause in seconds between task dispatches to prevent rate-limiting.
- `timeout` (`float`, default: `30.0`): Per-request HTTP timeout in seconds.
- `show_progress` (`bool`, default: `False`): Displays a terminal progress bar via `tqdm`.

## Synchronous Batch Alternative

For single-threaded environments, `GoogleNewsClient.batch_search` executes queries
sequentially while respecting the in-memory cache:

```python
from google_news_api import GoogleNewsClient

with GoogleNewsClient() as client:
    results = client.batch_search(["spacex", "blue origin"], delay=1.0)
    for q, arts in results.items():
        print(f"{q}: {len(arts)} articles found")
```
