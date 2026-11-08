from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from custom_components.fonia import (
    _async_options_updated,
    _sync_blueprints,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.fonia.api import FoniaApiError, FoniaAuthError
from custom_components.fonia.const import CONF_PASSWORD, CONF_USERNAME


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        CONF_USERNAME: "jan@example.com",
        CONF_PASSWORD: "secret_password",
    }
    entry.options = {}
    entry.runtime_data = None
    entry.add_update_listener = MagicMock(return_value=lambda: None)
    entry.async_on_unload = MagicMock()
    return entry


@pytest.mark.asyncio
async def test_async_setup_entry_success(mock_entry) -> None:
    hass = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

    with (
        patch("custom_components.fonia.FoniaApi.login", new_callable=AsyncMock),
        patch(
            "custom_components.fonia.FoniaCoordinator.async_config_entry_first_refresh",
            new_callable=AsyncMock,
        ),
    ):
        result = await async_setup_entry(hass, mock_entry)

    assert result is True
    assert mock_entry.runtime_data is not None
    mock_entry.async_on_unload.assert_called_once()
    hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
        mock_entry, [Platform.SENSOR, Platform.BUTTON]
    )


@pytest.mark.asyncio
async def test_async_setup_entry_auth_failed(mock_entry) -> None:
    hass = MagicMock()

    with (
        patch(
            "custom_components.fonia.FoniaApi.login",
            new_callable=AsyncMock,
            side_effect=FoniaAuthError("Invalid credentials"),
        ),
        pytest.raises(ConfigEntryAuthFailed),
    ):
        await async_setup_entry(hass, mock_entry)


@pytest.mark.asyncio
async def test_async_setup_entry_not_ready(mock_entry) -> None:
    hass = MagicMock()

    with (
        patch(
            "custom_components.fonia.FoniaApi.login",
            new_callable=AsyncMock,
            side_effect=FoniaApiError("Connection timed out"),
        ),
        pytest.raises(ConfigEntryNotReady),
    ):
        await async_setup_entry(hass, mock_entry)


@pytest.mark.asyncio
async def test_async_unload_entry(mock_entry) -> None:
    hass = MagicMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    result = await async_unload_entry(hass, mock_entry)
    assert result is True
    hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        mock_entry, [Platform.SENSOR, Platform.BUTTON]
    )


@pytest.mark.asyncio
async def test_async_options_updated(mock_entry) -> None:
    hass = MagicMock()
    hass.config_entries.async_reload = AsyncMock()

    await _async_options_updated(hass, mock_entry)
    hass.config_entries.async_reload.assert_awaited_once_with("test_entry_id")


@pytest.mark.asyncio
async def test_async_setup(tmp_path) -> None:
    hass = MagicMock()
    hass.config.path.return_value = str(tmp_path / "blueprints")
    hass.services.has_service.return_value = False

    result = await async_setup(hass, {})
    assert result is True


def test_sync_blueprints(tmp_path) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "bp1.yaml").write_text("blueprint 1 content")

    dst_dir = tmp_path / "dst"

    # First sync copies new files
    assert _sync_blueprints(src_dir, dst_dir) is True
    assert (dst_dir / "bp1.yaml").exists()
    assert (dst_dir / "bp1.yaml").read_text() == "blueprint 1 content"

    # Second sync without changes returns False
    assert _sync_blueprints(src_dir, dst_dir) is False

    # Sync updates when source changes
    (src_dir / "bp1.yaml").write_text("blueprint 1 updated")
    assert _sync_blueprints(src_dir, dst_dir) is True
    assert (dst_dir / "bp1.yaml").read_text() == "blueprint 1 updated"
