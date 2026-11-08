from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.fonia.api import (
    FoniaApiError,
    FoniaAuthError,
)
from custom_components.fonia.coordinator import FoniaCoordinator, _cashback_pln
from custom_components.fonia.models import FoniaData


def test_cashback_pln() -> None:
    assert _cashback_pln(500) == 5.0
    assert _cashback_pln("1250") == 12.5
    assert _cashback_pln(0) == 0.0
    assert _cashback_pln(None) is None
    assert _cashback_pln("invalid") is None


@pytest.mark.asyncio
async def test_coordinator_update_data_success() -> None:
    hass = MagicMock()
    entry = MagicMock()
    entry.options = {}
    entry.data = {}

    api = MagicMock()
    api.usage_sync = AsyncMock(return_value={})
    api.subscriptions = AsyncMock(
        return_value={
            "data": [
                {
                    "uuid": "sub-1",
                    "status": "ACTIVE",
                    "sim_cards": [
                        {
                            "uuid": "sim-1",
                            "phone_number": "+48111222333",
                            "usage": {"data_remaining_gb": 10.0, "data_total_gb": 20.0},
                        }
                    ],
                }
            ]
        }
    )
    api.subscription = AsyncMock(
        return_value={
            "data": {"orders": [{"id": 1}], "payment_method": {"type": "card"}}
        }
    )
    api.cashback = AsyncMock(
        return_value={"data": {"balance": 1500, "spendable": 1000}}
    )
    api.site_alerts = AsyncMock(return_value={"data": [{"id": 1, "text": "Alert"}]})
    api.cashback_transactions = AsyncMock(return_value={"data": []})

    coord = FoniaCoordinator(hass, entry, api)
    data = await coord._async_update_data()

    assert isinstance(data, FoniaData)
    assert len(data.subscriptions) == 1
    assert data.subscriptions[0].uuid == "sub-1"
    assert data.cashback_balance == 15.0
    assert data.cashback_spendable == 10.0
    assert len(data.site_alerts) == 1


@pytest.mark.asyncio
async def test_coordinator_usage_sync_failure_is_isolated() -> None:
    """A failure in usage_sync endpoint must not crash the entire coordinator update."""
    hass = MagicMock()
    entry = MagicMock()
    entry.options = {}
    entry.data = {}

    api = MagicMock()
    # usage_sync fails with 500
    api.usage_sync = AsyncMock(side_effect=FoniaApiError("HTTP 500"))
    api.subscriptions = AsyncMock(
        return_value={
            "data": [
                {
                    "uuid": "sub-1",
                    "sim_cards": [],
                }
            ]
        }
    )
    api.subscription = AsyncMock(return_value={"data": {}})
    api.cashback = AsyncMock(return_value={"data": {"balance": 2000}})
    api.site_alerts = AsyncMock(return_value={"data": []})
    api.cashback_transactions = AsyncMock(return_value={"data": []})

    coord = FoniaCoordinator(hass, entry, api)
    data = await coord._async_update_data()

    # Still successfully returned data despite usage_sync failure!
    assert len(data.subscriptions) == 1
    assert data.cashback_balance == 20.0


@pytest.mark.asyncio
async def test_coordinator_auth_error_raises_config_entry_auth_failed() -> None:
    hass = MagicMock()
    entry = MagicMock()
    entry.options = {}
    entry.data = {}

    api = MagicMock()
    api.usage_sync = AsyncMock(return_value={})
    api.subscriptions = AsyncMock(side_effect=FoniaAuthError("Authentication expired"))

    coord = FoniaCoordinator(hass, entry, api)
    with pytest.raises(ConfigEntryAuthFailed):
        await coord._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_manual_sync_usage_debounce() -> None:
    hass = MagicMock()
    entry = MagicMock()
    entry.options = {}
    entry.data = {}

    api = MagicMock()
    api.usage_sync = AsyncMock(return_value={})

    coord = FoniaCoordinator(hass, entry, api)
    coord.is_syncing_usage = True

    # When is_syncing_usage is True, call should return immediately without calling api.usage_sync
    await coord.async_sync_usage()
    api.usage_sync.assert_not_called()
