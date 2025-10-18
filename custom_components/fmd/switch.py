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
        FmdAllowInaccurateSwitch(hass, entry),
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

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the switch entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_allow_inaccurate"
        self._attr_name = "Allow inaccurate locations"
        # Initial state is the inverse of block_inaccurate setting
        # If block_inaccurate=True, then allow_inaccurate=False (switch is off)
        block_inaccurate = entry.data.get("block_inaccurate", True)
        self._attr_is_on = not block_inaccurate

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
        _LOGGER.info("Inaccurate locations allowed (blocking disabled)")
        self._attr_is_on = True
        self.async_write_ha_state()
        
        # Update the tracker to disable filtering
        tracker = self.hass.data[DOMAIN][self._entry.entry_id].get("tracker")
        if tracker:
            tracker._block_inaccurate = False
            _LOGGER.info("Location accuracy filtering disabled in tracker")
        else:
            _LOGGER.error("Could not find tracker to update filtering setting")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disallow inaccurate location updates."""
        _LOGGER.info("Inaccurate locations disallowed (blocking enabled)")
        self._attr_is_on = False
        self.async_write_ha_state()
        
        # Update the tracker to enable filtering
        tracker = self.hass.data[DOMAIN][self._entry.entry_id].get("tracker")
        if tracker:
            tracker._block_inaccurate = True
            _LOGGER.info("Location accuracy filtering enabled in tracker")
        else:
            _LOGGER.error("Could not find tracker to update filtering setting")
