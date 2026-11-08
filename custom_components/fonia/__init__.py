from __future__ import annotations

from typing import TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FoniaApi, FoniaApiError, FoniaAuthError
from .const import CONF_PASSWORD, CONF_USERNAME
from .coordinator import FoniaCoordinator

FoniaConfigEntry: TypeAlias = ConfigEntry[FoniaCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: FoniaConfigEntry) -> bool:
    """Set up Fonia from a config entry."""
    api = FoniaApi(
        async_get_clientsession(hass),
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
    )
    try:
        await api.login()
    except FoniaAuthError as err:
        raise ConfigEntryAuthFailed("Fonia authentication failed") from err
    except FoniaApiError as err:
        raise ConfigEntryNotReady("Unable to connect to Fonia") from err

    coordinator = FoniaCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(
        entry, [Platform.SENSOR, Platform.BUTTON]
    )
    return True


async def _async_options_updated(hass: HomeAssistant, entry: FoniaConfigEntry) -> None:
    """Reload the integration after options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: FoniaConfigEntry) -> bool:
    """Unload Fonia config entry."""
    return await hass.config_entries.async_unload_platforms(
        entry, [Platform.SENSOR, Platform.BUTTON]
    )
