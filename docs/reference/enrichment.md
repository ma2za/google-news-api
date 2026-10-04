# API Reference: Enrichment

## ArticleEnricher

Synchronous pipeline for Google News URL decoding and optional full-text extraction.

```python
class ArticleEnricher:
    def __init__(
        self,
        client: GoogleNewsClient,
        *,
        max_concurrent: int = 5,
        timeout: float = 30.0,
        delay: float = 1.0,
    ): ...

    def enrich(
        self,
        articles: Iterable[Article],
        *,
        decode_links: bool = True,
        extract_text: bool = False,
    ) -> List[EnrichedArticle]: ...
```

---

## AsyncArticleEnricher

Asynchronous pipeline for Google News URL decoding and optional full-text extraction.

```python
class AsyncArticleEnricher:
    def __init__(
        self,
        client: AsyncGoogleNewsClient,
        *,
        max_concurrent: int = 5,
        timeout: float = 30.0,
        delay: float = 1.0,
    ): ...

    async def enrich(
        self,
        articles: Iterable[Article],
        *,
        decode_links: bool = True,
        extract_text: bool = False,
    ) -> List[EnrichedArticle]: ...
```

### Optional Dependencies

Full-text extraction requires Trafilatura:
```bash
pip install "google-news-api[extract]"
```
If `extract_text=True` is requested without the dependency installed, a `RuntimeError`
is raised directing the user to install the extra.
