"""Config flow for the Felicity inverter."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

from .client import FelicityClient, FelicityConnectionError, FelicityError
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)


class FelicityConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            client = FelicityClient(user_input[CONF_HOST], user_input[CONF_PORT])
            try:
                data = await client.async_get_realtime()
            except FelicityConnectionError:
                errors["base"] = "cannot_connect"
            except FelicityError:
                errors["base"] = "unsupported"
            else:
                await self.async_set_unique_id(str(data["DevSN"]))
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: user_input[CONF_HOST]}
                )
                return self.async_create_entry(
                    title=f"Felicity {data['DevSN']}", data=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return FelicityOptionsFlow()


class FelicityOptionsFlow(OptionsFlow):
    """Options: poll interval."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                    int, vol.Range(min=MIN_SCAN_INTERVAL, max=300)
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
