"""Configure logging for the Google News API client."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Optional

# Create logger
logger = logging.getLogger("google_news_api")

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Default log configuration
DEFAULT_LOG_CONFIG = {
    "format": DEFAULT_LOG_FORMAT,
    "level": "INFO",
    "stream": sys.stdout,
    "datefmt": "%Y-%m-%d %H:%M:%S",
}


class StructuredFormatter(logging.Formatter):
    """Format log records as structured JSON."""

    def __init__(self) -> None:
        """Initialize the formatter."""
        super().__init__()
        self.default_fields = {
            "timestamp": "",
            "level": "",
            "message": "",
            "logger": "",
        }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON formatted string
        """
        message = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add any extra attributes
        if hasattr(record, "props"):
            message.update(record.props)
        # Handle extra attributes passed directly
        if hasattr(record, "__dict__"):
            extras = {
                key: value
                for key, value in record.__dict__.items()
                if key
                not in {
                    "args",
                    "asctime",
                    "created",
                    "exc_info",
                    "exc_text",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "msg",
                    "name",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "stack_info",
                    "thread",
                    "threadName",
                    "props",
                }
            }
            message.update(extras)

        return json.dumps(message)


def setup_logging(
    level: str = "INFO", structured: bool = True, log_file: Optional[str] = None
) -> None:
    """Configure logging with specified settings.

    Args:
        level: Log level (default: INFO)
        structured: Whether to use structured JSON logging (default: True)
        log_file: Optional file path to write logs to
    """
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # Create formatter
    formatter = (
        StructuredFormatter()
        if structured
        else logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def log_with_props(**props: Any) -> None:
    """Add properties to log records.

    Args:
        **props: Keyword arguments to add to the log record
    """

    def decorator(func: Any) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            old_factory = logging.getLogRecordFactory()

            def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
                record = old_factory(*args, **kwargs)
                record.props = props  # type: ignore
                return record

            logging.setLogRecordFactory(record_factory)
            try:
                return func(*args, **kwargs)
            finally:
                logging.setLogRecordFactory(old_factory)

        return wrapper

    return decorator
