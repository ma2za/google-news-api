import pytest
import httpx
from google_news_api import GoogleNewsClient, AsyncGoogleNewsClient, ClientConfig
from google_news_api.client import CHROME_HEADERS

def test_client_config_defaults():
    client = GoogleNewsClient()
    assert client.max_retries == 3
    assert client.retry_backoff == 2.0
    assert client._client.timeout.read == 30.0
    assert client._client.headers["User-Agent"] == CHROME_HEADERS["User-Agent"]
    
def test_client_config_custom():
    headers = {"X-Custom": "test", "User-Agent": "my-agent"}
    client = GoogleNewsClient(
        timeout=15.0,
        max_retries=1,
        retry_backoff=0.5,
        headers=headers,
    )
    assert client.max_retries == 1
    assert client.retry_backoff == 0.5
    assert client._client.timeout.read == 15.0
    # Custom headers overlay the defaults
    assert client._client.headers["X-Custom"] == "test"
    assert client._client.headers["User-Agent"] == "my-agent"
    assert client._client.headers["Accept"] == CHROME_HEADERS["Accept"]

def test_from_config():
    config = ClientConfig(timeout=10.0, max_retries=5)
    client = GoogleNewsClient.from_config(config)
    assert client.max_retries == 5
    assert client._client.timeout.read == 10.0
    
@pytest.mark.asyncio
async def test_async_client_config_custom():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b""))
    async with AsyncGoogleNewsClient(transport=transport) as client:
        assert client.client.timeout.read == 30.0
