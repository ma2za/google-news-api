"""Tests for the configuration module."""

import pytest

from google_news_api.config import ClientConfig, LogConfig
from google_news_api.exceptions import ConfigurationError


def test_default_client_config():
    """Test default client configuration."""
    config = ClientConfig()
    assert config.language == "en"
    assert config.country == "US"
    assert config.requests_per_minute == 60
    assert config.cache_ttl == 300
    assert config.log_config is not None


def test_custom_client_config():
    """Test custom client configuration."""
    config = ClientConfig(
        language="es",
        country="ES",
        requests_per_minute=30,
        cache_ttl=600,
    )
    assert config.language == "es"
    assert config.country == "ES"
    assert config.requests_per_minute == 30
    assert config.cache_ttl == 600


def test_invalid_language():
    """Test invalid language code."""
    with pytest.raises(ConfigurationError) as exc_info:
        ClientConfig(language="invalid")
    assert "Language must be" in str(exc_info.value)


def test_invalid_country():
    """Test invalid country code."""
    with pytest.raises(ConfigurationError) as exc_info:
        ClientConfig(country="INVALID")
    assert "Country must be" in str(exc_info.value)


def test_invalid_requests_per_minute():
    """Test invalid requests per minute."""
    with pytest.raises(ValueError) as exc_info:
        ClientConfig(requests_per_minute=0)
    assert "requests_per_minute must be positive" in str(exc_info.value)


def test_invalid_cache_ttl():
    """Test invalid cache TTL."""
    with pytest.raises(ValueError) as exc_info:
        ClientConfig(cache_ttl=0)
    assert "cache_ttl must be positive" in str(exc_info.value)


def test_log_config():
    """Test log configuration."""
    log_config = LogConfig(level="DEBUG", format="%(message)s")
    config = ClientConfig(log_config=log_config)
    assert config.log_config.level == "DEBUG"
    assert config.log_config.format == "%(message)s"


def test_config_as_dict():
    """Test configuration to dictionary conversion."""
    config = ClientConfig(language="fr", country="FR")
    config_dict = config.as_dict()
    assert config_dict["language"] == "fr"
    assert config_dict["country"] == "FR"
    assert "requests_per_minute" in config_dict
    assert "cache_ttl" in config_dict
