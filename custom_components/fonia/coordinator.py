from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FoniaApi, FoniaApiError, FoniaAuthError, FoniaRateLimitError
from .const import (
    ACCOUNT_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL,
    CONF_USAGE_SYNC,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DETAILS_SCAN_INTERVAL,
    USAGE_SYNC_INTERVAL,
)
from .models import FoniaData, normalize

_LOGGER = logging.getLogger(__name__)


class FoniaCoordinator(DataUpdateCoordinator[FoniaData]):
    """Coordinate Fonia API data and isolate optional endpoint failures."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: FoniaApi) -> None:
        self.api = api
        self.entry = entry
        self.last_usage_sync: datetime | None = None
        self.last_details_update: datetime | None = None
        self.last_account_update: datetime | None = None
        self.usage_sync_enabled = bool(entry.options.get(CONF_USAGE_SYNC, True))
        scan_minutes = entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
        )
        self.scan_interval = timedelta(minutes=max(5, min(60, int(scan_minutes))))
        super().__init__(
            hass,
            _LOGGER,
            name="Fonia",
            update_interval=self.scan_interval,
        )

    async def async_sync_usage(self) -> None:
        """Manually request a usage refresh without triggering a duplicate sync."""
        await self.api.usage_sync()
        self.last_usage_sync = datetime.now().astimezone()

    async def _async_update_data(self) -> FoniaData:
        now = datetime.now().astimezone()
        previous = self.data or FoniaData()
        try:
            if self.usage_sync_enabled and (
                self.last_usage_sync is None
                or now - self.last_usage_sync >= USAGE_SYNC_INTERVAL
            ):
                await self.api.usage_sync()
                self.last_usage_sync = now

            subscriptions_response = await self.api.subscriptions()
            raw_subscriptions = subscriptions_response.get("data") or []
            if not isinstance(raw_subscriptions, list):
                raise UpdateFailed("Unexpected subscriptions response from Fonia")
            subscriptions = [
                normalize(item)
                for item in raw_subscriptions
                if isinstance(item, dict) and item.get("uuid")
            ]
            result = FoniaData(subscriptions=subscriptions)

            if (
                self.last_details_update is None
                or now - self.last_details_update >= DETAILS_SCAN_INTERVAL
            ):
                details_ok = True
                for subscription in subscriptions:
                    try:
                        detail = await self.api.subscription(subscription.uuid)
                        detail_data = detail.get("data") or detail
                        if not isinstance(detail_data, dict):
                            raise FoniaApiError(
                                "Unexpected subscription detail response"
                            )
                        result.orders[subscription.uuid] = _dict_list(
                            detail_data.get("orders")
                        )
                        payment_method = detail_data.get("payment_method")
                        result.payment_methods[subscription.uuid] = (
                            payment_method if isinstance(payment_method, dict) else {}
                        )
                    except (FoniaAuthError, FoniaRateLimitError):
                        raise
                    except FoniaApiError:
                        details_ok = False
                        result.orders[subscription.uuid] = previous.orders.get(
                            subscription.uuid, []
                        )
                        result.payment_methods[subscription.uuid] = (
                            previous.payment_methods.get(subscription.uuid, {})
                        )
                        _LOGGER.debug(
                            "Unable to update details for a Fonia subscription",
                            exc_info=True,
                        )
                if details_ok:
                    self.last_details_update = now
            else:
                result.orders = {
                    item.uuid: previous.orders.get(item.uuid, [])
                    for item in subscriptions
                }
                result.payment_methods = {
                    item.uuid: previous.payment_methods.get(item.uuid, {})
                    for item in subscriptions
                }

            if (
                self.last_account_update is None
                or now - self.last_account_update >= ACCOUNT_SCAN_INTERVAL
            ):
                account_ok = True
                try:
                    cashback = await self.api.cashback()
                    cashback_data = cashback.get("data") or cashback
                    if not isinstance(cashback_data, dict):
                        raise FoniaApiError("Unexpected cashback response")
                    result.cashback_balance = _cashback_pln(
                        cashback_data.get("balance")
                    )
                    result.cashback_spendable = _cashback_pln(
                        cashback_data.get("spendable")
                    )
                except (FoniaAuthError, FoniaRateLimitError):
                    raise
                except FoniaApiError:
                    account_ok = False
                    result.cashback_balance = previous.cashback_balance
                    result.cashback_spendable = previous.cashback_spendable
                    _LOGGER.debug("Unable to update Fonia cashback", exc_info=True)
                try:
                    result.site_alerts = _list_data(await self.api.site_alerts())
                except (FoniaAuthError, FoniaRateLimitError):
                    raise
                except FoniaApiError:
                    account_ok = False
                    result.site_alerts = previous.site_alerts
                    _LOGGER.debug("Unable to update Fonia site alerts", exc_info=True)
                try:
                    result.cashback_transactions = _list_data(
                        await self.api.cashback_transactions()
                    )
                except (FoniaAuthError, FoniaRateLimitError):
                    raise
                except FoniaApiError:
                    account_ok = False
                    result.cashback_transactions = previous.cashback_transactions
                    _LOGGER.debug(
                        "Unable to update Fonia cashback transactions", exc_info=True
                    )
                if account_ok:
                    self.last_account_update = now
            else:
                result.cashback_balance = previous.cashback_balance
                result.cashback_spendable = previous.cashback_spendable
                result.site_alerts = previous.site_alerts
                result.cashback_transactions = previous.cashback_transactions

            return result
        except ConfigEntryAuthFailed:
            raise
        except FoniaAuthError as err:
            raise ConfigEntryAuthFailed("Fonia authentication expired") from err
        except FoniaRateLimitError as err:
            raise UpdateFailed("Fonia API rate limit reached; retrying later") from err
        except FoniaApiError as err:
            raise UpdateFailed(str(err)) from err


def _number(value: object) -> float | None:
    if not isinstance(value, (str, int, float)) or value == "":
        return None
    try:
        return float(value)
    except (OverflowError, ValueError):
        return None


def _cashback_pln(value: object) -> float | None:
    """Convert Fonia cashback minor units (grosze) to PLN."""
    amount = _number(value)
    return amount / 100 if amount is not None else None


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _list_data(response: dict[str, Any]) -> list[dict[str, Any]]:
    data = response.get("data")
    if isinstance(data, list):
        return _dict_list(data)
    if isinstance(data, dict):
        for key in ("alerts", "items", "results", "site_alerts", "transactions"):
            value = data.get(key)
            if isinstance(value, list):
                return _dict_list(value)
    return []
