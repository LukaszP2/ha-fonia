from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


def _date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(slots=True)
class Sim:
    uuid: str
    phone_number: str | None
    operator: str | None
    status: str | None
    tariff: str | None
    data_remaining: float | None
    data_total: float | None
    roaming_data_remaining: float | None = None
    roaming_data_total: float | None = None
    packages: list[dict[str, Any]] = field(default_factory=list)
    agreement_number: str | None = None
    iccid: str | None = None
    crm_reference: str | None = None


@dataclass(slots=True)
class Subscription:
    uuid: str
    public_reference: str | None
    status: str | None
    operator: str | None
    billing_period: str | None
    renewal_price: float | None
    start_date: date | None
    next_payment: date | None
    tariff: str | None
    billing_mode: str | None
    payment_mode: str | None
    sims: list[Sim] = field(default_factory=list)


@dataclass(slots=True)
class FoniaData:
    subscriptions: list[Subscription] = field(default_factory=list)
    cashback_balance: float | None = None
    cashback_spendable: float | None = None
    cashback_transactions: list[dict[str, Any]] = field(default_factory=list)
    orders: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    payment_methods: dict[str, dict[str, Any]] = field(default_factory=dict)
    site_alerts: list[dict[str, Any]] = field(default_factory=list)


def _roaming_package(packages: Any) -> dict[str, Any] | None:
    """Find the roaming package using the API's explicit package label/key."""
    if not isinstance(packages, list):
        return None
    for package in packages:
        if not isinstance(package, dict):
            continue
        label = str(package.get("label") or "").strip().lower()
        key = str(package.get("key") or "").strip().lower()
        if label == "roaming" or "roaming" in key:
            return package
    return None


def _package_value(packages: Any, field: str) -> float | None:
    """Return a numeric value from the roaming package, if supplied."""
    package = _roaming_package(packages)
    return _float(package.get(field)) if package else None


def normalize(raw: dict[str, Any]) -> Subscription:
    tariff_value = raw.get("tariff")
    tariff = tariff_value if isinstance(tariff_value, dict) else {}
    sims: list[Sim] = []
    raw_sims = raw.get("sim_cards") or []
    for item in raw_sims if isinstance(raw_sims, list) else []:
        if not isinstance(item, dict) or not item.get("uuid"):
            continue
        sim_tariff_value = item.get("tariff")
        sim_tariff = sim_tariff_value if isinstance(sim_tariff_value, dict) else tariff
        usage_value = item.get("usage")
        usage = usage_value if isinstance(usage_value, dict) else {}
        sims.append(
            Sim(
                uuid=str(item.get("uuid") or ""),
                phone_number=item.get("phone_number"),
                operator=item.get("operator") or sim_tariff.get("operator"),
                status=str(item.get("status")).lower()
                if item.get("status") is not None
                else None,
                tariff=sim_tariff.get("name_pl") or sim_tariff.get("name"),
                data_remaining=_float(usage.get("data_remaining_gb")),
                data_total=_float(usage.get("data_total_gb")),
                roaming_data_remaining=_package_value(
                    usage.get("packages"), "remaining_gb"
                ),
                roaming_data_total=_package_value(usage.get("packages"), "total_gb"),
                packages=usage.get("packages") or [],
                agreement_number=item.get("agreement_number"),
                iccid=item.get("iccid"),
                crm_reference=item.get("crm_reference"),
            )
        )

    return Subscription(
        uuid=str(raw.get("uuid") or ""),
        public_reference=raw.get("public_reference"),
        status=str(raw.get("status")).lower()
        if raw.get("status") is not None
        else None,
        operator=raw.get("operator"),
        billing_period=raw.get("billing_period"),
        renewal_price=_float(raw.get("renewal_effective_price")),
        start_date=_date(raw.get("start_date")),
        next_payment=_date(raw.get("next_payment_date")),
        tariff=tariff.get("name_pl") or tariff.get("name"),
        billing_mode=raw.get("billing_mode"),
        payment_mode=raw.get("subscription_payment_mode"),
        sims=sims,
    )
