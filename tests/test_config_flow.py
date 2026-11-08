from unittest.mock import MagicMock, patch

import pytest
from homeassistant.data_entry_flow import FlowResultType

from custom_components.fonia.api import (
    FoniaApiError,
    FoniaAuthError,
)
from custom_components.fonia.config_flow import FoniaConfigFlow, FoniaOptionsFlow
from custom_components.fonia.const import (
    CATEGORY_PAYMENTS,
    CATEGORY_USAGE,
    CONF_CATEGORIES,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USAGE_SYNC,
    CONF_USERNAME,
)


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.flow = MagicMock()
    hass.config_entries.flow._async_in_progress.return_value = []
    hass.config_entries.async_entry_for_domain_unique_id.return_value = None
    return hass


@pytest.mark.asyncio
async def test_config_flow_user_form(mock_hass) -> None:
    flow = FoniaConfigFlow()
    flow.hass = mock_hass
    flow.context = {}

    result = await flow.async_step_user(user_input=None)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_config_flow_user_success(mock_hass) -> None:
    flow = FoniaConfigFlow()
    flow.hass = mock_hass
    flow.context = {}

    with patch.object(
        flow,
        "_validate",
        return_value={
            "token": "tok123",
            "user": {"customer_number": "12345", "name": "Jan Kowalski"},
        },
    ):
        result = await flow.async_step_user(
            user_input={CONF_USERNAME: "jan@example.com", CONF_PASSWORD: "secret"}
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Jan Kowalski"
    assert result["data"] == {
        CONF_USERNAME: "jan@example.com",
        CONF_PASSWORD: "secret",
    }


@pytest.mark.asyncio
async def test_config_flow_user_with_custom_name(mock_hass) -> None:
    flow = FoniaConfigFlow()
    flow.hass = mock_hass
    flow.context = {}

    with patch.object(
        flow,
        "_validate",
        return_value={
            "token": "tok123",
            "user": {
                "customer_number": "12345",
                "name": "user_695a143c58e43",
                "email": "jan@example.com",
            },
        },
    ):
        result = await flow.async_step_user(
            user_input={
                CONF_USERNAME: "jan@example.com",
                CONF_PASSWORD: "secret",
                CONF_NAME: "Moja Karta Fonia",
            }
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Moja Karta Fonia"


@pytest.mark.asyncio
async def test_config_flow_user_falls_back_from_user_prefix(mock_hass) -> None:
    flow = FoniaConfigFlow()
    flow.hass = mock_hass
    flow.context = {}

    with patch.object(
        flow,
        "_validate",
        return_value={
            "token": "tok123",
            "user": {
                "customer_number": "12345",
                "name": "user_695a143c58e43",
                "email": "jan@example.com",
            },
        },
    ):
        result = await flow.async_step_user(
            user_input={CONF_USERNAME: "jan@example.com", CONF_PASSWORD: "secret"}
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "jan@example.com"


@pytest.mark.asyncio
async def test_config_flow_user_invalid_auth(mock_hass) -> None:
    flow = FoniaConfigFlow()
    flow.hass = mock_hass

    with patch.object(flow, "_validate", side_effect=FoniaAuthError):
        result = await flow.async_step_user(
            user_input={CONF_USERNAME: "jan@example.com", CONF_PASSWORD: "wrong"}
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


@pytest.mark.asyncio
async def test_config_flow_user_cannot_connect(mock_hass) -> None:
    flow = FoniaConfigFlow()
    flow.hass = mock_hass

    with patch.object(flow, "_validate", side_effect=FoniaApiError):
        result = await flow.async_step_user(
            user_input={CONF_USERNAME: "jan@example.com", CONF_PASSWORD: "wrong"}
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.asyncio
async def test_config_flow_reauth_verify_same_account(mock_hass) -> None:
    flow = FoniaConfigFlow()
    flow.hass = mock_hass

    entry = MagicMock()
    entry.unique_id = "12345"
    entry.data = {CONF_USERNAME: "jan@example.com", CONF_PASSWORD: "old"}
    flow._reauth_entry = entry

    # Same account -> Success
    with patch.object(
        flow,
        "_validate",
        return_value={
            "token": "new-tok",
            "user": {"customer_number": "12345", "name": "Jan"},
        },
    ):
        result = await flow.async_step_reauth_confirm(
            user_input={CONF_USERNAME: "jan@example.com", CONF_PASSWORD: "new_pass"}
        )

    assert result["type"] == FlowResultType.ABORT


@pytest.mark.asyncio
async def test_config_flow_reauth_reject_different_account(mock_hass) -> None:
    flow = FoniaConfigFlow()
    flow.hass = mock_hass

    entry = MagicMock()
    entry.unique_id = "12345"
    entry.data = {CONF_USERNAME: "jan@example.com", CONF_PASSWORD: "old"}
    flow._reauth_entry = entry

    # Different account ID 99999 -> Must be rejected with wrong_account
    with patch.object(
        flow,
        "_validate",
        return_value={
            "token": "tok",
            "user": {"customer_number": "99999", "name": "Inna Osoba"},
        },
    ):
        result = await flow.async_step_reauth_confirm(
            user_input={CONF_USERNAME: "inna@example.com", CONF_PASSWORD: "password"}
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "wrong_account"}


@pytest.mark.asyncio
async def test_config_flow_reconfigure_success(mock_hass) -> None:
    flow = FoniaConfigFlow()
    flow.hass = mock_hass

    entry = MagicMock()
    entry.unique_id = "12345"
    entry.data = {CONF_USERNAME: "jan@example.com", CONF_PASSWORD: "old"}

    with (
        patch.object(flow, "_get_reconfigure_entry", return_value=entry),
        patch.object(
            flow,
            "_validate",
            return_value={
                "token": "new-tok",
                "user": {"customer_number": "12345", "name": "Jan"},
            },
        ),
    ):
        result = await flow.async_step_reconfigure(
            user_input={
                CONF_USERNAME: "jan@example.com",
                CONF_PASSWORD: "new_password",
                CONF_NAME: "Nowa Nazwa Fonia",
            }
        )

    assert result["type"] == FlowResultType.ABORT
    mock_hass.config_entries.async_update_entry.assert_called_once_with(
        entry, title="Nowa Nazwa Fonia"
    )


@pytest.mark.asyncio
async def test_options_flow(mock_hass) -> None:
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.title = "user_695a143c58e43"
    entry.options = {}
    mock_hass.config_entries.async_get_known_entry.return_value = entry

    flow = FoniaOptionsFlow()
    flow.handler = entry.entry_id
    flow.hass = mock_hass

    result = await flow.async_step_init(user_input=None)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    result2 = await flow.async_step_init(
        user_input={
            CONF_NAME: "Własna Nazwa",
            CONF_SCAN_INTERVAL: 30,
            CONF_USAGE_SYNC: True,
            CONF_CATEGORIES: [CATEGORY_PAYMENTS, CATEGORY_USAGE],
        }
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_CATEGORIES] == [CATEGORY_PAYMENTS, CATEGORY_USAGE]
    mock_hass.config_entries.async_update_entry.assert_called_once_with(
        entry, title="Własna Nazwa"
    )
