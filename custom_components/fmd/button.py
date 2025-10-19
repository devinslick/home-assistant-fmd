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
        FmdRingButton(hass, entry),
        FmdLockButton(hass, entry),
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
                
                # Write the updated state to Home Assistant
                tracker.async_write_ha_state()
                
                _LOGGER.info("Location update completed successfully")
            else:
                _LOGGER.warning("Failed to send location request to device")
                
        except Exception as e:
            _LOGGER.error("Error requesting location update: %s", e, exc_info=True)


class FmdRingButton(ButtonEntity):
    """Button entity to make the device ring."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:bell-ring"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ring"
        self._attr_name = "Ring"

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
        """Handle the button press - make the device ring."""
        _LOGGER.info("Ring button pressed - sending ring command to device")
        
        # Get the tracker to access its API
        tracker = self.hass.data[DOMAIN][self._entry.entry_id].get("tracker")
        if not tracker:
            _LOGGER.error("Could not find tracker to send ring command")
            return
        
        try:
            # Send ring command to device
            _LOGGER.info("Sending ring command to device...")
            success = await tracker.api.send_command("ring")
            
            if success:
                _LOGGER.info("Ring command sent successfully")
            else:
                _LOGGER.warning("Failed to send ring command to device")
                
        except Exception as e:
            _LOGGER.error("Error sending ring command: %s", e, exc_info=True)


class FmdLockButton(ButtonEntity):
    """Button entity to lock the device."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:lock"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_lock"
        self._attr_name = "Lock"

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
        """Handle the button press - lock the device."""
        _LOGGER.info("Lock button pressed - sending lock command to device")
        
        # Get the tracker to access its API
        tracker = self.hass.data[DOMAIN][self._entry.entry_id].get("tracker")
        if not tracker:
            _LOGGER.error("Could not find tracker to send lock command")
            return
        
        try:
            # Send lock command to device
            _LOGGER.info("Sending lock command to device...")
            success = await tracker.api.send_command("lock")
            
            if success:
                _LOGGER.info("Lock command sent successfully")
            else:
                _LOGGER.warning("Failed to send lock command to device")
                
        except Exception as e:
            _LOGGER.error("Error sending lock command: %s", e, exc_info=True)
