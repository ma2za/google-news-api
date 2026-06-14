"""Google News API package."""

from importlib.metadata import PackageNotFoundError, version

from .client import AsyncGoogleNewsClient, GoogleNewsClient
from .config import ClientConfig
from .exceptions import (
    ConfigurationError,
    GoogleNewsError,
    HTTPError,
    ParsingError,
    RateLimitError,
    ValidationError,
)
from .logging import setup_logging
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
    "ConfigurationError",
    "GoogleNewsError",
    "HTTPError",
    "ParsingError",
    "RateLimitError",
    "ValidationError",
    "setup_logging",
    "AsyncCache",
    "AsyncRateLimiter",
    "Cache",
    "RateLimiter",
]
