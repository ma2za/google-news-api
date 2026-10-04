# API Reference: Types

Strongly typed `TypedDict` structures used across the public interface.

## Article

Base article dictionary returned by standard search and headlines methods.

```python
class Article(TypedDict):
    title: str
    link: str
    published: str
    summary: str
    source: str
    id: Optional[str]
```

---

## EnrichedArticle

Article dictionary augmented with link decoding and body text extraction.

```python
class EnrichedArticle(TypedDict, total=False):
    title: str
    link: str
    published: str
    summary: str
    source: str
    id: Optional[str]
    google_link: str
    text: str
```

---

## NormalizedArticle

Article dictionary augmented with parsed UTC timestamp and publisher domain.

```python
class NormalizedArticle(TypedDict, total=False):
    title: str
    link: str
    published: str
    summary: str
    source: str
    id: Optional[str]
    published_datetime: datetime
    source_domain: str
```

---

## RelatedArticle & ArticleCluster

Structures representing Google News story clusters.

```python
class RelatedArticle(TypedDict):
    title: str
    link: str
    source: str

class ArticleCluster(TypedDict):
    primary: Article
    related: List[RelatedArticle]
```
