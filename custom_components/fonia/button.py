from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import FoniaApiError, FoniaAuthError
from .const import DOMAIN
from .coordinator import FoniaCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


class FoniaUsageSyncButton(CoordinatorEntity[FoniaCoordinator], ButtonEntity):
    """Trigger a fresh usage synchronization at Fonia."""

    _attr_has_entity_name = True
    _attr_translation_key = "usage_sync"

    def __init__(self, coordinator: FoniaCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "account_usage_sync"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "account")},
            name="Fonia",
            manufacturer="Fonia",
            model="Konto",
        )

    async def async_press(self) -> None:
        """Synchronize usage and refresh data."""
        try:
            await self.coordinator.async_sync_usage()
        except FoniaAuthError:
            self.coordinator.entry.async_start_reauth(self.coordinator.hass)
            return
        except FoniaApiError as err:
            _LOGGER.warning("Fonia usage synchronization failed: %s", err)
            return
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[FoniaCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Fonia buttons."""
    async_add_entities([FoniaUsageSyncButton(entry.runtime_data)])
