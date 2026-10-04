"""Tests for sync and async Google News URL decoding and platform configuration."""

import asyncio
import json
import platform
from typing import Optional

import httpx
import pytest

from google_news_api import (
    AsyncGoogleNewsClient,
    GoogleNewsClient,
    HTTPError,
    ParsingError,
    RateLimitError,
    ValidationError,
)
from google_news_api.client import _get_platform_info

VALID_HTML = """
<!DOCTYPE html>
<html>
<body>
  <c-wiz>
    <div jscontroller="d04e5" data-n-a-sg="test-sig-xyz" data-n-a-ts="1720000000"></div>
  </c-wiz>
</body>
</html>
"""

HTML_NO_CWIZ = """
<!DOCTYPE html>
<html><body><div>No data here</div></body></html>
"""

HTML_MISSING_ATTRS = """
<!DOCTYPE html>
<html>
<body>
  <c-wiz>
    <div jscontroller="d04e5"></div>
  </c-wiz>
</body>
</html>
"""


def _make_batch_response(target_url: str) -> str:
    inner = json.dumps([None, target_url])
    batch_data = [[None, None, inner], None, None]
    return f")]}}'\n\n{json.dumps(batch_data)}"


def _build_mock_transport(
    *,
    splash_status: int = 200,
    splash_html: str = VALID_HTML,
    splash_headers: Optional[dict] = None,
    batch_status: int = 200,
    batch_body: Optional[str] = None,
    batch_headers: Optional[dict] = None,
    fail_transport: bool = False,
):
    if batch_body is None:
        batch_body = _make_batch_response("https://destination-news.com/article/42")

    def handler(request: httpx.Request) -> httpx.Response:
        if fail_transport:
            raise httpx.ConnectError("Network failure", request=request)

        url_str = str(request.url)
        if "batchexecute" in url_str:
            return httpx.Response(
                status_code=batch_status,
                text=batch_body,
                headers=batch_headers or {"Content-Type": "text/plain"},
                request=request,
            )
        else:
            return httpx.Response(
                status_code=splash_status,
                text=splash_html,
                headers=splash_headers or {"Content-Type": "text/html"},
                request=request,
            )

    return httpx.MockTransport(handler)


# -----------------------------------------------------------------------------
# Platform info tests
# -----------------------------------------------------------------------------


def test_platform_info_windows(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    assert _get_platform_info() == "Windows NT 10.0; Win64; x64"


def test_platform_info_darwin(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    assert _get_platform_info() == "Macintosh; Intel Mac OS X 10_15_7"


def test_platform_info_linux(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    assert _get_platform_info() == "X11; Linux x86_64"


# -----------------------------------------------------------------------------
# Sync decode_url tests
# -----------------------------------------------------------------------------


def test_sync_decode_url_success():
    transport = _build_mock_transport()
    client = GoogleNewsClient(transport=transport)
    source_url = "https://news.google.com/rss/articles/CBMi_test_token"
    decoded = client.decode_url(source_url)
    assert decoded == "https://destination-news.com/article/42"


def test_sync_decode_url_validation_errors():
    client = GoogleNewsClient()
    with pytest.raises(ValidationError) as exc:
        client.decode_url("not-a-url")
    assert "URL must be a Google News article URL" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        client.decode_url("https://othersite.com/rss/articles/abc")
    assert "URL must be a Google News article URL" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        client.decode_url("https://news.google.com/articles/short")
    assert "Invalid Google News URL format" in str(exc.value)


def test_sync_decode_url_429_rate_limit():
    transport = _build_mock_transport(
        splash_status=429, splash_headers={"Retry-After": "45"}
    )
    client = GoogleNewsClient(transport=transport)
    with pytest.raises(RateLimitError) as exc:
        client.decode_url("https://news.google.com/rss/articles/CBMi_test")
    assert exc.value.retry_after == 45.0


def test_sync_decode_url_splash_http_error():
    transport = _build_mock_transport(splash_status=500)
    client = GoogleNewsClient(transport=transport)
    with pytest.raises(HTTPError) as exc:
        client.decode_url("https://news.google.com/rss/articles/CBMi_test")
    assert exc.value.status_code == 500


def test_sync_decode_url_missing_cwiz():
    transport = _build_mock_transport(splash_html=HTML_NO_CWIZ)
    client = GoogleNewsClient(transport=transport)
    with pytest.raises(ParsingError) as exc:
        client.decode_url("https://news.google.com/rss/articles/CBMi_test")
    assert "Could not find required data element" in str(exc.value)


def test_sync_decode_url_missing_attributes():
    transport = _build_mock_transport(splash_html=HTML_MISSING_ATTRS)
    client = GoogleNewsClient(transport=transport)
    with pytest.raises(ParsingError) as exc:
        client.decode_url("https://news.google.com/rss/articles/CBMi_test")
    assert "Missing required attributes in response" in str(exc.value)


def test_sync_decode_url_batch_http_error():
    transport = _build_mock_transport(batch_status=503)
    client = GoogleNewsClient(transport=transport)
    with pytest.raises(HTTPError) as exc:
        client.decode_url("https://news.google.com/rss/articles/CBMi_test")
    assert exc.value.status_code == 503


def test_sync_decode_url_batch_malformed_json():
    transport = _build_mock_transport(batch_body=")]}'\n\nnot-json")
    client = GoogleNewsClient(transport=transport)
    with pytest.raises(ParsingError) as exc:
        client.decode_url("https://news.google.com/rss/articles/CBMi_test")
    assert "Failed to parse decoded URL" in str(exc.value)


def test_sync_decode_url_unexpected_exception_fallback(monkeypatch):
    client = GoogleNewsClient()

    def raise_runtime(*args, **kwargs):
        raise RuntimeError("Unexpected boom")

    monkeypatch.setattr(client._client, "get", raise_runtime)
    url = "https://news.google.com/rss/articles/CBMi_test"
    result = client.decode_url(url)
    assert result == url


def test_sync_decode_urls_empty_and_validation():
    client = GoogleNewsClient()
    assert client.decode_urls([]) == []

    with pytest.raises(ValidationError) as exc:
        client.decode_urls("not-a-list")
    assert "urls must be a list of strings" in str(exc.value)


def test_sync_decode_urls_mixed_results():
    valid_url = "https://news.google.com/rss/articles/CBMi_valid"
    bad_url = "https://news.google.com/invalid"
    boom_url = "https://news.google.com/rss/articles/CBMi_boom"

    def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "CBMi_boom" in url_str:
            return httpx.Response(500, request=request)
        if "batchexecute" in url_str:
            return httpx.Response(
                200, text=_make_batch_response("https://ok.com/1"), request=request
            )
        return httpx.Response(200, text=VALID_HTML, request=request)

    client = GoogleNewsClient(transport=httpx.MockTransport(handler))
    results = client.decode_urls(
        [valid_url, bad_url, boom_url], delay=0, show_progress=True
    )
    assert results == ["https://ok.com/1", None, None]


# -----------------------------------------------------------------------------
# Async decode_url tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_decode_url_success():
    transport = _build_mock_transport()
    async with AsyncGoogleNewsClient(transport=transport) as client:
        source_url = "https://news.google.com/rss/articles/CBMi_test_token"
        decoded = await client.decode_url(source_url)
        assert decoded == "https://destination-news.com/article/42"


@pytest.mark.asyncio
async def test_async_decode_url_validation_errors():
    async with AsyncGoogleNewsClient() as client:
        with pytest.raises(ValidationError) as exc:
            await client.decode_url("not-a-url")
        assert "URL must be a Google News article URL" in str(exc.value)

        with pytest.raises(ValidationError) as exc:
            await client.decode_url("https://othersite.com/rss/articles/abc")
        assert "URL must be a Google News article URL" in str(exc.value)

        with pytest.raises(ValidationError) as exc:
            await client.decode_url("https://news.google.com/articles/short")
        assert "Invalid Google News URL format" in str(exc.value)


@pytest.mark.asyncio
async def test_async_decode_url_429_rate_limit():
    transport = _build_mock_transport(
        splash_status=429, splash_headers={"Retry-After": "30"}
    )
    async with AsyncGoogleNewsClient(transport=transport) as client:
        with pytest.raises(RateLimitError) as exc:
            await client.decode_url("https://news.google.com/rss/articles/CBMi_test")
        assert exc.value.retry_after == 30.0


@pytest.mark.asyncio
async def test_async_decode_url_splash_http_error():
    transport = _build_mock_transport(splash_status=502)
    async with AsyncGoogleNewsClient(transport=transport) as client:
        with pytest.raises(HTTPError) as exc:
            await client.decode_url("https://news.google.com/rss/articles/CBMi_test")
        assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_async_decode_url_missing_cwiz():
    transport = _build_mock_transport(splash_html=HTML_NO_CWIZ)
    async with AsyncGoogleNewsClient(transport=transport) as client:
        with pytest.raises(ParsingError) as exc:
            await client.decode_url("https://news.google.com/rss/articles/CBMi_test")
        assert "Could not find required data element" in str(exc.value)


@pytest.mark.asyncio
async def test_async_decode_url_missing_attributes():
    transport = _build_mock_transport(splash_html=HTML_MISSING_ATTRS)
    async with AsyncGoogleNewsClient(transport=transport) as client:
        with pytest.raises(ParsingError) as exc:
            await client.decode_url("https://news.google.com/rss/articles/CBMi_test")
        assert "Missing required attributes in response" in str(exc.value)


@pytest.mark.asyncio
async def test_async_decode_url_batch_http_error():
    transport = _build_mock_transport(batch_status=500)
    async with AsyncGoogleNewsClient(transport=transport) as client:
        with pytest.raises(HTTPError) as exc:
            await client.decode_url("https://news.google.com/rss/articles/CBMi_test")
        assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_async_decode_url_batch_malformed_json():
    transport = _build_mock_transport(batch_body=")]}'\n\nnot-valid-json")
    async with AsyncGoogleNewsClient(transport=transport) as client:
        with pytest.raises(ParsingError) as exc:
            await client.decode_url("https://news.google.com/rss/articles/CBMi_test")
        assert "Failed to parse decoded URL" in str(exc.value)


@pytest.mark.asyncio
async def test_async_decode_url_unexpected_exception_fallback(monkeypatch):
    async with AsyncGoogleNewsClient() as client:

        async def raise_runtime(*args, **kwargs):
            raise RuntimeError("Unexpected async boom")

        monkeypatch.setattr(client.client, "get", raise_runtime)
        url = "https://news.google.com/rss/articles/CBMi_test"
        result = await client.decode_url(url)
        assert result == url


@pytest.mark.asyncio
async def test_async_decode_urls_empty_and_validation():
    async with AsyncGoogleNewsClient() as client:
        assert await client.decode_urls([]) == []

        with pytest.raises(ValidationError) as exc:
            await client.decode_urls("not-a-list")
        assert "urls must be a list of strings" in str(exc.value)


@pytest.mark.asyncio
async def test_async_decode_urls_mixed_results():
    valid_url = "https://news.google.com/rss/articles/CBMi_valid"
    bad_url = "https://news.google.com/invalid"
    boom_url = "https://news.google.com/rss/articles/CBMi_boom"

    def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "CBMi_boom" in url_str:
            return httpx.Response(500, request=request)
        if "batchexecute" in url_str:
            return httpx.Response(
                200, text=_make_batch_response("https://ok.com/2"), request=request
            )
        return httpx.Response(200, text=VALID_HTML, request=request)

    async with AsyncGoogleNewsClient(transport=httpx.MockTransport(handler)) as client:
        results = await client.decode_urls(
            [valid_url, bad_url, boom_url], delay=0, show_progress=True
        )
        assert results == ["https://ok.com/2", None, None]


@pytest.mark.asyncio
async def test_async_decode_urls_concurrency():
    concurrent_requests = 0
    max_observed_concurrent = 0
    lock = asyncio.Lock()

    def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "batchexecute" in url_str:
            return httpx.Response(
                200, text=_make_batch_response("https://ok.com/fast"), request=request
            )
        return httpx.Response(200, text=VALID_HTML, request=request)

    async with AsyncGoogleNewsClient(transport=httpx.MockTransport(handler)) as client:
        # Wrap decode_url to track concurrency
        original_decode_url = client.decode_url

        async def tracked_decode_url(url, timeout=30.0):
            nonlocal concurrent_requests, max_observed_concurrent
            async with lock:
                concurrent_requests += 1
                if concurrent_requests > max_observed_concurrent:
                    max_observed_concurrent = concurrent_requests
            try:
                await asyncio.sleep(0.02)
                return await original_decode_url(url, timeout)
            finally:
                async with lock:
                    concurrent_requests -= 1

        client.decode_url = tracked_decode_url
        urls = [f"https://news.google.com/rss/articles/CBMi_{i}" for i in range(8)]
        results = await client.decode_urls(urls, max_concurrent=2, delay=0)

        assert len(results) == 8
        assert all(r == "https://ok.com/fast" for r in results)
        assert max_observed_concurrent <= 2
