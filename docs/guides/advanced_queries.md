# Guide: Advanced Queries

`google-news-api` supports complex search syntax including Boolean operators,
exact phrase matches, site domain scoping, and date-range filters.

## Using `NewsQuery` Builder

`NewsQuery` provides a fluent interface for building query strings with correct
escaping and operator formatting:

```python
from google_news_api import GoogleNewsClient, NewsQuery

# Build an advanced query using NewsQuery
query = NewsQuery(
    text="solar",
    exact_phrase="clean energy",
    exclude_words=["subsidies"],
    in_title="breakthrough",
).build()

print(f"Generated query: {query}")
# Output: solar "clean energy" -subsidies intitle:"breakthrough"

with GoogleNewsClient() as client:
    articles = client.search(query, max_results=5)
    for article in articles:
        print(f"- {article['title']}")
```

## Boolean Logic & Search Operators

Direct query strings support Google News search operators:

- **Exact Match (`"..."`):** `"semiconductor shortage"`
- **Logical OR (`OR`):** `apple OR microsoft OR google`
- **Exclusion (`-`):** `python -snake -reptile`
- **Site Domain (`site:...`):** `site:nature.com physics`
- **Title Scoping (`intitle:...`):** `intitle:"breakthrough"`

## Date-Based Filtering

You can pass temporal constraints directly to `client.search()` or embed them in
the query:

```python
from google_news_api import GoogleNewsClient

with GoogleNewsClient() as client:
    # 1. Relative time windows: "1h", "24h", "7d", "1y"
    recent = client.search("space launch", when="24h")

    # 2. Absolute date boundaries (YYYY-MM-DD): max 100 results per Google limits
    dated = client.search(
        "nobel prize",
        after="2026-01-01",
        before="2026-10-01",
    )
    print(f"Historical articles: {len(dated)}")
```
