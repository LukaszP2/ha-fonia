from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from custom_components.fonia.const import CONF_PASSWORD, CONF_USERNAME
from custom_components.fonia.diagnostics import async_get_config_entry_diagnostics
from custom_components.fonia.models import FoniaData, Subscription


@pytest.mark.asyncio
async def test_diagnostics_redacts_credentials() -> None:
    hass = MagicMock()
    entry = MagicMock()
    entry.data = {
        CONF_USERNAME: "secret_user@example.com",
        CONF_PASSWORD: "super_secret_password",
    }
    entry.options = {"scan_interval": 15}

    coordinator = MagicMock()
    coordinator.last_usage_sync = datetime(2026, 11, 6, 10, 0, tzinfo=UTC)
    coordinator.last_details_update = None
    coordinator.last_account_update = None
    coordinator.last_update_success = True
    coordinator.scan_interval.total_seconds.return_value = 900
    coordinator.usage_sync_enabled = True

    sub = Subscription(
        uuid="sub-1",
        public_reference="REF1",
        status="active",
        operator="Fonia",
        billing_period="m",
        renewal_price=19.99,
        start_date=None,
        next_payment=None,
        tariff="Plan",
        billing_mode="prepaid",
        payment_mode="card",
        sims=[],
    )
    coordinator.data = FoniaData(
        subscriptions=[sub],
        cashback_balance=25.0,
        site_alerts=[],
    )
    entry.runtime_data = coordinator

    diag = await async_get_config_entry_diagnostics(hass, entry)

    # Secrets must be redacted
    assert diag["entry"][CONF_USERNAME] == "**REDACTED**"
    assert diag["entry"][CONF_PASSWORD] == "**REDACTED**"
    assert diag["options"]["scan_interval"] == 15
    assert diag["coordinator"]["subscriptions"] == 1
    assert diag["coordinator"]["cashback_available"] is True
