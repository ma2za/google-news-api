"""Tests verifying API and behavioral parity between sync and async clients."""

import inspect
from typing import Any, Dict

import httpx
import pytest

from google_news_api import (
    AsyncGoogleNewsClient,
    GoogleNewsClient,
    ValidationError,
)

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Google News</title>
    <link>https://news.google.com</link>
    <item>
      <title>Parity Article Title - Test News</title>
      <link>https://news.google.com/rss/articles/CBMi_parity_id</link>
      <pubDate>Mon, 05 Oct 2026 10:00:00 GMT</pubDate>
      <description>&lt;a href="https://news.google.com/rss/articles/CBMi_parity_id"&gt;Parity Article Title&lt;/a&gt;&amp;nbsp;&amp;nbsp;&lt;font color="#6f6f6f"&gt;Test News&lt;/font&gt;&lt;ol&gt;&lt;li&gt;&lt;a href="https://news.google.com/rss/articles/CBMi_related_1"&gt;Related Story One&lt;/a&gt;&amp;nbsp;&amp;nbsp;&lt;font color="#6f6f6f"&gt;Related Source&lt;/font&gt;&lt;/li&gt;&lt;/ol&gt;</description>  # noqa: E501
      <source url="https://testnews.com">Test News</source>
    </item>
  </channel>
</rss>
"""


def _get_sig_dict(callable_obj) -> Dict[str, inspect.Parameter]:
    return inspect.signature(callable_obj).parameters


def _make_rss_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=SAMPLE_RSS, request=request)

    return httpx.MockTransport(handler)


# -----------------------------------------------------------------------------
# Method Inventory and Signature Parity
# -----------------------------------------------------------------------------


def test_client_method_inventory_parity():
    sync_methods = {
        name
        for name, member in inspect.getmembers(
            GoogleNewsClient, predicate=inspect.isfunction
        )
        if not name.startswith("_") and name not in {"close"}
    }
    async_methods = {
        name
        for name, member in inspect.getmembers(
            AsyncGoogleNewsClient, predicate=inspect.isfunction
        )
        if not name.startswith("_") and name not in {"aclose"}
    }

    assert sync_methods == async_methods
    expected_public_methods = {
        "search",
        "top_news",
        "top_news_clusters",
        "location_news",
        "batch_search",
        "decode_url",
        "decode_urls",
    }
    assert sync_methods == expected_public_methods


@pytest.mark.parametrize(
    "method_name",
    [
        "search",
        "top_news",
        "top_news_clusters",
        "location_news",
        "decode_url",
    ],
)
def test_method_signature_exact_parity(method_name):
    sync_sig = _get_sig_dict(getattr(GoogleNewsClient, method_name))
    async_sig = _get_sig_dict(getattr(AsyncGoogleNewsClient, method_name))

    assert list(sync_sig.keys()) == list(async_sig.keys())
    for param_name, sync_param in sync_sig.items():
        async_param = async_sig[param_name]
        assert (
            sync_param.kind == async_param.kind
        ), f"Parameter kind mismatch on {method_name}.{param_name}"
        assert (
            sync_param.default == async_param.default
        ), f"Default mismatch on {method_name}.{param_name}"


def test_batch_search_signature_parity():
    sync_params = _get_sig_dict(GoogleNewsClient.batch_search)
    async_params = _get_sig_dict(AsyncGoogleNewsClient.batch_search)

    # Async has documented concurrency controls:
    # max_concurrent, timeout, delay, show_progress
    async_specific = {"max_concurrent", "timeout", "delay", "show_progress"}
    shared_keys = [k for k in async_params if k not in async_specific]
    assert list(sync_params.keys()) == shared_keys

    for k in sync_params:
        assert sync_params[k].kind == async_params[k].kind
        assert sync_params[k].default == async_params[k].default


def test_decode_urls_signature_parity():
    sync_params = _get_sig_dict(GoogleNewsClient.decode_urls)
    async_params = _get_sig_dict(AsyncGoogleNewsClient.decode_urls)

    # Async adds max_concurrent
    async_specific = {"max_concurrent"}
    shared_keys = [k for k in async_params if k not in async_specific]
    assert list(sync_params.keys()) == shared_keys

    for k in sync_params:
        assert sync_params[k].kind == async_params[k].kind
        assert sync_params[k].default == async_params[k].default


# -----------------------------------------------------------------------------
# Input Validation Parity
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_location",
    ["", "   ", None, 123],
)
async def test_location_news_validation_parity(bad_location: Any):
    client = GoogleNewsClient()
    with pytest.raises(ValidationError) as sync_exc:
        client.location_news(bad_location)  # type: ignore

    async with AsyncGoogleNewsClient() as async_client:
        with pytest.raises(ValidationError) as async_exc:
            await async_client.location_news(bad_location)  # type: ignore

    assert sync_exc.value.field == "location"
    assert async_exc.value.field == "location"
    assert "location must be a non-empty string" in str(sync_exc.value)
    assert "location must be a non-empty string" in str(async_exc.value)


@pytest.mark.asyncio
async def test_top_news_invalid_topic_parity():
    client = GoogleNewsClient()
    with pytest.raises(ValidationError) as sync_exc:
        client.top_news("INVALID_TOPIC_NAME")

    async with AsyncGoogleNewsClient() as async_client:
        with pytest.raises(ValidationError) as async_exc:
            await async_client.top_news("INVALID_TOPIC_NAME")

    assert sync_exc.value.field == "topic"
    assert async_exc.value.field == "topic"


@pytest.mark.asyncio
async def test_search_invalid_mode_parity():
    client = GoogleNewsClient()
    with pytest.raises(ValidationError) as sync_exc:
        client.search("python", mode="nonexistent_mode")

    async with AsyncGoogleNewsClient() as async_client:
        with pytest.raises(ValidationError) as async_exc:
            await async_client.search("python", mode="nonexistent_mode")

    assert sync_exc.value.field == "mode"
    assert async_exc.value.field == "mode"


@pytest.mark.asyncio
async def test_batch_search_validation_parity():
    client = GoogleNewsClient()
    with pytest.raises(ValidationError) as sync_exc:
        client.batch_search("not-a-list")  # type: ignore

    async with AsyncGoogleNewsClient() as async_client:
        with pytest.raises(ValidationError) as async_exc:
            await async_client.batch_search("not-a-list")  # type: ignore

    assert sync_exc.value.field == "queries"
    assert async_exc.value.field == "queries"
    assert client.batch_search([]) == {}
    assert await async_client.batch_search([]) == {}


# -----------------------------------------------------------------------------
# Execution & Result Output Parity
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_result_output_parity():
    transport = _make_rss_transport()
    sync_client = GoogleNewsClient(transport=transport)
    sync_res = sync_client.search("ai tech")

    async with AsyncGoogleNewsClient(transport=transport) as async_client:
        async_res = await async_client.search("ai tech")

    assert len(sync_res) == len(async_res) == 1
    assert sync_res[0] == async_res[0]
    expected_keys = ("title", "link", "published", "summary", "source", "id")
    assert tuple(sync_res[0].keys()) == expected_keys


@pytest.mark.asyncio
async def test_top_news_clusters_output_parity():
    transport = _make_rss_transport()
    sync_client = GoogleNewsClient(transport=transport)
    sync_clusters = sync_client.top_news_clusters("WORLD")

    async with AsyncGoogleNewsClient(transport=transport) as async_client:
        async_clusters = await async_client.top_news_clusters("WORLD")

    assert len(sync_clusters) == len(async_clusters) == 1
    assert sync_clusters[0] == async_clusters[0]
    assert "primary" in sync_clusters[0]
    assert "related" in sync_clusters[0]
    assert len(sync_clusters[0]["related"]) == 1


@pytest.mark.asyncio
async def test_location_news_output_parity():
    transport = _make_rss_transport()
    sync_client = GoogleNewsClient(transport=transport)
    sync_articles = sync_client.location_news("Tokyo")

    async with AsyncGoogleNewsClient(transport=transport) as async_client:
        async_articles = await async_client.location_news("Tokyo")

    assert sync_articles == async_articles
    assert len(sync_articles) == 1
    assert sync_articles[0]["title"] == "Parity Article Title - Test News"
