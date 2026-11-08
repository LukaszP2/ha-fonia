from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

try:
    from homeassistant.helpers.device_registry import ChildDeviceInfo

    _CHILD_DEVICE_SUPPORTED = True
except ImportError:  # HA < 2026.x
    _CHILD_DEVICE_SUPPORTED = False

from .const import (
    ALL_CATEGORIES,
    CATEGORY_ADVANCED,
    CATEGORY_CORE,
    CATEGORY_HISTORY,
    CATEGORY_PAYMENTS,
    CATEGORY_USAGE,
    CONF_CATEGORIES,
    DOMAIN,
)
from .coordinator import FoniaCoordinator
from .models import FoniaData, Sim, Subscription

SensorScope = Literal["subscription", "sim", "account"]


@dataclass(frozen=True, kw_only=True)
class FoniaSensorDescription(SensorEntityDescription):
    """Describe a Fonia sensor."""

    value_fn: Callable[[FoniaData, Subscription | None, Sim | None], Any]
    scope: SensorScope = "subscription"
    enabled_by_default: bool = True
    entity_category: EntityCategory | None = None
    category: str = CATEGORY_CORE


SENSORS: tuple[FoniaSensorDescription, ...] = (
    FoniaSensorDescription(
        key="status",
        translation_key="status",
        value_fn=lambda _, sub, __: sub.status if sub else None,
        category=CATEGORY_CORE,
    ),
    FoniaSensorDescription(
        key="next_payment",
        translation_key="next_payment",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda _, sub, __: sub.next_payment if sub else None,
        category=CATEGORY_PAYMENTS,
    ),
    FoniaSensorDescription(
        key="renewal_price",
        translation_key="renewal_price",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="PLN",
        value_fn=lambda _, sub, __: sub.renewal_price if sub else None,
        category=CATEGORY_PAYMENTS,
    ),
    FoniaSensorDescription(
        key="data_remaining",
        translation_key="data_remaining",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _, __, sim: sim.data_remaining if sim else None,
        scope="sim",
        category=CATEGORY_CORE,
    ),
    FoniaSensorDescription(
        key="data_total",
        translation_key="data_total",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _, __, sim: sim.data_total if sim else None,
        scope="sim",
        enabled_by_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        category=CATEGORY_USAGE,
    ),
    FoniaSensorDescription(
        key="data_used_percentage",
        translation_key="data_used_percentage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _, __, sim: _used_percentage(sim),
        scope="sim",
        category=CATEGORY_USAGE,
    ),
    FoniaSensorDescription(
        key="order_count",
        translation_key="order_count",
        value_fn=lambda data, sub, __: (
            len(data.orders.get(sub.uuid, [])) if sub else None
        ),
        enabled_by_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        category=CATEGORY_PAYMENTS,
    ),
    FoniaSensorDescription(
        key="roaming_data_remaining",
        translation_key="roaming_data_remaining",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _, __, sim: sim.roaming_data_remaining if sim else None,
        scope="sim",
        category=CATEGORY_USAGE,
    ),
    FoniaSensorDescription(
        key="roaming_data_total",
        translation_key="roaming_data_total",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _, __, sim: sim.roaming_data_total if sim else None,
        scope="sim",
        enabled_by_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        category=CATEGORY_USAGE,
    ),
    FoniaSensorDescription(
        key="roaming_data_used_percentage",
        translation_key="roaming_data_used_percentage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _, __, sim: _roaming_used_percentage(sim),
        scope="sim",
        category=CATEGORY_USAGE,
    ),
)

ACCOUNT_SENSORS: tuple[FoniaSensorDescription, ...] = (
    FoniaSensorDescription(
        key="cashback_balance",
        translation_key="cashback_balance",
        native_unit_of_measurement="PLN",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data, _, __: data.cashback_balance,
        scope="account",
        category=CATEGORY_CORE,
    ),
    FoniaSensorDescription(
        key="cashback_spendable",
        translation_key="cashback_spendable",
        native_unit_of_measurement="PLN",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data, _, __: data.cashback_spendable,
        scope="account",
        category=CATEGORY_CORE,
    ),
    FoniaSensorDescription(
        key="cashback_transaction_count",
        translation_key="cashback_transaction_count",
        value_fn=lambda data, _, __: len(data.cashback_transactions),
        scope="account",
        enabled_by_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        category=CATEGORY_HISTORY,
    ),
    FoniaSensorDescription(
        key="site_alert_count",
        translation_key="site_alert_count",
        value_fn=lambda data, _, __: len(data.site_alerts),
        scope="account",
        enabled_by_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        category=CATEGORY_ADVANCED,
    ),
)

SENSORS_BY_KEY: dict[str, FoniaSensorDescription] = {
    sensor.key: sensor for sensor in SENSORS
}

PARALLEL_UPDATES = 0


class FoniaSensor(CoordinatorEntity[FoniaCoordinator], SensorEntity):
    """Representation of a Fonia sensor."""

    entity_description: FoniaSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FoniaCoordinator,
        entry: ConfigEntry,
        description: FoniaSensorDescription,
        subscription: Subscription | None = None,
        sim: Sim | None = None,
        parent_device_id: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self.entity_description = description
        self._subscription_id = subscription.uuid if subscription else None
        self._sim_id = sim.uuid if sim else None
        scope_id = (
            f"sim_{self._sim_id}"
            if self._sim_id
            else (
                f"sub_{self._subscription_id}"
                if self._subscription_id
                else f"account_{entry.entry_id}"
            )
        )
        self._attr_unique_id = f"{scope_id}_{description.key}"
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = description.enabled_by_default
        self._attr_device_info = _device_info(
            entry, subscription, sim, description.scope, parent_device_id
        )

    def _items(self) -> tuple[Subscription | None, Sim | None]:
        if not self._subscription_id:
            return None, None
        subscription = next(
            (
                item
                for item in self.coordinator.data.subscriptions
                if item.uuid == self._subscription_id
            ),
            None,
        )
        sim = (
            next(
                (item for item in subscription.sims if item.uuid == self._sim_id), None
            )
            if subscription and self._sim_id
            else None
        )
        return subscription, sim

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        subscription, sim = self._items()
        if self.entity_description.scope == "sim":
            return sim is not None
        if self.entity_description.scope == "subscription":
            return subscription is not None
        return True

    @property
    def native_value(self) -> Any:
        subscription, sim = self._items()
        return self.entity_description.value_fn(
            self.coordinator.data, subscription, sim
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        subscription, sim = self._items()
        if not subscription:
            if self.entity_description.scope != "account":
                return None
            if self.entity_description.key == "site_alert_count":
                return {"site_alerts": self.coordinator.data.site_alerts}
            if self.entity_description.key == "cashback_transaction_count":
                return {
                    "latest_transaction": _latest_order(
                        self.coordinator.data.cashback_transactions
                    )
                }
            return None

        # Only expose metadata attributes on the primary status sensor to avoid
        # recorder bloat and unnecessary duplication on every sensor.
        if self.entity_description.key != "status":
            return None

        attributes: dict[str, Any] = {
            "public_reference": subscription.public_reference,
            "operator": subscription.operator or (sim.operator if sim else None),
            "tariff": subscription.tariff or (sim.tariff if sim else None),
            "billing_period": subscription.billing_period,
            "billing_mode": subscription.billing_mode,
            "subscription_payment_mode": subscription.payment_mode,
        }
        if sim:
            attributes.update(
                phone_number=sim.phone_number,
                sim_status=sim.status,
            )
        orders = self.coordinator.data.orders.get(subscription.uuid)
        if orders:
            attributes["latest_order"] = _latest_order(orders)
        return {key: value for key, value in attributes.items() if value is not None}


def _account_device_info(entry: ConfigEntry) -> DeviceInfo:
    """DeviceInfo for the top-level account device."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"account_{entry.entry_id}")},
        name="Fonia",
        manufacturer="Fonia",
        model="Konto",
    )


def _sim_device_info(
    entry: ConfigEntry,
    sim: Sim,
    parent_device_id: str | None = None,
) -> DeviceInfo:
    """DeviceInfo for a SIM / phone-number child device.

    Uses ChildDeviceInfo (HA ≥ 2026.x) when available so the phone number
    is modeled as a component part of the account device.
    Falls back to via_device on older HA versions.
    """
    name = f"Fonia · {sim.phone_number}" if sim.phone_number else "Fonia · SIM"
    identifiers: set[tuple[str, str]] = {(DOMAIN, f"sim_{sim.uuid}")}

    if _CHILD_DEVICE_SUPPORTED and parent_device_id:
        return ChildDeviceInfo(  # type: ignore[return-value]
            identifiers=identifiers,
            name=name,
            parent_device_id=parent_device_id,
        )

    # Fallback for HA < 2026.x — via_device is the closest available relation.
    return DeviceInfo(
        identifiers=identifiers,
        name=name,
        manufacturer="Fonia",
        model="Karta SIM",
        via_device=(DOMAIN, f"account_{entry.entry_id}"),
    )


def _subscription_device_info(
    entry: ConfigEntry,
    subscription: Subscription,
    parent_device_id: str | None = None,
) -> DeviceInfo:
    """DeviceInfo for a standalone subscription child device (no SIM card)."""
    name = (
        f"Fonia · {subscription.public_reference}"
        if subscription.public_reference
        else "Fonia · Subskrypcja"
    )
    identifiers: set[tuple[str, str]] = {(DOMAIN, f"sub_{subscription.uuid}")}

    if _CHILD_DEVICE_SUPPORTED and parent_device_id:
        return ChildDeviceInfo(  # type: ignore[return-value]
            identifiers=identifiers,
            name=name,
            parent_device_id=parent_device_id,
        )

    # Fallback for HA < 2026.x — via_device is the closest available relation.
    return DeviceInfo(
        identifiers=identifiers,
        name=name,
        manufacturer="Fonia",
        model="Subskrypcja",
        via_device=(DOMAIN, f"account_{entry.entry_id}"),
    )


def _device_info(
    entry: ConfigEntry,
    subscription: Subscription | None,
    sim: Sim | None,
    scope: SensorScope,
    parent_device_id: str | None = None,
) -> DeviceInfo:
    if scope == "account":
        return _account_device_info(entry)
    if sim is not None:
        return _sim_device_info(entry, sim, parent_device_id)
    if subscription is not None:
        return _subscription_device_info(entry, subscription, parent_device_id)
    return _account_device_info(entry)


def _used_percentage(sim: Sim | None) -> float | None:
    if (
        not sim
        or sim.data_total is None
        or sim.data_remaining is None
        or sim.data_total <= 0
    ):
        return None
    return round(
        max(
            0.0,
            min(100.0, (sim.data_total - sim.data_remaining) / sim.data_total * 100),
        ),
        1,
    )


def _roaming_used_percentage(sim: Sim | None) -> float | None:
    """Calculate roaming package usage percentage when both values exist."""
    if (
        not sim
        or sim.roaming_data_total is None
        or sim.roaming_data_remaining is None
        or sim.roaming_data_total <= 0
    ):
        return None
    used = (
        (sim.roaming_data_total - sim.roaming_data_remaining)
        / sim.roaming_data_total
        * 100
    )
    return round(max(0.0, min(100.0, used)), 1)


def _latest_order(orders: list[dict[str, Any]]) -> dict[str, Any]:
    if not orders:
        return {}
    latest = max(
        orders,
        key=lambda item: str(
            item.get("created_at") or item.get("date") or item.get("id") or ""
        ),
    )
    result = {
        key: latest.get(key)
        for key in (
            "id",
            "uuid",
            "status",
            "created_at",
            "date",
            "type",
        )
        if latest.get(key) is not None
    }
    for amount_key in ("amount", "total", "amount_pln"):
        if amount_key in latest and latest[amount_key] is not None:
            raw_val = latest[amount_key]
            try:
                result[amount_key] = round(float(raw_val), 2)
            except (TypeError, ValueError):
                result[amount_key] = raw_val
    return result


def _build_entities(
    coordinator: FoniaCoordinator,
    entry: ConfigEntry,
    parent_device_id: str,
) -> list[FoniaSensor]:
    """Build account entities and group subscription data under each phone."""
    enabled_categories = set(entry.options.get(CONF_CATEGORIES, ALL_CATEGORIES))
    enabled_categories.add(CATEGORY_CORE)

    entities: list[FoniaSensor] = [
        FoniaSensor(coordinator, entry, description)
        for description in ACCOUNT_SENSORS
        if description.category in enabled_categories
    ]
    for subscription in coordinator.data.subscriptions:
        if subscription.sims:
            for sim in subscription.sims:
                common = {
                    "subscription": subscription,
                    "sim": sim,
                    "parent_device_id": parent_device_id,
                }
                for sensor_desc in SENSORS:
                    if sensor_desc.category in enabled_categories:
                        entities.append(
                            FoniaSensor(coordinator, entry, sensor_desc, **common)
                        )
        else:
            for sensor_desc in SENSORS:
                if (
                    sensor_desc.scope == "subscription"
                    and sensor_desc.category in enabled_categories
                ):
                    entities.append(
                        FoniaSensor(
                            coordinator,
                            entry,
                            sensor_desc,
                            subscription=subscription,
                            sim=None,
                            parent_device_id=parent_device_id,
                        )
                    )
    return entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[FoniaCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors and discover new subscriptions/SIMs during polling."""
    coordinator: FoniaCoordinator = entry.runtime_data
    known_unique_ids: set[str] = set()

    # Ensure the account (parent) device exists in the registry before any
    # child SIM device is registered; ChildDeviceInfo requires the parent's
    # internal device-registry ID, not its identifiers tuple.
    device_registry = dr.async_get(hass)
    account_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"account_{entry.entry_id}")},
        name="Fonia",
        manufacturer="Fonia",
        model="Konto",
    )

    def add_missing_entities() -> None:
        new_entities = [
            entity
            for entity in _build_entities(coordinator, entry, account_device.id)
            if entity.unique_id not in known_unique_ids
        ]
        if new_entities:
            known_unique_ids.update(entity.unique_id for entity in new_entities)
            async_add_entities(new_entities)

    add_missing_entities()
    entry.async_on_unload(coordinator.async_add_listener(add_missing_entities))
