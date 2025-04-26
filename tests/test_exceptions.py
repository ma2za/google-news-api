"""Tests for custom exceptions."""

from http import HTTPStatus

import httpx

from google_news_api.exceptions import (
    ConfigurationError,
    GoogleNewsError,
    HTTPError,
    ParsingError,
    RateLimitError,
    ValidationError,
)


def test_base_exception():
    """Test base GoogleNewsError exception."""
    error = GoogleNewsError("Test error message")
    assert str(error) == "Test error message"
    assert error.message == "Test error message"

    # Test with additional attributes
    error = GoogleNewsError("Test error", extra_field="value")
    assert error.extra_field == "value"


def test_configuration_error():
    """Test ConfigurationError exception."""
    error = ConfigurationError(
        "Invalid configuration",
        field="language",
        value="invalid",
    )
    assert "Invalid configuration" in str(error)
    assert error.field == "language"
    assert error.value == "invalid"


def test_validation_error():
    """Test ValidationError exception."""
    error = ValidationError(
        "Invalid parameter",
        field="query",
        value="",
    )
    assert "Invalid parameter" in str(error)
    assert error.field == "query"
    assert error.value == ""


def test_http_error():
    """Test HTTPError exception."""
    response = httpx.Response(
        status_code=HTTPStatus.BAD_REQUEST,
        text="Bad Request",
        request=httpx.Request("GET", "http://example.com"),
    )

    error = HTTPError(
        "HTTP request failed",
        status_code=400,
        response_text="Bad Request",
        response=response,
    )

    assert "HTTP request failed" in str(error)
    assert error.status_code == 400
    assert error.response_text == "Bad Request"
    assert error.response == response


def test_rate_limit_error():
    """Test RateLimitError exception."""
    response = httpx.Response(
        status_code=HTTPStatus.TOO_MANY_REQUESTS,
        text="Too Many Requests",
        request=httpx.Request("GET", "http://example.com"),
    )

    error = RateLimitError(
        "Rate limit exceeded",
        retry_after=60,
        response=response,
    )

    assert "Rate limit exceeded" in str(error)
    assert error.retry_after == 60
    assert error.response == response


def test_parsing_error():
    """Test ParsingError exception."""
    error = ParsingError(
        "Failed to parse feed",
        data="<invalid>xml</invalid>",
        error=ValueError("XML parsing error"),
    )

    assert "Failed to parse feed" in str(error)
    assert error.data == "<invalid>xml</invalid>"
    assert isinstance(error.error, ValueError)
    assert str(error.error) == "XML parsing error"
