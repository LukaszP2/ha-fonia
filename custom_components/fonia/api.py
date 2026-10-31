from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout, ContentTypeError

from .const import API_BASE

_LOGGER = logging.getLogger(__name__)


class FoniaApiError(Exception):
    """Base Fonia API error."""


class FoniaAuthError(FoniaApiError):
    """Authentication failed or expired."""


class FoniaRateLimitError(FoniaApiError):
    """Fonia API rate limit was reached."""


class FoniaApi:
    """Async client for the Fonia web API."""
    def __init__(self, session: ClientSession) -> None:
        self.session = session
        self.token: str | None = None

    @staticmethod
    def _browser_headers() -> dict[str, str]:
        # These headers mirror the actual web application request captured in
        # the HAR. They are not a CORS workaround; they simply make the
        # server-to-server request look like the request used by Fonia's UI.
        return {
            "Accept": "application/json",
            "Origin": "https://moja.fonia.app",
            "Referer": "https://moja.fonia.app/login",
        }

    async def login(self, username: str, password: str) -> dict[str, Any]:
        try:
            async with self.session.post(
                f"{API_BASE}/login",
                json={"identifier": username, "password": password},
                headers={**self._browser_headers(), "Content-Type": "application/json"},
                timeout=ClientTimeout(total=20),
            ) as response:
                if response.status in (401, 403):
                    raise FoniaAuthError("Invalid credentials")
                if response.status == 429:
                    raise FoniaRateLimitError("Fonia login rate limit reached")
                if response.status >= 400:
                    raise FoniaApiError(f"HTTP {response.status}")
                try:
                    data = await response.json()
                except (ContentTypeError, ValueError) as err:
                    raise FoniaApiError("Fonia returned a non-JSON login response") from err
        except FoniaApiError:
            raise
        except (ClientError, TimeoutError) as err:
            raise FoniaApiError("Unable to connect to Fonia") from err

        if not isinstance(data, dict) or not data.get("token"):
            raise FoniaApiError("Fonia login response did not contain a token")
        self.token = str(data["token"])
        return data

    def headers(self) -> dict[str, str]:
        if not self.token:
            raise FoniaAuthError("Not authenticated")
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Origin": "https://moja.fonia.app",
            "Referer": "https://moja.fonia.app/",
        }

    async def get(self, path: str, **params: str) -> dict[str, Any]:
        try:
            async with self.session.get(
                f"{API_BASE}{path}",
                headers=self.headers(),
                params=params,
                timeout=ClientTimeout(total=20),
            ) as response:
                if response.status in (401, 403):
                    raise FoniaAuthError("Authentication expired")
                if response.status == 429:
                    raise FoniaRateLimitError("Fonia API rate limit reached")
                if response.status >= 400:
                    raise FoniaApiError(f"HTTP {response.status}")
                try:
                    data = await response.json()
                except (ContentTypeError, ValueError) as err:
                    raise FoniaApiError(f"Fonia returned a non-JSON response for {path}") from err
                if not isinstance(data, dict):
                    raise FoniaApiError(f"Unexpected response for {path}")
                return data
        except FoniaApiError:
            raise
        except (ClientError, TimeoutError) as err:
            raise FoniaApiError("Unable to connect to Fonia") from err

    async def subscriptions(self) -> dict[str, Any]:
        return await self.get("/subscriptions", include="tariff,usage")

    async def subscription(self, uid: str) -> dict[str, Any]:
        return await self.get(
            f"/subscriptions/{uid}",
            include="tariff,usage,orders,payment_method",
        )

    async def cashback(self) -> dict[str, Any]:
        return await self.get("/cashback/account")

    async def site_alerts(self) -> dict[str, Any]:
        return await self.get("/site-alerts")

    async def cashback_transactions(self) -> dict[str, Any]:
        return await self.get("/cashback/transactions")

    async def orders(self) -> dict[str, Any]:
        return await self.get("/orders")

    async def usage_sync(self) -> dict[str, Any]:
        """Ask Fonia to refresh usage data. Empty/204 responses are valid."""
        try:
            async with self.session.post(
                f"{API_BASE}/usage-sync",
                headers=self.headers(),
                timeout=ClientTimeout(total=20),
            ) as response:
                if response.status in (401, 403):
                    raise FoniaAuthError("Authentication expired")
                if response.status == 429:
                    raise FoniaRateLimitError("Fonia API rate limit reached")
                if response.status >= 400:
                    raise FoniaApiError(f"HTTP {response.status}")
                if response.status == 204:
                    return {}
                body = await response.text()
                if not body.strip():
                    return {}
                try:
                    data = await response.json()
                except (ContentTypeError, ValueError):
                    _LOGGER.debug("Fonia usage-sync returned a non-JSON body")
                    return {}
                return data if isinstance(data, dict) else {}
        except FoniaApiError:
            raise
        except (ClientError, TimeoutError) as err:
            raise FoniaApiError("Unable to connect to Fonia") from err
