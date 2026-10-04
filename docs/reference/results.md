# API Reference: Result Utilities

Top-level functions for post-processing and normalizing article dictionaries.

## normalize_article

```python
def normalize_article(article: Article) -> NormalizedArticle: ...
```

Adds `published_datetime` (parsed UTC `datetime`) and `source_domain` (extracted
publisher hostname) to an article dictionary without mutating the original dictionary.

---

## normalize_articles

```python
def normalize_articles(articles: Iterable[Article]) -> List[NormalizedArticle]: ...
```

Normalizes an iterable of article dictionaries without mutating input dictionaries.

---

## deduplicate_articles

```python
def deduplicate_articles(
    articles: Iterable[Article],
    *,
    by: str = "id",
) -> List[Article]: ...
```

Stably deduplicates articles, preserving the first observed occurrence.
`by` must be one of `"id"`, `"link"`, or `"title"`. Falls back gracefully if the
primary key is missing.

---

## sort_articles

```python
def sort_articles(
    articles: Iterable[Article],
    *,
    newest_first: bool = True,
) -> List[Article]: ...
```

Stably sorts articles chronologically by their published date. Articles with
unparseable or missing publication dates are placed at the end regardless of
sort direction.

---

## parse_published

```python
def parse_published(value: Optional[str]) -> Optional[datetime]: ...
```

Parses an RFC 2822 publication date string into a timezone-aware UTC datetime.
Returns `None` if the input is empty or invalid.

---

## source_domain

```python
def source_domain(article: Mapping[str, Any]) -> Optional[str]: ...
```

Extracts the publisher hostname from an article's `link`. Returns `None` if the
link is missing or remains an undecoded Google News redirect.
