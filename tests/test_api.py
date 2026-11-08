from unittest.mock import MagicMock

import pytest
from aiohttp import ClientError

from custom_components.fonia.api import (
    FoniaApi,
    FoniaApiError,
    FoniaAuthError,
    FoniaRateLimitError,
)


class MockResponse:
    def __init__(
        self,
        status: int = 200,
        json_data: dict | None = None,
        text_data: str = "",
        headers: dict | None = None,
    ):
        self.status = status
        self._json_data = json_data or {}
        self._text_data = text_data
        self.headers = headers or {}

    async def json(self):
        return self._json_data

    async def text(self):
        return self._text_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


@pytest.mark.asyncio
async def test_api_login_success() -> None:
    session = MagicMock()
    session.post.return_value = MockResponse(
        status=200,
        json_data={"token": "test-token-123", "user": {"id": 1, "name": "Jan"}},
    )

    api = FoniaApi(session)
    data = await api.login("user@test.pl", "pass123")
    assert api.token == "test-token-123"
    assert data["token"] == "test-token-123"
    assert "Bearer test-token-123" in api.headers()["Authorization"]


@pytest.mark.asyncio
async def test_api_login_auth_error() -> None:
    session = MagicMock()
    session.post.return_value = MockResponse(status=401)

    api = FoniaApi(session)
    with pytest.raises(FoniaAuthError):
        await api.login("wrong_user", "wrong_pass")


@pytest.mark.asyncio
async def test_api_login_rate_limit() -> None:
    session = MagicMock()
    session.post.return_value = MockResponse(status=429, headers={"Retry-After": "60"})

    api = FoniaApi(session)
    with pytest.raises(FoniaRateLimitError, match="Retry-After: 60"):
        await api.login("user", "pass")


@pytest.mark.asyncio
async def test_api_network_error() -> None:
    session = MagicMock()
    session.post.side_effect = ClientError("Connection reset")

    api = FoniaApi(session)
    with pytest.raises(FoniaApiError, match="Unable to connect to Fonia"):
        await api.login("user", "pass")


@pytest.mark.asyncio
async def test_api_auto_relogin_on_401() -> None:
    session = MagicMock()
    # First GET returns 401 (expired token), then login succeeds, then second GET succeeds
    get_res_401 = MockResponse(status=401)
    post_res_login = MockResponse(status=200, json_data={"token": "new-token"})
    get_res_ok = MockResponse(status=200, json_data={"data": [{"uuid": "sub1"}]})

    session.get.side_effect = [get_res_401, get_res_ok]
    session.post.return_value = post_res_login

    api = FoniaApi(session, username="myuser", password="mypassword")
    api.token = "old-token"

    result = await api.get("/subscriptions")
    assert result == {"data": [{"uuid": "sub1"}]}
    assert api.token == "new-token"
    assert session.get.call_count == 2
    assert session.post.call_count == 1


@pytest.mark.asyncio
async def test_api_usage_sync_success_204() -> None:
    session = MagicMock()
    session.post.return_value = MockResponse(status=204)

    api = FoniaApi(session)
    api.token = "token"
    res = await api.usage_sync()
    assert res == {}
