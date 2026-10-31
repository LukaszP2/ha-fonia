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
from homeassistant.helpers.device_registry import ChildDeviceInfo, DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
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


SENSORS: tuple[FoniaSensorDescription, ...] = (
    FoniaSensorDescription(
        key="status",
        translation_key="status",
        value_fn=lambda _, sub, __: sub.status if sub else None,
    ),
    FoniaSensorDescription(
        key="next_payment",
        translation_key="next_payment",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda _, sub, __: sub.next_payment if sub else None,
    ),
    FoniaSensorDescription(
        key="renewal_price",
        translation_key="renewal_price",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="PLN",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _, sub, __: sub.renewal_price if sub else None,
    ),
    FoniaSensorDescription(
        key="data_remaining",
        translation_key="data_remaining",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _, __, sim: sim.data_remaining if sim else None,
        scope="sim",
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
    ),
    FoniaSensorDescription(
        key="data_used_percentage",
        translation_key="data_used_percentage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _, __, sim: _used_percentage(sim),
        scope="sim",
    ),
    FoniaSensorDescription(
        key="order_count",
        translation_key="order_count",
        value_fn=lambda data, sub, __: (
            len(data.orders.get(sub.uuid, [])) if sub else None
        ),
        enabled_by_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FoniaSensorDescription(
        key="roaming_data_remaining",
        translation_key="roaming_data_remaining",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _, __, sim: sim.roaming_data_remaining if sim else None,
        scope="sim",
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
    ),
    FoniaSensorDescription(
        key="roaming_data_used_percentage",
        translation_key="roaming_data_used_percentage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _, __, sim: _roaming_used_percentage(sim),
        scope="sim",
    ),
)

ACCOUNT_SENSORS: tuple[FoniaSensorDescription, ...] = (
    FoniaSensorDescription(
        key="cashback_balance",
        translation_key="cashback_balance",
        native_unit_of_measurement="PLN",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, _, __: data.cashback_balance,
        scope="account",
    ),
    FoniaSensorDescription(
        key="cashback_spendable",
        translation_key="cashback_spendable",
        native_unit_of_measurement="PLN",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, _, __: data.cashback_spendable,
        scope="account",
    ),
    FoniaSensorDescription(
        key="cashback_transaction_count",
        translation_key="cashback_transaction_count",
        value_fn=lambda data, _, __: len(data.cashback_transactions),
        scope="account",
        enabled_by_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FoniaSensorDescription(
        key="site_alert_count",
        translation_key="site_alert_count",
        value_fn=lambda data, _, __: len(data.site_alerts),
        scope="account",
        enabled_by_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
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
        description: FoniaSensorDescription,
        subscription: Subscription | None = None,
        sim: Sim | None = None,
        parent_device_id: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._subscription_id = subscription.uuid if subscription else None
        self._sim_id = sim.uuid if sim else None
        # All phone-specific entities use the SIM UUID. This keeps each
        # phone's subscription and usage data together on one HA device.
        scope_id = self._sim_id or self._subscription_id or "account"
        self._attr_unique_id = f"{scope_id}_{description.key}"
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = description.enabled_by_default
        self._attr_device_info = _device_info(
            subscription, sim, description.scope, parent_device_id
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
                data_total_gb=sim.data_total,
                roaming_data_remaining_gb=sim.roaming_data_remaining,
                roaming_data_total_gb=sim.roaming_data_total,
                packages=sim.packages,
                agreement_number=sim.agreement_number,
                iccid=sim.iccid,
                crm_reference=sim.crm_reference,
            )
        payment_method = self.coordinator.data.payment_methods.get(subscription.uuid)
        if payment_method:
            safe = {
                key: payment_method.get(key)
                for key in ("type", "brand", "last4", "expiry_month", "expiry_year")
                if payment_method.get(key) is not None
            }
            attributes["payment_method"] = safe
        orders = self.coordinator.data.orders.get(subscription.uuid)
        if orders:
            attributes["latest_order"] = _latest_order(orders)
        return {key: value for key, value in attributes.items() if value is not None}


def _device_info(
    subscription: Subscription | None,
    sim: Sim | None,
    scope: SensorScope,
    parent_device_id: str | None = None,
) -> DeviceInfo | ChildDeviceInfo:
    if scope == "account":
        return DeviceInfo(
            identifiers={(DOMAIN, "account")},
            name="Fonia",
            manufacturer="Fonia",
            model="Konto",
        )
    if sim:
        # A phone/SIM is a logical child of the Fonia account, not a separate
        # top-level device. Home Assistant 2026.9+ models this with
        # ChildDeviceInfo.parent_device_id (not via_device_id).
        if parent_device_id is None:
            raise ValueError(
                "Fonia account device must be registered before SIM devices"
            )
        return ChildDeviceInfo(
            identifiers={(DOMAIN, f"sim_{sim.uuid}")},
            name=f"Fonia · {sim.phone_number}" if sim.phone_number else "Fonia · SIM",
            parent_device_id=parent_device_id,
        )
    # Subscription-only entities are not exposed as separate devices. In the
    # user-facing device model, subscriptions are an internal API concept and
    # their useful values are represented on each phone's device instead.
    return DeviceInfo(
        identifiers={(DOMAIN, "account")},
        name="Fonia",
        manufacturer="Fonia",
        model="Konto",
    )


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
    return {
        key: latest.get(key)
        for key in (
            "id",
            "uuid",
            "status",
            "created_at",
            "date",
            "amount",
            "total",
            "type",
        )
        if latest.get(key) is not None
    }


def _build_entities(
    coordinator: FoniaCoordinator,
    parent_device_id: str,
) -> list[FoniaSensor]:
    """Build account entities and group subscription data under each phone."""
    entities = [
        FoniaSensor(coordinator, description) for description in ACCOUNT_SENSORS
    ]
    for subscription in coordinator.data.subscriptions:
        # Subscription values are presented on each associated phone device.
        for sim in subscription.sims:
            common = {
                "subscription": subscription,
                "sim": sim,
                "parent_device_id": parent_device_id,
            }
            if subscription.status is not None:
                entities.append(
                    FoniaSensor(coordinator, SENSORS_BY_KEY["status"], **common)
                )
            if subscription.next_payment is not None:
                entities.append(
                    FoniaSensor(coordinator, SENSORS_BY_KEY["next_payment"], **common)
                )
            if subscription.renewal_price is not None:
                entities.append(
                    FoniaSensor(coordinator, SENSORS_BY_KEY["renewal_price"], **common)
                )
            if coordinator.data.orders.get(subscription.uuid):
                entities.append(
                    FoniaSensor(coordinator, SENSORS_BY_KEY["order_count"], **common)
                )
            if sim.data_remaining is not None:
                entities.append(
                    FoniaSensor(coordinator, SENSORS_BY_KEY["data_remaining"], **common)
                )
            if sim.data_total is not None:
                entities.append(
                    FoniaSensor(coordinator, SENSORS_BY_KEY["data_total"], **common)
                )
            if sim.data_total is not None and sim.data_remaining is not None:
                entities.append(
                    FoniaSensor(
                        coordinator, SENSORS_BY_KEY["data_used_percentage"], **common
                    )
                )
            if sim.roaming_data_remaining is not None:
                entities.append(
                    FoniaSensor(
                        coordinator, SENSORS_BY_KEY["roaming_data_remaining"], **common
                    )
                )
            if sim.roaming_data_total is not None:
                entities.append(
                    FoniaSensor(
                        coordinator, SENSORS_BY_KEY["roaming_data_total"], **common
                    )
                )
            if (
                sim.roaming_data_total is not None
                and sim.roaming_data_remaining is not None
            ):
                entities.append(
                    FoniaSensor(
                        coordinator,
                        SENSORS_BY_KEY["roaming_data_used_percentage"],
                        **common,
                    )
                )
    return entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[FoniaCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors and discover new subscriptions/SIMs during polling."""
    coordinator: FoniaCoordinator = entry.runtime_data
    known_unique_ids: set[str] = set()
    device_registry = dr.async_get(hass)

    def add_missing_entities() -> None:
        # The account is the only parent-level device. Each phone is a direct,
        # standalone device; subscription records stay internal to the API model.
        account_device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, "account")},
            name="Fonia",
            manufacturer="Fonia",
            model="Konto",
        )
        for subscription in coordinator.data.subscriptions:
            for sim in subscription.sims:
                device_registry.async_get_or_create_child(
                    config_entry_id=entry.entry_id,
                    identifiers={(DOMAIN, f"sim_{sim.uuid}")},
                    name=f"Fonia · {sim.phone_number}"
                    if sim.phone_number
                    else "Fonia · SIM",
                    parent_device_id=account_device.id,
                )

        new_entities = [
            entity
            for entity in _build_entities(coordinator, account_device.id)
            if entity.unique_id not in known_unique_ids
        ]
        if new_entities:
            known_unique_ids.update(entity.unique_id for entity in new_entities)
            async_add_entities(new_entities)

    add_missing_entities()
    entry.async_on_unload(coordinator.async_add_listener(add_missing_entities))
