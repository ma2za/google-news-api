"""Google News API package."""

from importlib.metadata import PackageNotFoundError, version

from .client import AsyncGoogleNewsClient, GoogleNewsClient
from .config import ClientConfig
from .enrichment import ArticleEnricher, AsyncArticleEnricher
from .exceptions import (
    ConfigurationError,
    GoogleNewsError,
    HTTPError,
    ParsingError,
    RateLimitError,
    ValidationError,
)
from .logging import setup_logging
from .query import NewsQuery
from .results import (
    deduplicate_articles,
    normalize_article,
    normalize_articles,
    parse_published,
    sort_articles,
    source_domain,
)
from .types import Article, EnrichedArticle, NormalizedArticle
from .utils import AsyncCache, AsyncRateLimiter, Cache, RateLimiter

try:
    __version__ = version("google-news-api")
except PackageNotFoundError:
    __version__ = "0.0.0"

__author__ = "Paolo Mazza"
__email__ = "mazzapaolo2019@gmail.com"

__all__ = [
    "AsyncGoogleNewsClient",
    "GoogleNewsClient",
    "ClientConfig",
    "ArticleEnricher",
    "AsyncArticleEnricher",
    "NewsQuery",
    "ConfigurationError",
    "GoogleNewsError",
    "HTTPError",
    "ParsingError",
    "RateLimitError",
    "ValidationError",
    "setup_logging",
    "Article",
    "EnrichedArticle",
    "NormalizedArticle",
    "deduplicate_articles",
    "normalize_article",
    "normalize_articles",
    "parse_published",
    "sort_articles",
    "source_domain",
    "AsyncCache",
    "AsyncRateLimiter",
    "Cache",
    "RateLimiter",
]
