"""Custom exceptions for the Google News API client."""

from typing import Any, Optional


class GoogleNewsError(Exception):
    """Base exception for all Google News API errors."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(message, *args)
        self.message = message
        for key, value in kwargs.items():
            setattr(self, key, value)


class ConfigurationError(GoogleNewsError):
    """Raised when there is an error in the client configuration."""


class RateLimitError(GoogleNewsError):
    """Raised when the API rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[float] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)
        self.retry_after = retry_after


class HTTPError(GoogleNewsError):
    """Raised when an HTTP request fails."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the HTTP error.

        Args:
            message: Error message
            status_code: HTTP status code
            response_text: Response body text
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)
        self.status_code = status_code
        self.response_text = response_text


class ValidationError(GoogleNewsError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the validation error.

        Args:
            message: Error message
            field: Name of the invalid field
            value: Invalid value
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)
        self.field = field
        self.value = value


class ParsingError(GoogleNewsError):
    """Raised when parsing RSS feed or article data fails."""

    def __init__(
        self, message: str, data: Optional[Any] = None, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize the parsing error.

        Args:
            message: Error message
            data: Data that failed to parse
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)
        self.data = data
