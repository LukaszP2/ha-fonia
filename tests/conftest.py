"""Pytest configuration and mocks for isolated test runs without full Home Assistant."""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

# 1. Voluptuous
if "voluptuous" not in sys.modules:
    vol = types.ModuleType("voluptuous")
    vol.Schema = MagicMock(side_effect=lambda x: x)
    vol.Required = MagicMock(
        side_effect=lambda *args, **kwargs: args[0] if args else kwargs
    )
    vol.Optional = MagicMock(
        side_effect=lambda *args, **kwargs: args[0] if args else kwargs
    )
    vol.In = MagicMock(side_effect=lambda x: x)
    vol.All = MagicMock(side_effect=lambda *args: args)
    vol.Coerce = MagicMock(side_effect=lambda x: x)
    vol.Range = MagicMock(side_effect=lambda **kwargs: kwargs)
    sys.modules["voluptuous"] = vol

# 2. Home Assistant and submodules
if "homeassistant" not in sys.modules:
    ha = types.ModuleType("homeassistant")
    ha.__path__ = []
    sys.modules["homeassistant"] = ha

    # homeassistant.const
    const = types.ModuleType("homeassistant.const")
    const.PERCENTAGE = "%"
    const.CONF_NAME = "name"

    class UnitOfInformation:
        GIGABYTES = "GB"
        MEGABYTES = "MB"

    const.UnitOfInformation = UnitOfInformation

    class Platform:
        SENSOR = "sensor"
        BUTTON = "button"

    const.Platform = Platform

    class EntityCategory:
        CONFIG = "config"
        DIAGNOSTIC = "diagnostic"

    const.EntityCategory = EntityCategory
    sys.modules["homeassistant.const"] = const
    ha.const = const

    # homeassistant.exceptions
    class HomeAssistantError(Exception):
        pass

    class ConfigEntryAuthFailed(HomeAssistantError):
        pass

    class ConfigEntryNotReady(HomeAssistantError):
        pass

    exceptions = types.ModuleType("homeassistant.exceptions")
    exceptions.HomeAssistantError = HomeAssistantError
    exceptions.ConfigEntryAuthFailed = ConfigEntryAuthFailed
    exceptions.ConfigEntryNotReady = ConfigEntryNotReady
    sys.modules["homeassistant.exceptions"] = exceptions
    ha.exceptions = exceptions

    # homeassistant.core
    core = types.ModuleType("homeassistant.core")

    class HomeAssistant(MagicMock):
        pass

    def callback(fn):
        return fn

    core.HomeAssistant = HomeAssistant
    core.callback = callback
    sys.modules["homeassistant.core"] = core
    ha.core = core

    # homeassistant.data_entry_flow
    deflow = types.ModuleType("homeassistant.data_entry_flow")

    class FlowResultType:
        FORM = "form"
        CREATE_ENTRY = "create_entry"
        ABORT = "abort"
        EXTERNAL_STEP = "external_step"
        SHOW_PROGRESS = "show_progress"
        SHOW_PROGRESS_DONE = "show_progress_done"
        MENU = "menu"

    deflow.FlowResultType = FlowResultType
    deflow.FlowResult = dict
    sys.modules["homeassistant.data_entry_flow"] = deflow
    ha.data_entry_flow = deflow

    # homeassistant.config_entries
    ce = types.ModuleType("homeassistant.config_entries")
    ce.SOURCE_USER = "user"
    ce.SOURCE_REAUTH = "reauth"
    ce.SOURCE_RECONFIGURE = "reconfigure"
    ce.ConfigFlowResult = dict

    class DummyConfigEntry(MagicMock):
        __class_getitem__ = classmethod(lambda cls, item: cls)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.entry_id = kwargs.get("entry_id", "test_entry_id")
            self.title = kwargs.get("title", "Fonia")
            self.data = kwargs.get("data", {})
            self.options = kwargs.get("options", {})
            self.unique_id = kwargs.get("unique_id", "test_unique_id")

    class DummyConfigFlow:
        def __init_subclass__(cls, domain=None, **kwargs):
            super().__init_subclass__()
            cls._domain = domain

        def __init__(self):
            self.hass = MagicMock()
            self.context = {}
            self.source = "user"

        def async_show_form(self, **kwargs):
            return {"type": "form", **kwargs}

        def async_create_entry(self, **kwargs):
            return {"type": "create_entry", **kwargs}

        def async_abort(self, reason, **kwargs):
            return {"type": "abort", "reason": reason, **kwargs}

        def async_update_reload_and_abort(
            self, entry, data_updates=None, reason="reauth_successful", **kwargs
        ):
            if entry and data_updates:
                entry.data.update(data_updates)
            return {"type": "abort", "reason": reason, **kwargs}

        async def async_set_unique_id(self, unique_id, **kwargs):
            self.unique_id = unique_id

        def _abort_if_unique_id_configured(self):
            pass

        def _get_reconfigure_entry(self):
            return getattr(self, "_reconfigure_entry", None)

    class DummyOptionsFlow:
        def __init__(self):
            self.hass = MagicMock()
            self.handler = "test_entry_id"

        @property
        def config_entry(self):
            if hasattr(self, "_config_entry"):
                return self._config_entry
            entry = self.hass.config_entries.async_get_known_entry(self.handler)
            if entry:
                return entry
            entry = MagicMock()
            entry.entry_id = self.handler
            entry.title = "Fonia"
            entry.options = {}
            entry.data = {}
            return entry

        def async_show_form(self, **kwargs):
            return {"type": "form", **kwargs}

        def async_create_entry(self, **kwargs):
            return {"type": "create_entry", **kwargs}

    ce.ConfigEntry = DummyConfigEntry
    ce.ConfigFlow = DummyConfigFlow
    ce.OptionsFlow = DummyOptionsFlow
    sys.modules["homeassistant.config_entries"] = ce
    ha.config_entries = ce

    # homeassistant.helpers
    helpers = types.ModuleType("homeassistant.helpers")
    helpers.__path__ = []

    # redact
    redact = types.ModuleType("homeassistant.helpers.redact")

    def async_redact_data(data, to_redact):
        if not isinstance(data, dict):
            return data
        return {k: ("**REDACTED**" if k in to_redact else v) for k, v in data.items()}

    redact.async_redact_data = async_redact_data
    sys.modules["homeassistant.helpers.redact"] = redact
    helpers.redact = redact

    # aiohttp_client
    aiohttp_client = types.ModuleType("homeassistant.helpers.aiohttp_client")
    aiohttp_client.async_get_clientsession = MagicMock()
    aiohttp_client.async_create_clientsession = MagicMock()
    sys.modules["homeassistant.helpers.aiohttp_client"] = aiohttp_client
    helpers.aiohttp_client = aiohttp_client

    # selector
    selector = types.ModuleType("homeassistant.helpers.selector")

    class SelectSelector:
        def __init__(self, config=None):
            self.config = config

    class SelectSelectorConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class SelectSelectorMode:
        LIST = "list"
        DROPDOWN = "dropdown"

    class TextSelector:
        def __init__(self, config=None):
            self.config = config

    class TextSelectorConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    selector.SelectSelector = SelectSelector
    selector.SelectSelectorConfig = SelectSelectorConfig
    selector.SelectSelectorMode = SelectSelectorMode
    selector.TextSelector = TextSelector
    selector.TextSelectorConfig = TextSelectorConfig
    sys.modules["homeassistant.helpers.selector"] = selector
    helpers.selector = selector

    # device_registry
    dr = types.ModuleType("homeassistant.helpers.device_registry")

    class DeviceInfo(dict):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            for k, v in kwargs.items():
                setattr(self, k, v)

    class ChildDeviceInfo(DeviceInfo):
        pass

    dr.DeviceInfo = DeviceInfo
    dr.ChildDeviceInfo = ChildDeviceInfo
    dr.async_get = MagicMock()
    sys.modules["homeassistant.helpers.device_registry"] = dr
    helpers.device_registry = dr

    # entity
    entity = types.ModuleType("homeassistant.helpers.entity")

    class EntityCategory:
        CONFIG = "config"
        DIAGNOSTIC = "diagnostic"

    entity.EntityCategory = EntityCategory
    sys.modules["homeassistant.helpers.entity"] = entity
    helpers.entity = entity

    # entity_platform
    ep = types.ModuleType("homeassistant.helpers.entity_platform")
    ep.AddEntitiesCallback = MagicMock
    sys.modules["homeassistant.helpers.entity_platform"] = ep
    helpers.entity_platform = ep

    # update_coordinator
    coord = types.ModuleType("homeassistant.helpers.update_coordinator")

    class UpdateFailed(HomeAssistantError):
        pass

    class DataUpdateCoordinator:
        __class_getitem__ = classmethod(lambda cls, item: cls)

        def __init__(self, hass, logger, name, update_interval=None, **kwargs):
            self.hass = hass
            self.logger = logger
            self.name = name
            self.update_interval = update_interval
            self.data = None
            self._listeners = []

        async def async_config_entry_first_refresh(self):
            pass

        def async_add_listener(self, update_callback):
            self._listeners.append(update_callback)
            return lambda: self._listeners.remove(update_callback)

        async def async_request_refresh(self):
            pass

    class CoordinatorEntity:
        __class_getitem__ = classmethod(lambda cls, item: cls)

        def __init__(self, coordinator=None, *args, **kwargs):
            self.coordinator = coordinator

        @property
        def available(self) -> bool:
            return True

        @property
        def unique_id(self):
            return getattr(self, "_attr_unique_id", None)

        @property
        def device_info(self):
            return getattr(self, "_attr_device_info", None)

        @property
        def entity_category(self):
            return getattr(self, "_attr_entity_category", None)

        @property
        def entity_registry_enabled_default(self):
            return getattr(self, "_attr_entity_registry_enabled_default", True)

    coord.DataUpdateCoordinator = DataUpdateCoordinator
    coord.CoordinatorEntity = CoordinatorEntity
    coord.UpdateFailed = UpdateFailed
    sys.modules["homeassistant.helpers.update_coordinator"] = coord
    helpers.update_coordinator = coord

    sys.modules["homeassistant.helpers"] = helpers
    ha.helpers = helpers

    # homeassistant.components
    comps = types.ModuleType("homeassistant.components")
    comps.__path__ = []

    # components.sensor
    sensor = types.ModuleType("homeassistant.components.sensor")

    class SensorEntity:
        pass

    @dataclass(frozen=True, kw_only=True)
    class SensorEntityDescription:
        key: str
        device_class: Any = None
        entity_category: Any = None
        native_unit_of_measurement: Any = None
        state_class: Any = None
        translation_key: Any = None
        has_entity_name: bool = False

    class SensorDeviceClass:
        DATE = "date"
        MONETARY = "monetary"
        DATA_SIZE = "data_size"

    class SensorStateClass:
        MEASUREMENT = "measurement"
        TOTAL = "total"
        TOTAL_INCREASING = "total_increasing"

    sensor.SensorEntity = SensorEntity
    sensor.SensorEntityDescription = SensorEntityDescription
    sensor.SensorDeviceClass = SensorDeviceClass
    sensor.SensorStateClass = SensorStateClass
    sys.modules["homeassistant.components.sensor"] = sensor
    comps.sensor = sensor

    # components.button
    button = types.ModuleType("homeassistant.components.button")

    class ButtonEntity:
        pass

    button.ButtonEntity = ButtonEntity
    sys.modules["homeassistant.components.button"] = button
    comps.button = button

    # components.diagnostics
    diag = types.ModuleType("homeassistant.components.diagnostics")
    diag.async_redact_data = async_redact_data
    sys.modules["homeassistant.components.diagnostics"] = diag
    comps.diagnostics = diag

    sys.modules["homeassistant.components"] = comps
    ha.components = comps
