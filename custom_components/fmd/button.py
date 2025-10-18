"""Button entities for FMD integration."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FMD button entities."""
    async_add_entities([
        FmdManualUpdateButton(entry),
    ])


class FmdManualUpdateButton(ButtonEntity):
    """Button entity to trigger a manual location update."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:map-marker-refresh"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_manual_update"
        self._attr_name = "Manual update"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"FMD {self._entry.data['id']}",
            "manufacturer": "FMD",
            "model": "Device Tracker",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Manual update button pressed")
        # TODO: Trigger immediate location update in device_tracker
        self.async_write_ha_state()
