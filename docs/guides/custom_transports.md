# Guide: Custom Transports & Proxies

`GoogleNewsClient` and `AsyncGoogleNewsClient` support enterprise network setups,
including corporate HTTP/HTTPS proxies, custom request headers, retry policies,
and custom `httpx` transports.

## Configuration with `ClientConfig`

You can pass options directly to the client constructor or encapsulate them in
a reusable `ClientConfig`:

```python
from google_news_api import ClientConfig, GoogleNewsClient

# Define production client configuration
config = ClientConfig(
    language="en",
    country="US",
    timeout=20.0,
    max_retries=5,
    retry_backoff=1.5,
    proxy="http://proxy.corp.internal:8080",
    headers={"X-Application-Name": "NewsCrawler/1.0"},
)

# Instantiate client from config
with GoogleNewsClient.from_config(config) as client:
    articles = client.search("market outlook", max_results=5)
```

## Injecting Custom `httpx` Transports

For testing, mock networks, or custom connection poolers, you can inject any
`httpx.BaseTransport` (sync) or `httpx.AsyncBaseTransport` (async):

```python
import httpx
from google_news_api import GoogleNewsClient

# Custom transport with strict connection limits
custom_transport = httpx.HTTPTransport(
    retries=3,
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
)

with GoogleNewsClient(transport=custom_transport) as client:
    articles = client.search("cybersecurity", max_results=5)
```

## Mock Transport for Testing

For unit testing without network calls, inject an `httpx.MockTransport`:

```python
import httpx
from google_news_api import GoogleNewsClient

def mock_feed_handler(request: httpx.Request) -> httpx.Response:
    sample_feed = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Google News</title>
        <item>
          <title>Mocked News Headline</title>
          <link>https://news.google.com/rss/articles/CBMi_test</link>
          <pubDate>Mon, 05 Oct 2026 12:00:00 GMT</pubDate>
          <source url="https://mock.com">Mock Source</source>
        </item>
      </channel>
    </rss>"""
    return httpx.Response(200, text=sample_feed, request=request)

transport = httpx.MockTransport(mock_feed_handler)
with GoogleNewsClient(transport=transport) as client:
    articles = client.search("any query")
    assert articles[0]["title"] == "Mocked News Headline"
```
