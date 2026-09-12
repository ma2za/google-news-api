import time
from unittest.mock import MagicMock, patch

import httpx
import pytest

from google_news_api import GoogleNewsClient, HTTPError, RateLimitError


def test_fetch_feed_retries_on_timeout():
    client = GoogleNewsClient(max_retries=2, retry_backoff=0.01)

    with patch.object(
        client._client, 'get', side_effect=httpx.TimeoutException("timeout")
    ) as mock_get:
        with pytest.raises(HTTPError, match="timeout"):
            client._fetch_feed("http://fake")

        # 1 initial + 2 retries = 3 calls
        assert mock_get.call_count == 3


def test_fetch_feed_retries_on_502():
    client = GoogleNewsClient(max_retries=1, retry_backoff=0.01)

    response = MagicMock()
    response.status_code = 502
    response.text = "Bad Gateway"
    response.reason_phrase = "Bad Gateway"

    with patch.object(client._client, 'get', return_value=response) as mock_get:
        with pytest.raises(HTTPError, match="HTTP 502: Bad Gateway"):
            client._fetch_feed("http://fake")

        assert mock_get.call_count == 2


def test_fetch_feed_does_not_retry_404():
    client = GoogleNewsClient(max_retries=2, retry_backoff=0.01)

    response = MagicMock()
    response.status_code = 404
    response.text = "Not Found"
    response.reason_phrase = "Not Found"

    with patch.object(client._client, 'get', return_value=response) as mock_get:
        with pytest.raises(HTTPError, match="HTTP 404: Not Found"):
            client._fetch_feed("http://fake")

        assert mock_get.call_count == 1


def test_fetch_feed_respects_retry_after():
    client = GoogleNewsClient(max_retries=1, retry_backoff=0.01)

    response = MagicMock()
    response.status_code = 429
    response.text = "Too Many Requests"
    response.reason_phrase = "Too Many Requests"
    response.headers = {"Retry-After": "0.05"}

    start_time = time.time()
    with patch.object(client._client, 'get', return_value=response) as mock_get:
        with pytest.raises(RateLimitError):
            client._fetch_feed("http://fake")

        assert mock_get.call_count == 2

    duration = time.time() - start_time
    assert duration >= 0.05
