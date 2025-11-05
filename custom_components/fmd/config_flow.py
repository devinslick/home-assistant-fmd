"""Config flow for FMD integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

# Prefer v2 client; fall back to v1 name for CI or environments with older fmd_api
from fmd_api import FmdClient
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_USE_IMPERIAL, DEFAULT_POLLING_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def authenticate_and_get_locations(
    url: str, fmd_id: str, password: str
) -> list[dict[str, Any]]:
    """Create FMD API instance and validate connection."""
    api = await FmdClient.create(url, fmd_id, password)
    locations = await api.get_locations(1)
    locations = [loc for loc in locations if loc]
    return locations


class FMDConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle re-authentication with new credentials."""
        errors: dict[str, str] = {}
        entry_id = self.context.get("entry_id")
        entry = self.hass.config_entries.async_get_entry(entry_id) if entry_id else None
        entry_data = entry.data if entry else {}

        if user_input is not None:
            try:
                await authenticate_and_get_locations(
                    user_input["url"],
                    user_input["id"],
                    user_input["password"],
                )
                # Update the config entry with new credentials
                if entry:
                    self.hass.config_entries.async_update_entry(entry, data=user_input)
                return self.async_abort(reason="reauth_successful")
            except Exception:
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required("url", default=entry_data.get("url", "")): str,
                vol.Required("id", default=entry_data.get("id", "")): str,
                vol.Required("password"): str,
            }
        )

        return self.async_show_form(
            step_id="reauth",
            data_schema=data_schema,
            errors=errors,
        )

    """Handle a config flow for FMD."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await authenticate_and_get_locations(
                    user_input["url"],
                    user_input["id"],
                    user_input["password"],
                )
                return self.async_create_entry(title=user_input["id"], data=user_input)
            except Exception as e:
                _LOGGER.error("Failed to connect to FMD server: %s", e, exc_info=True)
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required("url"): str,
                vol.Required("id"): str,
                vol.Required("password"): str,
                vol.Optional("polling_interval", default=DEFAULT_POLLING_INTERVAL): int,
                vol.Optional("allow_inaccurate_locations", default=False): bool,
                vol.Optional(CONF_USE_IMPERIAL, default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={},
        )
