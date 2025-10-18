"""Button entities for FMD integration."""
from __future__ import annotations

import asyncio
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
        FmdLocationUpdateButton(hass, entry),
    ])


class FmdLocationUpdateButton(ButtonEntity):
    """Button entity to trigger a location update from the device."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:map-marker-refresh"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_location_update"
        self._attr_name = "Location update"

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
        """Handle the button press - request location update from device."""
        _LOGGER.info("Location update button pressed - requesting new location from device")
        
        # Get the tracker to access its API
        tracker = self.hass.data[DOMAIN][self._entry.entry_id].get("tracker")
        if not tracker:
            _LOGGER.error("Could not find tracker to request location update")
            return
        
        try:
            # Send command to device to request a new location update
            _LOGGER.info("Sending location request command to device...")
            success = await tracker.api.request_location(provider="all")
            
            if success:
                _LOGGER.info("Location request sent successfully. Waiting 10 seconds for device to respond...")
                
                # Wait 10 seconds for the device to capture and upload the location
                await asyncio.sleep(10)
                
                # Fetch the latest location data from the server
                _LOGGER.info("Fetching updated location from server...")
                await tracker.async_update()
                
                _LOGGER.info("Location update completed successfully")
            else:
                _LOGGER.warning("Failed to send location request to device")
                
        except Exception as e:
            _LOGGER.error("Error requesting location update: %s", e, exc_info=True)
