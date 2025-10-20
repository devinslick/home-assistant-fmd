"""Config flow for FMD integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, DEFAULT_POLLING_INTERVAL, CONF_USE_IMPERIAL
from .fmd_client.fmd_api import FmdApi

_LOGGER = logging.getLogger(__name__)

async def authenticate_and_get_locations(url, fmd_id, password):
    """Create FMD API instance and validate connection."""
    api = await FmdApi.create(url, fmd_id, password)
    locations = await api.get_all_locations(num_to_get=1, skip_empty=True)
    return locations

class FMDConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FMD."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
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

        data_schema = vol.Schema({
            vol.Required("url"): str,
            vol.Required("id"): str,
            vol.Required("password"): str,
            vol.Optional("polling_interval", default=DEFAULT_POLLING_INTERVAL): int,
            vol.Optional("allow_inaccurate_locations", default=False): bool,
            vol.Optional(CONF_USE_IMPERIAL, default=False): bool,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
