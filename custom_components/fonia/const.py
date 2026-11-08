from __future__ import annotations

from datetime import timedelta

DOMAIN = "fonia"
NAME = "Fonia"
VERSION = "0.6.0"
API_BASE = "https://moja.fonia.app/api"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=15)
USAGE_SYNC_INTERVAL = timedelta(hours=2)
DETAILS_SCAN_INTERVAL = timedelta(hours=2)
ACCOUNT_SCAN_INTERVAL = timedelta(minutes=30)
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_USAGE_SYNC = "usage_sync_enabled"
CONF_CATEGORIES = "categories"

CATEGORY_CORE = "core"
CATEGORY_PAYMENTS = "payments"
CATEGORY_USAGE = "usage"
CATEGORY_HISTORY = "history"
CATEGORY_ADVANCED = "advanced"

ALL_CATEGORIES = [
    CATEGORY_PAYMENTS,
    CATEGORY_USAGE,
    CATEGORY_HISTORY,
    CATEGORY_ADVANCED,
]

DEFAULT_SCAN_INTERVAL_MINUTES = 15
MIN_SCAN_INTERVAL_MINUTES = 5
MAX_SCAN_INTERVAL_MINUTES = 60
