from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.helpers.entity import EntityCategory

from custom_components.fonia.api import FoniaAuthError
from custom_components.fonia.button import FoniaUsageSyncButton
from custom_components.fonia.const import DOMAIN


@pytest.mark.asyncio
async def test_button_press_success() -> None:
    coordinator = MagicMock()
    coordinator.is_syncing_usage = False
    coordinator.async_sync_usage = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()

    entry = MagicMock()
    entry.entry_id = "test_entry_id"

    button = FoniaUsageSyncButton(coordinator, entry)
    assert button.unique_id == "test_entry_id_usage_sync"
    assert button.device_info["identifiers"] == {(DOMAIN, "account_test_entry_id")}
    assert button.entity_category == EntityCategory.DIAGNOSTIC

    await button.async_press()

    coordinator.async_sync_usage.assert_awaited_once()
    coordinator.async_request_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_button_press_debounced() -> None:
    coordinator = MagicMock()
    coordinator.is_syncing_usage = True
    coordinator.async_sync_usage = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()

    entry = MagicMock()
    entry.entry_id = "test_entry_id"

    button = FoniaUsageSyncButton(coordinator, entry)
    await button.async_press()

    # Did not invoke sync because already syncing!
    coordinator.async_sync_usage.assert_not_called()
    coordinator.async_request_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_button_press_auth_error_triggers_reauth() -> None:
    coordinator = MagicMock()
    coordinator.is_syncing_usage = False
    coordinator.async_sync_usage = AsyncMock(side_effect=FoniaAuthError)
    coordinator.entry = MagicMock()
    coordinator.hass = MagicMock()

    entry = MagicMock()
    entry.entry_id = "test_entry_id"

    button = FoniaUsageSyncButton(coordinator, entry)
    await button.async_press()

    coordinator.entry.async_start_reauth.assert_called_once_with(coordinator.hass)
