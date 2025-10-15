"""Config flow for FMD integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, DEFAULT_POLLING_INTERVAL
from .fmd_client.fmd_api import FmdApi

class FMDConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FMD."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                api = FmdApi(user_input["url"], user_input["id"], user_input["password"])
                await self.hass.async_add_executor_job(api.get_locations)
                
                return self.async_create_entry(title=user_input["id"], data=user_input)
            except Exception:
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema({
            vol.Required("url"): str,
            vol.Required("id"): str,
            vol.Required("password"): str,
            vol.Optional("polling_interval", default=DEFAULT_POLLING_INTERVAL): int,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
