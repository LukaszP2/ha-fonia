from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FoniaApi, FoniaApiError, FoniaAuthError, FoniaRateLimitError
from .const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USAGE_SYNC,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    MAX_SCAN_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
)


class FoniaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # pyright: ignore[reportCallIssue, reportGeneralTypeIssues]
    """Handle Fonia setup and credential reauthentication."""

    VERSION = 1

    async def _validate(self, username: str, password: str) -> dict:
        api = FoniaApi(async_get_clientsession(self.hass))
        return await api.login(username, password)

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input:
            username = user_input[CONF_USERNAME].strip()
            try:
                result = await self._validate(username, user_input[CONF_PASSWORD])
                user = result.get("user") or {}
                account = str(user.get("customer_number") or user.get("id") or username)
                await self.async_set_unique_id(account)
                self._abort_if_unique_id_configured()
            except FoniaAuthError:
                errors["base"] = "invalid_auth"
            except FoniaRateLimitError:
                errors["base"] = "rate_limited"
            except FoniaApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user.get("name") or "Fonia",
                    data={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data):
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors: dict[str, str] = {}
        entry = getattr(self, "_reauth_entry", None)
        if entry is None:
            return self.async_abort(reason="reauth_entry_not_found")
        if user_input:
            username = user_input[CONF_USERNAME].strip()
            try:
                await self._validate(username, user_input[CONF_PASSWORD])
            except FoniaAuthError:
                errors["base"] = "invalid_auth"
            except FoniaRateLimitError:
                errors["base"] = "rate_limited"
            except FoniaApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=entry.data[CONF_USERNAME]): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> FoniaOptionsFlow:
        """Create the options flow."""
        return FoniaOptionsFlow()


class FoniaOptionsFlow(config_entries.OptionsFlow):
    """Configure polling and usage synchronization."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
                        ),
                    ): vol.All(
                        int,
                        vol.Range(
                            min=MIN_SCAN_INTERVAL_MINUTES, max=MAX_SCAN_INTERVAL_MINUTES
                        ),
                    ),
                    vol.Required(
                        CONF_USAGE_SYNC,
                        default=self.config_entry.options.get(CONF_USAGE_SYNC, True),
                    ): bool,
                }
            ),
        )
