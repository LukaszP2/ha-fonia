from unittest.mock import MagicMock

from homeassistant.components.sensor import SensorDeviceClass

from custom_components.fonia.const import (
    CATEGORY_PAYMENTS,
    CONF_CATEGORIES,
    DOMAIN,
)
from custom_components.fonia.models import FoniaData, Sim, Subscription
from custom_components.fonia.sensor import (
    _CHILD_DEVICE_SUPPORTED,
    ACCOUNT_SENSORS,
    SENSORS,
    SENSORS_BY_KEY,
    FoniaSensor,
    _build_entities,
    _latest_order,
    _roaming_used_percentage,
    _used_percentage,
)


def test_used_percentage() -> None:
    sim = Sim(
        uuid="sim-1",
        phone_number="+48111",
        operator="Play",
        status="active",
        tariff="Smart",
        data_remaining=5.0,
        data_total=20.0,
    )
    # (20 - 5) / 20 * 100 = 75.0%
    assert _used_percentage(sim) == 75.0

    # Total <= 0
    sim.data_total = 0.0
    assert _used_percentage(sim) is None
    assert _used_percentage(None) is None


def test_roaming_used_percentage() -> None:
    sim = Sim(
        uuid="sim-1",
        phone_number="+48111",
        operator="Play",
        status="active",
        tariff="Smart",
        data_remaining=10.0,
        data_total=20.0,
        roaming_data_remaining=1.0,
        roaming_data_total=4.0,
    )
    # (4 - 1) / 4 * 100 = 75.0%
    assert _roaming_used_percentage(sim) == 75.0


def test_sensor_multi_account_uniqueness() -> None:
    coordinator = MagicMock()
    coordinator.data = FoniaData()

    entry_1 = MagicMock()
    entry_1.entry_id = "entry_1"

    entry_2 = MagicMock()
    entry_2.entry_id = "entry_2"

    cashback_desc = next(s for s in ACCOUNT_SENSORS if s.key == "cashback_balance")

    sensor_1 = FoniaSensor(coordinator, entry_1, cashback_desc)
    sensor_2 = FoniaSensor(coordinator, entry_2, cashback_desc)

    # Unique IDs must differ!
    assert sensor_1.unique_id == "account_entry_1_cashback_balance"
    assert sensor_2.unique_id == "account_entry_2_cashback_balance"

    # Device identifiers must differ!
    assert sensor_1.device_info["identifiers"] == {(DOMAIN, "account_entry_1")}
    assert sensor_2.device_info["identifiers"] == {(DOMAIN, "account_entry_2")}


def test_sim_sensor_device_info_via_device() -> None:
    coordinator = MagicMock()
    sim = Sim(
        uuid="sim-abc",
        phone_number="+48999",
        operator="Fonia",
        status="active",
        tariff="Plan",
        data_remaining=10.0,
        data_total=20.0,
    )
    sub = Subscription(
        uuid="sub-xyz",
        public_reference="R1",
        status="active",
        operator="Fonia",
        billing_period="m",
        renewal_price=29.0,
        start_date=None,
        next_payment=None,
        tariff="Plan",
        billing_mode="prepaid",
        payment_mode="card",
        sims=[sim],
    )
    coordinator.data = FoniaData(subscriptions=[sub])

    entry = MagicMock()
    entry.entry_id = "main_entry"

    sensor = FoniaSensor(
        coordinator,
        entry,
        SENSORS_BY_KEY["data_remaining"],
        subscription=sub,
        sim=sim,
        parent_device_id="account_device_123",
    )

    assert sensor.unique_id == "sim_sim-abc_data_remaining"
    assert sensor.device_info["identifiers"] == {(DOMAIN, "sim_sim-abc")}
    if _CHILD_DEVICE_SUPPORTED:
        assert sensor.device_info["parent_device_id"] == "account_device_123"
    else:
        assert sensor.device_info["via_device"] == (DOMAIN, "account_main_entry")
    assert sensor.native_value == 10.0


def test_sensor_availability_when_sim_removed() -> None:
    coordinator = MagicMock()
    coordinator.last_update_success = True

    sim = Sim(
        uuid="sim-temp",
        phone_number="+48111",
        operator="Fonia",
        status="active",
        tariff="Plan",
        data_remaining=5.0,
        data_total=10.0,
    )
    sub = Subscription(
        uuid="sub-1",
        public_reference=None,
        status="active",
        operator="Fonia",
        billing_period=None,
        renewal_price=None,
        start_date=None,
        next_payment=None,
        tariff=None,
        billing_mode=None,
        payment_mode=None,
        sims=[sim],
    )
    coordinator.data = FoniaData(subscriptions=[sub])

    entry = MagicMock()
    entry.entry_id = "e1"

    sensor = FoniaSensor(
        coordinator, entry, SENSORS_BY_KEY["data_remaining"], subscription=sub, sim=sim
    )
    assert sensor.available is True

    # SIM is removed from coordinator data
    sub.sims = []
    assert sensor.available is False


def test_attributes_privacy_on_data_sensor() -> None:
    coordinator = MagicMock()
    coordinator.data = FoniaData()

    sim = Sim(
        uuid="sim-1",
        phone_number="+48123456789",
        operator="Fonia",
        status="active",
        tariff="Smart",
        data_remaining=10.0,
        data_total=20.0,
        iccid="8948123456789",
        agreement_number="AGR-999",
    )
    sub = Subscription(
        uuid="sub-1",
        public_reference="REF",
        status="active",
        operator="Fonia",
        billing_period="m",
        renewal_price=19.99,
        start_date=None,
        next_payment=None,
        tariff="Smart",
        billing_mode="prepaid",
        payment_mode="card",
        sims=[sim],
    )
    coordinator.data.subscriptions = [sub]

    entry = MagicMock()
    entry.entry_id = "e1"

    # Status sensor gets basic subscriber attributes
    status_sensor = FoniaSensor(
        coordinator, entry, SENSORS_BY_KEY["status"], subscription=sub, sim=sim
    )
    attrs = status_sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["phone_number"] == "+48123456789"
    # ICCID and agreement numbers must not be exposed in state attributes
    assert "iccid" not in attrs
    assert "agreement_number" not in attrs

    # Usage sensors do NOT duplicate subscriber attributes
    usage_sensor = FoniaSensor(
        coordinator, entry, SENSORS_BY_KEY["data_remaining"], subscription=sub, sim=sim
    )
    assert usage_sensor.extra_state_attributes is None


def test_monetary_sensors_have_no_state_class() -> None:
    all_sensors = SENSORS + ACCOUNT_SENSORS
    monetary_sensors = [
        s for s in all_sensors if s.device_class == SensorDeviceClass.MONETARY
    ]
    assert len(monetary_sensors) == 3
    for s in monetary_sensors:
        assert s.state_class is None


def test_build_entities_category_filtering() -> None:
    coordinator = MagicMock()
    sim = Sim(
        uuid="sim-cat",
        phone_number="+48100",
        operator="Fonia",
        status="active",
        tariff="Smart",
        data_remaining=15.0,
        data_total=30.0,
    )
    sub = Subscription(
        uuid="sub-cat",
        public_reference="REF-CAT",
        status="active",
        operator="Fonia",
        billing_period="m",
        renewal_price=29.0,
        start_date=None,
        next_payment=None,
        tariff="Smart",
        billing_mode="prepaid",
        payment_mode="card",
        sims=[sim],
    )
    coordinator.data = FoniaData(
        subscriptions=[sub],
        cashback_balance=50.0,
        cashback_spendable=30.0,
        cashback_transactions=[{"id": "t1"}],
        site_alerts=[{"id": "a1"}],
    )

    entry = MagicMock()
    entry.entry_id = "entry_cat"
    # Enable ONLY payments category; core is always active; usage/history/advanced disabled
    entry.options = {CONF_CATEGORIES: [CATEGORY_PAYMENTS]}

    entities = _build_entities(coordinator, entry, "parent_123")
    keys = {e.entity_description.key for e in entities}

    # Core must be present
    assert "status" in keys
    assert "data_remaining" in keys
    assert "cashback_balance" in keys
    assert "cashback_spendable" in keys

    # Payments must be present
    assert "next_payment" in keys
    assert "renewal_price" in keys
    assert "order_count" in keys

    # Usage, history, advanced must NOT be present
    assert "data_total" not in keys
    assert "data_used_percentage" not in keys
    assert "roaming_data_remaining" not in keys
    assert "cashback_transaction_count" not in keys
    assert "site_alert_count" not in keys


def test_standalone_subscription_without_sims() -> None:
    coordinator = MagicMock()
    sub = Subscription(
        uuid="sub-standalone",
        public_reference="SUB-999",
        status="pending",
        operator="Fonia",
        billing_period="monthly",
        renewal_price=49.0,
        start_date=None,
        next_payment=None,
        tariff="Pro",
        billing_mode="prepaid",
        payment_mode="card",
        sims=[],  # No active SIM card yet
    )
    coordinator.data = FoniaData(subscriptions=[sub])

    entry = MagicMock()
    entry.entry_id = "entry_standalone"
    entry.options = {}

    entities = _build_entities(coordinator, entry, "parent_device_xyz")
    sub_entities = [e for e in entities if e._subscription_id == "sub-standalone"]

    # Only subscription-scoped sensors should be created, no SIM-scoped sensors
    sub_keys = {e.entity_description.key for e in sub_entities}
    assert "status" in sub_keys
    assert "next_payment" in sub_keys
    assert "renewal_price" in sub_keys
    assert "order_count" in sub_keys
    assert "data_remaining" not in sub_keys
    assert "data_total" not in sub_keys

    # Check child device info for the standalone subscription
    status_sensor = next(
        e for e in sub_entities if e.entity_description.key == "status"
    )
    assert status_sensor.device_info["identifiers"] == {(DOMAIN, "sub_sub-standalone")}
    assert status_sensor.native_value == "pending"
    if _CHILD_DEVICE_SUPPORTED:
        assert status_sensor.device_info["parent_device_id"] == "parent_device_xyz"
    else:
        assert status_sensor.device_info["via_device"] == (
            DOMAIN,
            "account_entry_standalone",
        )


def test_latest_order_normalization() -> None:
    orders = [
        {
            "id": 1,
            "created_at": "2026-01-01T10:00:00Z",
            "amount": "29.50",
            "total": 30,
            "type": "renewal",
        },
        {
            "id": 2,
            "created_at": "2026-02-01T10:00:00Z",
            "amount": 49.9912,
            "amount_pln": "50",
            "status": "completed",
        },
    ]

    latest = _latest_order(orders)
    assert latest["id"] == 2
    assert latest["status"] == "completed"
    assert latest["amount"] == 49.99
    assert latest["amount_pln"] == 50.0
    assert _latest_order([]) == {}
