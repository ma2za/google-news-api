import inspect

from feedparser import FeedParserDict

import google_news_api
from google_news_api import AsyncGoogleNewsClient, GoogleNewsClient


def _parameters(callable_object):
    return tuple(
        (
            parameter.name,
            parameter.kind.name,
            parameter.default,
        )
        for parameter in inspect.signature(callable_object).parameters.values()
    )


def test_public_exports_are_stable():
    assert set(google_news_api.__all__) == {
        "Article",
        "AsyncCache",
        "AsyncGoogleNewsClient",
        "AsyncRateLimiter",
        "Cache",
        "ClientConfig",
        "ConfigurationError",
        "EnrichedArticle",
        "GoogleNewsClient",
        "GoogleNewsError",
        "HTTPError",
        "ParsingError",
        "RateLimitError",
        "RateLimiter",
        "ValidationError",
        "setup_logging",
    }


def test_client_constructor_contract_is_stable():
    expected = (
        ("language", "POSITIONAL_OR_KEYWORD", "en"),
        ("country", "POSITIONAL_OR_KEYWORD", "US"),
        ("requests_per_minute", "POSITIONAL_OR_KEYWORD", 60),
        ("cache_ttl", "POSITIONAL_OR_KEYWORD", 300),
    )

    assert _parameters(GoogleNewsClient) == expected
    assert _parameters(AsyncGoogleNewsClient) == expected


def test_search_contract_is_stable():
    expected = (
        ("self", "POSITIONAL_OR_KEYWORD", inspect.Parameter.empty),
        ("query", "POSITIONAL_OR_KEYWORD", inspect.Parameter.empty),
        ("after", "KEYWORD_ONLY", None),
        ("before", "KEYWORD_ONLY", None),
        ("when", "KEYWORD_ONLY", None),
        ("max_results", "KEYWORD_ONLY", None),
        ("mode", "KEYWORD_ONLY", "default"),
        ("include_domains", "KEYWORD_ONLY", None),
        ("exclude_domains", "KEYWORD_ONLY", None),
    )

    assert _parameters(GoogleNewsClient.search) == expected
    assert _parameters(AsyncGoogleNewsClient.search) == expected


def test_top_news_contract_is_stable():
    expected = (
        ("self", "POSITIONAL_OR_KEYWORD", inspect.Parameter.empty),
        ("topic", "POSITIONAL_OR_KEYWORD", "WORLD"),
        ("max_results", "KEYWORD_ONLY", None),
        ("mode", "KEYWORD_ONLY", "default"),
    )

    assert _parameters(GoogleNewsClient.top_news) == expected
    assert _parameters(AsyncGoogleNewsClient.top_news) == expected


def test_batch_search_contract_is_stable():
    shared_start = (
        ("self", "POSITIONAL_OR_KEYWORD", inspect.Parameter.empty),
        ("queries", "POSITIONAL_OR_KEYWORD", inspect.Parameter.empty),
        ("after", "KEYWORD_ONLY", None),
        ("before", "KEYWORD_ONLY", None),
        ("when", "KEYWORD_ONLY", None),
        ("max_results", "KEYWORD_ONLY", None),
    )
    shared_end = (
        ("mode", "KEYWORD_ONLY", "default"),
        ("include_domains", "KEYWORD_ONLY", None),
        ("exclude_domains", "KEYWORD_ONLY", None),
    )
    async_controls = (
        ("max_concurrent", "KEYWORD_ONLY", 5),
        ("timeout", "KEYWORD_ONLY", 30.0),
        ("delay", "KEYWORD_ONLY", 1.0),
        ("show_progress", "KEYWORD_ONLY", False),
    )

    assert _parameters(GoogleNewsClient.batch_search) == shared_start + shared_end
    assert (
        _parameters(AsyncGoogleNewsClient.batch_search)
        == shared_start + async_controls + shared_end
    )


def test_decode_url_contract_is_stable():
    expected = (
        ("self", "POSITIONAL_OR_KEYWORD", inspect.Parameter.empty),
        ("source_url", "POSITIONAL_OR_KEYWORD", inspect.Parameter.empty),
        ("timeout", "POSITIONAL_OR_KEYWORD", 30.0),
    )

    assert _parameters(GoogleNewsClient.decode_url) == expected
    assert _parameters(AsyncGoogleNewsClient.decode_url) == expected


def test_decode_urls_contract_is_stable():
    shared_start = (
        ("self", "POSITIONAL_OR_KEYWORD", inspect.Parameter.empty),
        ("urls", "POSITIONAL_OR_KEYWORD", inspect.Parameter.empty),
    )
    shared_end = (
        ("timeout", "KEYWORD_ONLY", 30.0),
        ("delay", "KEYWORD_ONLY", 1.0),
        ("show_progress", "KEYWORD_ONLY", False),
    )
    async_controls = (("max_concurrent", "KEYWORD_ONLY", 5),)

    assert _parameters(GoogleNewsClient.decode_urls) == shared_start + shared_end
    assert (
        _parameters(AsyncGoogleNewsClient.decode_urls)
        == shared_start + async_controls + shared_end
    )


def test_base_article_shape_is_stable():
    feed = FeedParserDict()
    feed.entries = [
        FeedParserDict(
            title="Title",
            link="https://news.google.com/rss/articles/article-id",
            published="Wed, 29 Jul 2026 12:00:00 GMT",
            summary="Summary",
            source=FeedParserDict(title="Publisher"),
        )
    ]
    client = object.__new__(GoogleNewsClient)

    article = client._parse_articles(feed)[0]

    assert tuple(article) == (
        "title",
        "link",
        "published",
        "summary",
        "source",
        "id",
    )
