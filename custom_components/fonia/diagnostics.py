from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data

from . import FoniaConfigEntry
from .const import CONF_PASSWORD, CONF_USERNAME

TO_REDACT = {CONF_PASSWORD, CONF_USERNAME}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: FoniaConfigEntry
) -> dict[str, Any]:
    """Return non-sensitive diagnostics for a Fonia config entry."""
    coordinator = entry.runtime_data
    data = coordinator.data
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "coordinator": {
            "subscriptions": len(data.subscriptions),
            "sims": sum(len(item.sims) for item in data.subscriptions),
            "cashback_available": data.cashback_balance is not None,
            "site_alerts": len(data.site_alerts),
            "last_usage_sync": coordinator.last_usage_sync.isoformat()
            if coordinator.last_usage_sync
            else None,
            "last_details_update": coordinator.last_details_update.isoformat()
            if coordinator.last_details_update
            else None,
            "last_account_update": coordinator.last_account_update.isoformat()
            if coordinator.last_account_update
            else None,
            "last_update_success": coordinator.last_update_success,
            "scan_interval_seconds": int(coordinator.scan_interval.total_seconds()),
            "usage_sync_enabled": coordinator.usage_sync_enabled,
        },
        "subscriptions": [
            {
                "public_reference": item.public_reference,
                "status": item.status,
                "operator": item.operator,
                "tariff": item.tariff,
                "billing_period": item.billing_period,
                "sim_count": len(item.sims),
            }
            for item in data.subscriptions
        ],
    }
