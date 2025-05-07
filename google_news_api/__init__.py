"""Google News API package."""

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

__version__ = "0.0.5"
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
