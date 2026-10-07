"""Tests for Google News custom section tokens (Release 0.1.1)."""

from pathlib import Path

import httpx
import pytest

from google_news_api import (
    AsyncGoogleNewsClient,
    GoogleNewsClient,
    ValidationError,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
EN_US_XML = (FIXTURES_DIR / "topic_token_en_us.xml").read_text(encoding="utf-8")
IT_IT_XML = (FIXTURES_DIR / "topic_token_it_it.xml").read_text(encoding="utf-8")


# -----------------------------------------------------------------------------
# Exact URL Construction & Encoding Tests
# -----------------------------------------------------------------------------


def test_named_topic_exact_url_unchanged():
    """Named topics continue to build legacy headlines/section/topic/ URLs."""
    client = GoogleNewsClient(language="en", country="US")

    assert client._get_topic_path("WORLD") == "topic/WORLD"
    expected_world = (
        "https://news.google.com/rss/headlines/section/topic/WORLD"
        "?hl=en-US&gl=US&ceid=US%3Aen"
    )
    assert client._build_url("topic/WORLD") == expected_world

    assert client._get_topic_path("TECHNOLOGY") == "topic/TECHNOLOGY"
    expected_tech = (
        "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY"
        "?hl=en-US&gl=US&ceid=US%3Aen"
    )
    assert client._build_url("topic/TECHNOLOGY") == expected_tech


def test_topic_token_exact_url():
    """Custom section tokens route to topics/<TOKEN> with exactly one encoding pass."""
    client = GoogleNewsClient(language="en", country="US")
    token = "CAAqKggKIiRDQkFTRF..."

    path = client._get_topic_path(topic_token=token)
    assert path == f"topics/{token}"

    url = client._build_url(path)
    assert (
        url == f"https://news.google.com/rss/topics/{token}?hl=en-US&gl=US&ceid=US%3Aen"
    )


def test_topic_token_encoding_safety():
    """Special characters in section tokens are safely percent-encoded once."""
    client = GoogleNewsClient(language="en", country="US")
    raw_token = "CAAq+test=value/123"

    path = client._get_topic_path(topic_token=raw_token)
    assert path == "topics/CAAq%2Btest%3Dvalue%2F123"

    url = client._build_url(path)
    expected = (
        "https://news.google.com/rss/topics/CAAq%2Btest%3Dvalue%2F123"
        "?hl=en-US&gl=US&ceid=US%3Aen"
    )
    assert url == expected


def test_async_topic_token_exact_url_parity():
    """Async client builds the identical URL for custom section tokens."""
    client = AsyncGoogleNewsClient(language="it", country="IT")
    token = "CAAqKggKIiRDQkFTRF..."

    path = client._get_topic_path(topic_token=token)
    assert path == f"topics/{token}"

    url = client._build_url(path)
    assert (
        url == f"https://news.google.com/rss/topics/{token}?hl=it-IT&gl=IT&ceid=IT%3Ait"
    )


# -----------------------------------------------------------------------------
# Input Validation & Mutual Exclusion Tests
# -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "invalid_token",
    ["", "   ", "\t\n", 12345, ["token"], {"key": "val"}],
)
def test_reject_empty_or_non_string_topic_token(invalid_token):
    client = GoogleNewsClient()
    with pytest.raises(ValidationError) as exc:
        client.top_news(topic_token=invalid_token)

    assert exc.value.field == "topic_token"
    assert "topic_token must be a non-empty string" in str(exc.value)


@pytest.mark.parametrize(
    "url_token",
    [
        "https://news.google.com/topics/CAAq...",
        "http://news.google.com/rss/topics/CAAq...",
        "ftp://example.com/topic",
    ],
)
def test_reject_url_passed_as_topic_token(url_token):
    client = GoogleNewsClient()
    with pytest.raises(ValidationError) as exc:
        client.top_news(topic_token=url_token)

    assert exc.value.field == "topic_token"
    assert "topic_token must be a section token, not a URL" in str(exc.value)


def test_reject_named_topic_together_with_topic_token():
    """Prevent using a non-default named topic and a topic_token in the same call."""
    client = GoogleNewsClient()
    with pytest.raises(ValidationError) as exc:
        client.top_news("TECHNOLOGY", topic_token="CAAq...")

    assert exc.value.field == "topic_token"
    assert "Cannot use 'topic_token' together with a custom 'topic'" in str(exc.value)


def test_clusters_reject_named_topic_together_with_topic_token():
    """Prevent using a non-default named topic and topic_token in top_news_clusters."""
    client = GoogleNewsClient()
    with pytest.raises(ValidationError) as exc:
        client.top_news_clusters("BUSINESS", topic_token="CAAq...")

    assert exc.value.field == "topic_token"
    assert "Cannot use 'topic_token' together with a custom 'topic'" in str(exc.value)


def test_reject_topic_token_in_non_default_mode():
    """topic_token is only supported in RSS mode."""
    client = GoogleNewsClient()
    with pytest.raises(ValidationError) as exc:
        client.top_news(mode="searchapi_portal", topic_token="CAAq...")

    assert exc.value.field == "topic_token"
    assert "topic_token is only supported in default RSS mode" in str(exc.value)


# -----------------------------------------------------------------------------
# Default-Topic Regressions Tests
# -----------------------------------------------------------------------------


def test_default_topic_regression_sync():
    """Calling top_news() with default arguments retains WORLD topic and exact URL."""
    requested_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        return httpx.Response(200, text=EN_US_XML, request=request)

    client = GoogleNewsClient(transport=httpx.MockTransport(handler))
    articles = client.top_news()

    assert len(requested_urls) == 1
    assert "headlines/section/topic/WORLD" in requested_urls[0]
    assert len(articles) > 0


@pytest.mark.asyncio
async def test_default_topic_regression_async():
    """Calling top_news() on async client retains WORLD topic and exact URL."""
    requested_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        return httpx.Response(200, text=EN_US_XML, request=request)

    async with AsyncGoogleNewsClient(transport=httpx.MockTransport(handler)) as client:
        articles = await client.top_news()

    assert len(requested_urls) == 1
    assert "headlines/section/topic/WORLD" in requested_urls[0]
    assert len(articles) > 0


# -----------------------------------------------------------------------------
# Cache-Key Isolation Tests
# -----------------------------------------------------------------------------


def test_cache_key_isolation_sync():
    """Named topics, custom tokens, and distinct tokens occupy isolated cache keys."""
    requests_made = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests_made.append(str(request.url))
        return httpx.Response(200, text=EN_US_XML, request=request)

    client = GoogleNewsClient(transport=httpx.MockTransport(handler))

    # 1. Query named topic WORLD
    client.top_news()
    assert len(requests_made) == 1
    world_url = requests_made[0]

    # Repeating WORLD query hits cache
    client.top_news()
    assert len(requests_made) == 1

    # 2. Query token A
    token_a = "TOKEN_A"
    client.top_news(topic_token=token_a)
    assert len(requests_made) == 2
    token_a_url = requests_made[1]

    # Repeating token A hits cache
    client.top_news(topic_token=token_a)
    assert len(requests_made) == 2

    # 3. Query token B
    token_b = "TOKEN_B"
    client.top_news(topic_token=token_b)
    assert len(requests_made) == 3
    token_b_url = requests_made[2]

    # Verify all 3 URLs are distinct
    assert len({world_url, token_a_url, token_b_url}) == 3

    # Verify cache keys inside client._cache
    assert client._cache.get(world_url) is not None
    assert client._cache.get(token_a_url) is not None
    assert client._cache.get(token_b_url) is not None


@pytest.mark.asyncio
async def test_cache_key_isolation_async():
    """Async cache key isolation across different tokens and named topic."""
    requests_made = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests_made.append(str(request.url))
        return httpx.Response(200, text=EN_US_XML, request=request)

    async with AsyncGoogleNewsClient(transport=httpx.MockTransport(handler)) as client:
        await client.top_news()
        await client.top_news(topic_token="TOKEN_X")
        await client.top_news(topic_token="TOKEN_Y")

        assert len(requests_made) == 3

        # Repeating requests hits cache
        await client.top_news()
        await client.top_news(topic_token="TOKEN_X")
        await client.top_news(topic_token="TOKEN_Y")
        assert len(requests_made) == 3


# -----------------------------------------------------------------------------
# Saved Locale Fixtures Verification Tests
# -----------------------------------------------------------------------------


def test_saved_en_us_fixture_sync():
    """Verify parsing real Google News RSS responses for en-US section tokens."""
    token = "CAAqKggKIiRDQkFTRF..."

    def handler(request: httpx.Request) -> httpx.Response:
        assert f"topics/{token}" in str(request.url)
        assert "hl=en-US" in str(request.url)
        return httpx.Response(200, text=EN_US_XML, request=request)

    client = GoogleNewsClient(
        language="en", country="US", transport=httpx.MockTransport(handler)
    )
    articles = client.top_news(topic_token=token, max_results=10)

    assert len(articles) == 10
    for article in articles:
        assert article["title"]
        assert article["link"]
        assert article["published"]
        assert article["source"]
        assert article["id"]

    # Verify clusters parsing on fixture
    clusters = client.top_news_clusters(topic_token=token, max_results=5)
    assert len(clusters) == 5
    for cluster in clusters:
        assert cluster["primary"]["title"]
        assert isinstance(cluster["related"], list)


def test_saved_it_it_fixture_sync():
    """Verify parsing real Google News RSS responses for it-IT section tokens."""
    token = "CAAqKggKIiRDQkFTRF..."

    def handler(request: httpx.Request) -> httpx.Response:
        assert f"topics/{token}" in str(request.url)
        assert "hl=it-IT" in str(request.url)
        return httpx.Response(200, text=IT_IT_XML, request=request)

    client = GoogleNewsClient(
        language="it", country="IT", transport=httpx.MockTransport(handler)
    )
    articles = client.top_news(topic_token=token, max_results=10)

    assert len(articles) == 10
    for article in articles:
        assert article["title"]
        assert article["link"]
        assert article["published"]
        assert article["source"]
        assert article["id"]

    clusters = client.top_news_clusters(topic_token=token, max_results=5)
    assert len(clusters) == 5
    for cluster in clusters:
        assert cluster["primary"]["title"]
        assert isinstance(cluster["related"], list)


@pytest.mark.asyncio
async def test_saved_fixtures_async():
    """Verify parsing real Google News RSS responses asynchronously."""
    token = "CAAqKggKIiRDQkFTRF..."

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=EN_US_XML, request=request)

    async with AsyncGoogleNewsClient(
        language="en", country="US", transport=httpx.MockTransport(handler)
    ) as client:
        articles = await client.top_news(topic_token=token, max_results=5)
        clusters = await client.top_news_clusters(topic_token=token, max_results=5)

    assert len(articles) == 5
    assert len(clusters) == 5
