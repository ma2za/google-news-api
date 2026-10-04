# Guide: Incremental Monitoring

For scheduled crawlers, alerting bots, and event-driven feeds, `ArticleTracker`
maintains persistent state across runs so you only process unseen articles.

## Persistent Monitoring with `ArticleTracker`

`ArticleTracker` saves seen article IDs/hashes to disk atomically:

```python
from google_news_api import GoogleNewsClient
from google_news_api.monitor import ArticleTracker

tracker = ArticleTracker("state/seen_articles.json")

with GoogleNewsClient() as client:
    # Query feed
    articles = client.search("critical infrastructure cyberattack")

    # Filter out articles seen in prior runs
    new_articles = tracker.filter_new(
        articles,
        fingerprint="cyberattack_feed_v1",
        emit_existing=False,  # On first run, seeds state without emitting
    )

    print(f"Discovered {len(new_articles)} new stories:")
    for article in new_articles:
        print(f"• {article['title']}")
```

## Scheduled Watch via CLI

The CLI provides a continuous watch command with configurable intervals:

```bash
# Poll every 60 seconds and print newly published articles as JSON lines
google-news watch --query "space exploration" --interval 60 --state-file ./watch.json
```

## Atomic State Guarantees

- **Crash Safety:** State writes use temporary file creation and atomic replacement (`os.replace`) to prevent state corruption during process interruption.
- **Bounded Retention:** Keeps up to `max_seen=10_000` (configurable) most recent article identities to prevent unbounded state file growth.
- **Fingerprint Protection:** Guarantees that if query parameters or fingerprints change, state mismatch errors are raised instead of corrupting deduplication sets.
