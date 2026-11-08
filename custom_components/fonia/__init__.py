from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FoniaApi, FoniaApiError, FoniaAuthError
from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN
from .coordinator import FoniaCoordinator

_LOGGER = logging.getLogger(__name__)

FoniaConfigEntry: TypeAlias = ConfigEntry[FoniaCoordinator]


def _sync_blueprints(source_dir: Path, target_dir: Path) -> bool:
    """Synchronize blueprints from the component folder to HA blueprints folder."""
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        updated = False
        for src_file in source_dir.glob("*.yaml"):
            dst_file = target_dir / src_file.name
            if not dst_file.exists() or dst_file.read_bytes() != src_file.read_bytes():
                shutil.copy2(src_file, dst_file)
                updated = True
        return updated
    except OSError as err:
        _LOGGER.warning("Could not synchronize Fonia blueprints: %s", err)
        return False


async def _async_deploy_blueprints(hass: HomeAssistant) -> None:
    """Deploy blueprints if not already present or if updated."""
    source_dir = Path(__file__).parent / "blueprints"
    if not source_dir.is_dir():
        return

    target_path_fn = getattr(getattr(hass, "config", None), "path", None)
    if not callable(target_path_fn):
        return

    try:
        target_dir = Path(target_path_fn("blueprints", "automation", DOMAIN))
    except (AttributeError, TypeError):
        return

    add_job = getattr(hass, "async_add_executor_job", None)
    if not callable(add_job):
        return

    try:
        job = add_job(_sync_blueprints, source_dir, target_dir)
        updated = await job if hasattr(job, "__await__") else job

        if (
            updated
            and hasattr(hass, "services")
            and hasattr(hass.services, "has_service")
            and callable(hass.services.has_service)
            and hass.services.has_service("automation", "reload")
        ):
            call = hass.services.async_call("automation", "reload", blocking=False)
            if hasattr(call, "__await__"):
                await call
    except (OSError, RuntimeError) as err:
        _LOGGER.debug("Skipping blueprint auto-deploy: %s", err)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Fonia integration component."""
    await _async_deploy_blueprints(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: FoniaConfigEntry) -> bool:
    """Set up Fonia from a config entry."""
    await _async_deploy_blueprints(hass)

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
