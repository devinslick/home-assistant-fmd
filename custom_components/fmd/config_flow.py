"""Config flow for FMD integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from fmd_api import FmdApi
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_USE_IMPERIAL, DEFAULT_POLLING_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def authenticate_and_get_locations(
    url: str, fmd_id: str, password: str
) -> list[dict[str, Any]]:
    """Create FMD API instance and validate connection."""
    api = await FmdApi.create(url, fmd_id, password)
    locations = await api.get_all_locations(num_to_get=1, skip_empty=True)
    return locations


class FMDConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
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
