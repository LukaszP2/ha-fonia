import json
from datetime import date
from pathlib import Path

from custom_components.fonia.const import VERSION
from custom_components.fonia.models import (
    Sim,
    Subscription,
    _date,
    _float,
    _package_value,
    _roaming_package,
    normalize,
)


def test_date_conversion() -> None:
    assert _date("2026-11-06") == date(2026, 11, 6)
    assert _date("2026-11-06T12:00:00Z") == date(2026, 11, 6)
    assert _date("") is None
    assert _date(None) is None
    assert _date("invalid-date") is None


def test_float_conversion() -> None:
    assert _float("12.5") == 12.5
    assert _float("12,5") == 12.5
    assert _float("2,50 GB") == 2.5
    assert _float("500 MB") == 500.0
    assert _float("19,99 PLN") == 19.99
    assert _float("19.99 zł") == 19.99
    assert _float(42) == 42.0
    assert _float("") is None
    assert _float(None) is None
    assert _float("invalid") is None


def test_roaming_package_matching() -> None:
    packages = [
        {"label": "Krajowy", "key": "domestic_data", "remaining_gb": 10.0},
        {"label": "Roaming UE", "key": "roaming_eu", "remaining_gb": 2.5},
    ]
    pkg = _roaming_package(packages)
    assert pkg is not None
    assert pkg["label"] == "Roaming UE"
    assert _package_value(packages, "remaining_gb") == 2.5

    # Non-roaming only
    domestic_only = [{"label": "Standard", "key": "std"}]
    assert _roaming_package(domestic_only) is None
    assert _package_value(domestic_only, "remaining_gb") is None
    assert _roaming_package(None) is None


def test_normalize_subscription() -> None:
    raw = {
        "uuid": "sub-123",
        "public_reference": "REF123",
        "status": "ACTIVE",
        "operator": "Play",
        "billing_period": "monthly",
        "renewal_effective_price": "29.99",
        "start_date": "2026-01-01",
        "next_payment_date": "2026-12-01",
        "tariff": {"name_pl": "Taryfa Smart"},
        "billing_mode": "prepaid",
        "subscription_payment_mode": "card",
        "sim_cards": [
            {
                "uuid": "sim-456",
                "phone_number": "+48123456789",
                "status": "ACTIVE",
                "usage": {
                    "data_remaining_gb": "15.5",
                    "data_total_gb": "20.0",
                    "packages": [
                        {
                            "label": "Roaming UE",
                            "key": "roaming",
                            "remaining_gb": "3.0",
                            "total_gb": "5.0",
                        }
                    ],
                },
            }
        ],
    }

    sub = normalize(raw)
    assert isinstance(sub, Subscription)
    assert sub.uuid == "sub-123"
    assert sub.status == "active"
    assert sub.renewal_price == 29.99
    assert sub.start_date == date(2026, 1, 1)
    assert sub.next_payment == date(2026, 12, 1)
    assert sub.tariff == "Taryfa Smart"
    assert len(sub.sims) == 1

    sim = sub.sims[0]
    assert isinstance(sim, Sim)
    assert sim.uuid == "sim-456"
    assert sim.phone_number == "+48123456789"
    assert sim.status == "active"
    assert sim.data_remaining == 15.5
    assert sim.data_total == 20.0
    assert sim.roaming_data_remaining == 3.0
    assert sim.roaming_data_total == 5.0


def test_version_consistency() -> None:
    manifest_path = (
        Path(__file__).parent.parent / "custom_components" / "fonia" / "manifest.json"
    )
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["version"] == VERSION
