"""Switch entities for FMD integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up FMD switch entities."""
    async_add_entities([
        FmdHighFrequencyModeSwitch(entry),
        FmdAllowInaccurateSwitch(entry),
    ])


class FmdHighFrequencyModeSwitch(SwitchEntity):
    """Switch entity to enable high-frequency update mode."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:timer-fast-outline"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the switch entity."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_high_frequency_mode"
        self._attr_name = "High frequency mode"
        self._attr_is_on = False

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"FMD {self._entry.data['id']}",
            "manufacturer": "FMD",
            "model": "Device Tracker",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on high-frequency mode."""
        _LOGGER.info("High frequency mode enabled")
        self._attr_is_on = True
        self.async_write_ha_state()
        # TODO: Switch to high-frequency polling interval

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off high-frequency mode."""
        _LOGGER.info("High frequency mode disabled")
        self._attr_is_on = False
        self.async_write_ha_state()
        # TODO: Switch back to standard polling interval


class FmdAllowInaccurateSwitch(SwitchEntity):
    """Switch entity to allow inaccurate location updates."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:map-marker-question"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the switch entity."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_allow_inaccurate"
        self._attr_name = "Allow inaccurate locations"
        self._attr_is_on = False

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"FMD {self._entry.data['id']}",
            "manufacturer": "FMD",
            "model": "Device Tracker",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Allow inaccurate location updates."""
        _LOGGER.info("Inaccurate locations allowed")
        self._attr_is_on = True
        self.async_write_ha_state()
        # TODO: Update location filtering logic

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disallow inaccurate location updates."""
        _LOGGER.info("Inaccurate locations disallowed")
        self._attr_is_on = False
        self.async_write_ha_state()
        # TODO: Update location filtering logic
