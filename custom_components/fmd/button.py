"""Button entities for FMD integration."""
from __future__ import annotations

import asyncio
import base64
import logging
from datetime import datetime
from pathlib import Path

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
        FmdCaptureFrontCameraButton(hass, entry),
        FmdCaptureRearCameraButton(hass, entry),
        FmdDownloadPhotosButton(hass, entry),
    ])


class FmdLocationUpdateButton(ButtonEntity):
    """Button entity to trigger a location update from the device."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_location_update"
        self._attr_name = "Location update"

    @property
    def icon(self):
        """Return the icon for this button."""
        return "mdi:map-marker-refresh"

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


class FmdCaptureFrontCameraButton(ButtonEntity):
    """Button entity to capture a photo with the front camera."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:camera-front"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_capture_front"
        self._attr_name = "Capture front camera"

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
        """Handle the button press - capture front camera photo."""
        _LOGGER.info("Capture front camera button pressed - sending command to device")
        
        # Get the tracker to access its API
        tracker = self.hass.data[DOMAIN][self._entry.entry_id].get("tracker")
        if not tracker:
            _LOGGER.error("Could not find tracker to send camera command")
            return
        
        try:
            # Send camera front command to device
            _LOGGER.info("Sending 'camera front' command to device...")
            success = await tracker.api.send_command("camera front")
            
            if success:
                _LOGGER.info("Front camera command sent successfully. Device will capture and upload photo in ~15 seconds.")
            else:
                _LOGGER.warning("Failed to send front camera command to device")
                
        except Exception as e:
            _LOGGER.error("Error sending front camera command: %s", e, exc_info=True)


class FmdCaptureRearCameraButton(ButtonEntity):
    """Button entity to capture a photo with the rear camera."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:camera-rear"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_capture_rear"
        self._attr_name = "Capture rear camera"

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
        """Handle the button press - capture rear camera photo."""
        _LOGGER.info("Capture rear camera button pressed - sending command to device")
        
        # Get the tracker to access its API
        tracker = self.hass.data[DOMAIN][self._entry.entry_id].get("tracker")
        if not tracker:
            _LOGGER.error("Could not find tracker to send camera command")
            return
        
        try:
            # Send camera back command to device
            _LOGGER.info("Sending 'camera back' command to device...")
            success = await tracker.api.send_command("camera back")
            
            if success:
                _LOGGER.info("Rear camera command sent successfully. Device will capture and upload photo in ~15 seconds.")
            else:
                _LOGGER.warning("Failed to send rear camera command to device")
                
        except Exception as e:
            _LOGGER.error("Error sending rear camera command: %s", e, exc_info=True)


class FmdDownloadPhotosButton(ButtonEntity):
    """Button entity to download photos from the server to media folder."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:download-multiple"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_download_photos"
        self._attr_name = "Download photos"

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
        """Handle the button press - download photos to media folder."""
        _LOGGER.info("Download photos button pressed - fetching photos from server")
        
        # Get the tracker to access its API
        tracker = self.hass.data[DOMAIN][self._entry.entry_id].get("tracker")
        if not tracker:
            _LOGGER.error("Could not find tracker to download photos")
            return
        
        # Get max photos setting
        max_photos_number = self.hass.data[DOMAIN][self._entry.entry_id].get("max_photos_number")
        if not max_photos_number:
            _LOGGER.error("Could not find max_photos_number entity")
            return
        
        max_photos = int(max_photos_number.native_value)
        
        try:
            # Fetch photos from server
            _LOGGER.info("Fetching up to %s photos from server...", max_photos)
            pictures = await tracker.api.get_pictures(num_to_get=max_photos)
            
            if not pictures:
                _LOGGER.warning("No photos found on server")
                return
            
            _LOGGER.info("Retrieved %s photo blob(s) from server. Decrypting and saving...", len(pictures))
            
            # Create media directory
            # Use /media for Docker/Core installations, falls back to config/media for HAOS
            try:
                media_base = Path("/media")
                if not media_base.exists() or not media_base.is_dir():
                    # Fall back to config/media for Home Assistant OS
                    media_base = Path(self.hass.config.path("media"))
                media_dir = media_base / "fmd"
                media_dir.mkdir(parents=True, exist_ok=True)
                _LOGGER.info("Saving photos to: %s", media_dir)
            except Exception as e:
                _LOGGER.error("Failed to create media directory: %s", e)
                return
            
            # Download and save each photo
            successful_downloads = 0
            for idx, blob in enumerate(pictures):
                try:
                    # Decrypt the photo
                    decrypted = tracker.api.decrypt_data_blob(blob)
                    image_bytes = base64.b64decode(decrypted)
                    
                    # Generate filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"photo_{timestamp}_{idx:02d}.jpg"
                    filepath = media_dir / filename
                    
                    # Save to file
                    filepath.write_bytes(image_bytes)
                    successful_downloads += 1
                    _LOGGER.debug("Saved photo to %s", filename)
                    
                except Exception as e:
                    _LOGGER.error("Failed to decrypt/save photo %s: %s", idx, e)
            
            _LOGGER.info("Successfully downloaded %s of %s photos to media/fmd/", successful_downloads, len(pictures))
            
            # Update photo count sensor
            photo_sensor = self.hass.data[DOMAIN][self._entry.entry_id].get("photo_count_sensor")
            if photo_sensor:
                photo_sensor.update_photo_count(len(pictures))
                await photo_sensor.async_update_ha_state()
                _LOGGER.info("Updated photo count sensor")
            else:
                _LOGGER.warning("Could not find photo count sensor to update")
                
        except Exception as e:
            _LOGGER.error("Error downloading photos: %s", e, exc_info=True)

