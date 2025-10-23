"""Number entities for FMD integration."""
from __future__ import annotations

from typing import Any

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Default intervals in minutes
DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_HIGH_FREQUENCY_INTERVAL = 5


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FMD number entities."""
    entities = [
        FmdUpdateIntervalNumber(hass, entry),
        FmdHighFrequencyIntervalNumber(hass, entry),
        FmdMaxPhotosNumber(hass, entry),
    ]
    
    async_add_entities(entities)
    
    # Store max photos number reference for download button to access
    hass.data[DOMAIN][entry.entry_id]["max_photos_number"] = entities[2]


class FmdUpdateIntervalNumber(NumberEntity):
    """Number entity for standard update interval."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 1
    _attr_native_max_value = 1440  # 24 hours in minutes
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the number entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_update_interval"
        self._attr_name = "Update interval"
        self._attr_native_value = entry.data.get("polling_interval", DEFAULT_UPDATE_INTERVAL)
        self._attr_icon = "mdi:timer-outline"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"FMD {self._entry.data['id']}",
            "manufacturer": "FMD",
            "model": "Device Tracker",
        }

    async def async_set_native_value(self, value: float) -> None:
        """Update the interval value."""
        _LOGGER.info("Update interval changed to %s minutes", value)
        self._attr_native_value = value
        self.async_write_ha_state()
        
        # Update the actual polling interval in device_tracker
        tracker = self.hass.data[DOMAIN][self._entry.entry_id].get("tracker")
        if tracker:
            tracker.set_polling_interval(int(value))
            _LOGGER.info("Successfully updated tracker polling interval to %s minutes", value)
        else:
            _LOGGER.error("Could not find tracker to update polling interval")


class FmdHighFrequencyIntervalNumber(NumberEntity):
    """Number entity for high-frequency update interval."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 1
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:map-clock"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the number entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_high_frequency_interval"
        self._attr_name = "High frequency interval"
        self._attr_native_value = DEFAULT_HIGH_FREQUENCY_INTERVAL

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"FMD {self._entry.data['id']}",
            "manufacturer": "FMD",
            "model": "Device Tracker",
        }

    async def async_set_native_value(self, value: float) -> None:
        """Update the interval value."""
        _LOGGER.info("High frequency interval changed to %s minutes", value)
        self._attr_native_value = value
        self.async_write_ha_state()
        
        # Update the high-frequency interval in the tracker
        tracker = self.hass.data[DOMAIN][self._entry.entry_id].get("tracker")
        if tracker:
            tracker.set_high_frequency_interval(int(value))
            _LOGGER.info("Successfully updated tracker high-frequency interval to %s minutes", value)
        else:
            _LOGGER.error("Could not find tracker to update high-frequency interval")


class FmdMaxPhotosNumber(NumberEntity):
    """Number entity for maximum photos to download."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 1
    _attr_native_max_value = 50
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "photos"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the number entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_max_photos"
        self._attr_name = "Photo: Max to retain"
        self._attr_native_value = 10  # Default to 10 photos

    @property
    def icon(self):
        """Return the icon for this number entity."""
        return "mdi:image-multiple"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"FMD {self._entry.data['id']}",
            "manufacturer": "FMD",
            "model": "Device Tracker",
        }

    async def async_set_native_value(self, value: float) -> None:
        """Update the max photos to retain value."""
        _LOGGER.info("Photo: Max to retain changed to %s", value)
        self._attr_native_value = value
        self.async_write_ha_state()

