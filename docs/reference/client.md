# API Reference: Clients

## GoogleNewsClient

Synchronous client for Google News RSS operations.

```python
class GoogleNewsClient:
    def __init__(
        self,
        language: str = "en",
        country: str = "US",
        requests_per_minute: int = 60,
        cache_ttl: int = 300,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
        proxy: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        transport: Optional[Any] = None,
    ): ...
```

### Methods

- `search(query: str, *, after: Optional[str] = None, before: Optional[str] = None, when: Optional[str] = None, max_results: Optional[int] = None, mode: str = "default") -> List[Article]`
- `top_news(topic: str = "WORLD", *, topic_token: Optional[str] = None, max_results: Optional[int] = None, mode: str = "default") -> List[Article]`
- `top_news_clusters(topic: str = "WORLD", *, topic_token: Optional[str] = None, max_results: Optional[int] = None) -> List[ArticleCluster]`
- `location_news(location: str, *, max_results: Optional[int] = None) -> List[Article]`
- `batch_search(queries: List[str], *, delay: float = 1.0, show_progress: bool = False, mode: str = "default") -> Dict[str, List[Article]]`
- `decode_url(source_url: str, timeout: float = 30.0) -> str`
- `decode_urls(urls: List[str], *, timeout: float = 30.0, delay: float = 1.0, show_progress: bool = False) -> List[Optional[str]]`
- `close() -> None`

---

## AsyncGoogleNewsClient

Asynchronous client for Google News RSS operations.

```python
class AsyncGoogleNewsClient:
    def __init__(
        self,
        language: str = "en",
        country: str = "US",
        requests_per_minute: int = 60,
        cache_ttl: int = 300,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
        proxy: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        transport: Optional[Any] = None,
    ): ...
```

### Methods

- `async search(query: str, *, after: Optional[str] = None, before: Optional[str] = None, when: Optional[str] = None, max_results: Optional[int] = None, mode: str = "default") -> List[Article]`
- `async top_news(topic: str = "WORLD", *, topic_token: Optional[str] = None, max_results: Optional[int] = None, mode: str = "default") -> List[Article]`
- `async top_news_clusters(topic: str = "WORLD", *, topic_token: Optional[str] = None, max_results: Optional[int] = None) -> List[ArticleCluster]`
- `async location_news(location: str, *, max_results: Optional[int] = None) -> List[Article]`
- `async batch_search(queries: List[str], *, max_concurrent: int = 5, timeout: float = 30.0, delay: float = 1.0, show_progress: bool = False, mode: str = "default") -> Dict[str, List[Article]]`
- `async decode_url(source_url: str, timeout: float = 30.0) -> str`
- `async decode_urls(urls: List[str], *, max_concurrent: int = 5, timeout: float = 30.0, delay: float = 1.0, show_progress: bool = False) -> List[Optional[str]]`
- `async aclose() -> None`

---

## Custom Google News Sections (`topic_token`)

In addition to the eight canonical named topics (`WORLD`, `NATION`, `BUSINESS`, `TECHNOLOGY`, `ENTERTAINMENT`, `SPORTS`, `SCIENCE`, `HEALTH`), callers can query specific custom section feeds using the `topic_token` keyword argument.

### Token Acquisition
Google News section tokens are opaque base64-encoded protobuf tokens. Users can acquire them by opening a section in the Google News web interface and copying the token identifier from the URL path:
`https://news.google.com/topics/<TOKEN>`

### Upstream Instability & Named Topic Preference
- **Named topics are preferred for portable applications:** Named topics (`WORLD`, `TECHNOLOGY`, etc.) are canonical, stable across updates, and automatically map to corresponding localized sections across countries and languages.
- **Upstream instability of tokens:** Google News does not guarantee the longevity or structure of arbitrary section tokens. Section tokens may change, expire, or produce empty feeds over time as upstream feeds update.
- **Validation rules:** Empty strings, non-string values, and full URLs passed as `topic_token` are rejected with `ValidationError`. Passing a custom named `topic` together with `topic_token` in the same call is mutually exclusive and raises `ValidationError`.

---

## ClientConfig

Configuration dataclass for instantiating clients.

```python
@dataclass
class ClientConfig:
    language: str = "en"
    country: str = "US"
    requests_per_minute: int = 60
    cache_ttl: int = 300
    timeout: float = 30.0
    max_retries: int = 3
    retry_backoff: float = 2.0
    proxy: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    transport: Optional[Any] = None
```
