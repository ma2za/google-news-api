# API Reference: Exceptions

Hierarchy of exception classes raised by `google-news-api`.

```
GoogleNewsError (base class)
├── ValidationError
├── HTTPError
├── RateLimitError
├── ParsingError
└── ConfigurationError
```

## GoogleNewsError

```python
class GoogleNewsError(Exception):
    def __init__(self, message: str): ...
```
Base exception for all domain errors raised by the package.

---

## ValidationError

```python
class ValidationError(GoogleNewsError):
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
    ): ...
```
Raised when arguments, query options, or URLs fail validation. Includes `field`
and `value` attributes.

---

## HTTPError

```python
class HTTPError(GoogleNewsError):
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Any] = None,
    ): ...
```
Raised when upstream HTTP requests fail or return error status codes.

---

## RateLimitError

```python
class RateLimitError(GoogleNewsError):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float = 60.0,
    ): ...
```
Raised when HTTP 429 Too Many Requests is encountered. `retry_after` contains
the parsed backoff time in seconds (supporting both numeric and RFC 9110 HTTP-date
values).

---

## ParsingError

```python
class ParsingError(GoogleNewsError):
    def __init__(
        self,
        message: str,
        data: Optional[Any] = None,
    ): ...
```
Raised when an RSS feed or URL decoding response fails structural parsing.

---

## ConfigurationError

```python
class ConfigurationError(GoogleNewsError):
    def __init__(self, message: str): ...
```
Raised when invalid client options or conflicting network parameters are supplied.
