"""Configuration module for Google News API client."""

import logging
from dataclasses import asdict, dataclass
from typing import Dict, Optional

from .exceptions import ConfigurationError


@dataclass
class LogConfig:
    """Logging configuration for the Google News API client.

    Attributes:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log message format string
        date_format: Date format string for log messages
    """

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"

    def __post_init__(self) -> None:
        """Validate logging configuration.

        Raises:
            ConfigurationError: If logging level is invalid
        """
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level not in valid_levels:
            raise ConfigurationError(
                f"Invalid logging level. Must be one of: {', '.join(valid_levels)}",
                field="level",
                value=self.level,
            )

    def setup(self) -> None:
        """Configure logging with the specified settings."""
        logging.basicConfig(
            level=self.level,
            format=self.format,
            datefmt=self.date_format,
        )


@dataclass
class ClientConfig:
    """Configuration for the Google News API client.

    Attributes:
        language: Two-letter language code (ISO 639-1)
        country: Two-letter country code (ISO 3166-1 alpha-2)
        requests_per_minute: Maximum number of requests per minute
        cache_ttl: Cache time-to-live in seconds
        log_config: Logging configuration
    """

    language: str = "en"
    country: str = "US"
    requests_per_minute: int = 60
    cache_ttl: int = 300
    log_config: Optional[LogConfig] = None

    def __post_init__(self) -> None:
        """Validate client configuration.

        Raises:
            ConfigurationError: If any configuration values are invalid
            ValueError: If numeric values are not positive
        """
        # Validate language code
        if not isinstance(self.language, str) or len(self.language) != 2:
            raise ConfigurationError(
                "Language must be a two-letter ISO 639-1 code",
                field="language",
                value=self.language,
            )

        # Validate country code
        if not isinstance(self.country, str) or len(self.country) != 2:
            raise ConfigurationError(
                "Country must be a two-letter ISO 3166-1 alpha-2 code",
                field="country",
                value=self.country,
            )

        # Validate numeric values
        if self.requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")
        if self.cache_ttl <= 0:
            raise ValueError("cache_ttl must be positive")

        # Set up logging if config provided
        if self.log_config is None:
            self.log_config = LogConfig()
        self.log_config.setup()

    def as_dict(self) -> Dict[str, str]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        return asdict(self)
