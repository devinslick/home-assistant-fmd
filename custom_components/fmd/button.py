"""Button entities for FMD integration."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import logging
from typing import Any
from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS

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
        FmdWipeDeviceButton(hass, entry),
    ])


class FmdLocationUpdateButton(ButtonEntity):
    """Button entity to trigger a location update from the device."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:map-marker-circle"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_location_update"
        self._attr_name = "Location update"

    @property
    def device_info(self) -> dict[str, Any]:
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
        
        # Get the location source select entity to determine which provider to use
        location_source_entity_id = f"select.fmd_{self._entry.data['id']}_location_source"
        location_source_state = self.hass.states.get(location_source_entity_id)
        
        # Determine provider based on selected option
        provider = "all"  # Default
        if location_source_state:
            selected_option = location_source_state.state
            provider_map = {
                "All Providers (Default)": "all",
                "GPS Only (Accurate)": "gps",
                "Cell Only (Fast)": "cell",
                "Last Known (No Request)": "last"
            }
            provider = provider_map.get(selected_option, "all")
            _LOGGER.info(f"Using location source: {selected_option} (provider={provider})")
        else:
            _LOGGER.warning(f"Location source select entity not found: {location_source_entity_id}, using default 'all'")
        
        try:
            # Send command to device to request a new location update
            _LOGGER.info(f"Sending location request command to device (provider={provider})...")
            success = await tracker.api.request_location(provider=provider)
            
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
        self._attr_name = "Volume: Ring device"

    @property
    def device_info(self) -> dict[str, Any]:
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
        self._attr_name = "Lock device"

    @property
    def device_info(self) -> dict[str, Any]:
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
        self._attr_unique_id = f"{entry.entry_id}_capture_front_camera"
        self._attr_name = "Photo: Capture front"

    @property
    def device_info(self) -> dict[str, Any]:
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
            # Send camera front command to device using convenience method
            _LOGGER.info("Sending front camera capture command to device...")
            success = await tracker.api.take_picture("front")
            
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
        self._attr_unique_id = f"{entry.entry_id}_capture_rear_camera"
        self._attr_name = "Photo: Capture rear"

    @property
    def device_info(self) -> dict[str, Any]:
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
            # Send camera back command to device using convenience method
            _LOGGER.info("Sending rear camera capture command to device...")
            success = await tracker.api.take_picture("back")
            
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
        self._attr_name = "Photo: Download"

    async def _async_decrypt_data_blob(self, api: Any, blob: str) -> bytes:
        """Decrypt a data blob in an executor to avoid blocking the event loop.
        
        Args:
            api: The FmdApi instance
            blob: Base64-encoded encrypted blob from the server
            
        Returns:
            Decrypted bytes
        """
        return await self.hass.async_add_executor_job(
            api.decrypt_data_blob, blob
        )

    @property
    def device_info(self) -> dict[str, Any]:
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
            
            # Create media directory with device-specific subdirectory
            # Use /media for Docker/Core installations, falls back to config/media for HAOS
            try:
                media_base = Path("/media")
                if not media_base.exists() or not media_base.is_dir():
                    # Fall back to config/media for Home Assistant OS
                    media_base = Path(self.hass.config.path("media"))
                
                # Use device ID for subdirectory to separate photos from multiple devices
                device_id = self._entry.data["id"]
                media_dir = media_base / "fmd" / device_id
                media_dir.mkdir(parents=True, exist_ok=True)
                _LOGGER.info("Saving photos to: %s", media_dir)
            except Exception as e:
                _LOGGER.error("Failed to create media directory: %s", e)
                return
            
            # Download and save each photo
            successful_downloads = 0
            skipped_duplicates = 0
            
            _LOGGER.info("Processing %s photo(s)...", len(pictures))
            
            for idx, blob in enumerate(pictures):
                try:
                    _LOGGER.debug("Processing photo %s/%s", idx + 1, len(pictures))
                    
                    # Decrypt the photo (run in executor to avoid blocking event loop)
                    decrypted = await self._async_decrypt_data_blob(tracker.api, blob)
                    image_bytes = base64.b64decode(decrypted)
                    
                    _LOGGER.debug("Photo %s: Decrypted, size = %s bytes", idx + 1, len(image_bytes))
                    
                    # Generate content hash for duplicate detection
                    content_hash = hashlib.sha256(image_bytes).hexdigest()[:8]
                    _LOGGER.debug("Photo %s: Content hash = %s", idx + 1, content_hash)
                    
                    # Try to extract EXIF timestamp
                    timestamp_str = None
                    try:
                        img = Image.open(io.BytesIO(image_bytes))
                        
                        # Try to get EXIF data using getexif() (newer method)
                        exif_data = img.getexif()
                        
                        if exif_data:
                            _LOGGER.debug("Photo %s: EXIF data found with %s tags", idx + 1, len(exif_data))
                            
                            # Try multiple timestamp tags in order of preference
                            # 36867 = DateTimeOriginal (when photo was taken)
                            # 36868 = DateTimeDigitized (when photo was digitized)
                            # 306 = DateTime (last modification time)
                            datetime_value = None
                            tag_used = None
                            
                            for tag_id, tag_name in [(36867, "DateTimeOriginal"), (36868, "DateTimeDigitized"), (306, "DateTime")]:
                                datetime_value = exif_data.get(tag_id)
                                if datetime_value:
                                    tag_used = tag_name
                                    _LOGGER.debug("Photo %s: Found %s tag with value: %s", idx + 1, tag_name, datetime_value)
                                    break
                            
                            if datetime_value:
                                # Parse EXIF datetime format: "2025:10:19 15:00:34"
                                # Strip any extra whitespace or null bytes
                                datetime_clean = str(datetime_value).strip().rstrip('\x00')
                                dt = datetime.strptime(datetime_clean, "%Y:%m:%d %H:%M:%S")
                                timestamp_str = dt.strftime("%Y%m%d_%H%M%S")
                                _LOGGER.info("Photo %s: Extracted EXIF timestamp from %s: %s", idx + 1, tag_used, timestamp_str)
                            else:
                                _LOGGER.warning("Photo %s: No timestamp tags found in EXIF (tried 36867, 36868, 306)", idx + 1)
                        else:
                            _LOGGER.warning("Photo %s: No EXIF data found in image", idx + 1)
                    except Exception as e:
                        _LOGGER.warning("Photo %s: Could not extract EXIF timestamp: %s", idx + 1, e, exc_info=True)
                    
                    # Generate filename with timestamp if available, otherwise hash-only
                    if timestamp_str:
                        filename = f"photo_{timestamp_str}_{content_hash}.jpg"
                    else:
                        filename = f"photo_{content_hash}.jpg"
                    
                    filepath = media_dir / filename
                    
                    _LOGGER.debug("Photo %s: Generated filename: %s", idx + 1, filename)
                    
                    # Skip if file already exists (duplicate)
                    if filepath.exists():
                        _LOGGER.info("Photo %s: Skipping duplicate (file exists): %s", idx + 1, filename)
                        skipped_duplicates += 1
                        continue
                    
                    # Save to file (use executor to avoid blocking I/O)
                    await self.hass.async_add_executor_job(filepath.write_bytes, image_bytes)
                    successful_downloads += 1
                    _LOGGER.info("Photo %s: Saved successfully: %s", idx + 1, filename)
                    
                except Exception as e:
                    _LOGGER.error("Failed to decrypt/save photo %s: %s", idx + 1, e, exc_info=True)
            
            _LOGGER.info("Successfully downloaded %s new photo(s) to %s (skipped %s duplicate(s))", 
                        successful_downloads, media_dir, skipped_duplicates)
            
            # Check if auto-cleanup is enabled
            auto_cleanup_switch = self.hass.data[DOMAIN][self._entry.entry_id].get("photo_auto_cleanup_switch")
            if auto_cleanup_switch and auto_cleanup_switch.is_on:
                # Get max photos to retain setting
                max_photos_number = self.hass.data[DOMAIN][self._entry.entry_id].get("max_photos_number")
                if max_photos_number:
                    max_to_retain = int(max_photos_number.native_value)
                    await self._cleanup_old_photos(media_dir, max_to_retain)
            
            # Update photo count sensor
            photo_sensor = self.hass.data[DOMAIN][self._entry.entry_id].get("photo_count_sensor")
            if photo_sensor:
                photo_sensor.update_photo_count(len(pictures))
                photo_sensor.async_write_ha_state()
                _LOGGER.info("Updated photo count sensor")
            else:
                _LOGGER.warning("Could not find photo count sensor to update")
                
        except Exception as e:
            _LOGGER.error("Error downloading photos: %s", e, exc_info=True)

    async def _cleanup_old_photos(self, media_dir: Path, max_to_retain: int) -> None:
        """Delete oldest photos if count exceeds retention limit.
        
        Args:
            media_dir: Directory containing photos
            max_to_retain: Maximum number of photos to keep
        """
        try:
            # Get all photos in the directory
            photos = list(media_dir.glob("*.jpg"))
            photo_count = len(photos)
            
            if photo_count <= max_to_retain:
                _LOGGER.debug("Photo cleanup: %d photos, limit %d - no cleanup needed", 
                            photo_count, max_to_retain)
                return
            
            photos_to_delete = photo_count - max_to_retain
            
            _LOGGER.warning("📸 AUTO-CLEANUP: %d photo(s) exceed retention limit of %d", 
                          photos_to_delete, max_to_retain)
            _LOGGER.warning("🗑️ Deleting %d oldest photo(s)...", photos_to_delete)
            
            # Sort by file modification time (oldest first)
            photos_sorted = sorted(photos, key=lambda p: p.stat().st_mtime)
            
            deleted_count = 0
            for photo in photos_sorted[:photos_to_delete]:
                try:
                    _LOGGER.info("🗑️ Deleting old photo: %s", photo.name)
                    await self.hass.async_add_executor_job(photo.unlink)
                    deleted_count += 1
                except Exception as e:
                    _LOGGER.error("Failed to delete photo %s: %s", photo.name, e)
            
            _LOGGER.warning("✅ Auto-cleanup complete: Deleted %d photo(s), %d remaining", 
                          deleted_count, photo_count - deleted_count)
            
        except Exception as e:
            _LOGGER.error("Error during photo cleanup: %s", e, exc_info=True)


class FmdWipeDeviceButton(ButtonEntity):
    """Button entity to perform factory reset / device wipe.
    
    ⚠️ DANGEROUS: This will erase ALL data on the device!
    Requires the Device Wipe Safety switch to be enabled first.
    """

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_wipe_device"
        self._attr_name = "Wipe: ⚠️ Execute ⚠️"

    @property
    def icon(self):
        """Return the icon for this button."""
        return "mdi:delete-forever"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"FMD {self._entry.data['id']}",
            "manufacturer": "FMD",
            "model": "Device Tracker",
        }

    async def async_press(self) -> None:
        """Handle the button press - wipe device if safety switch is enabled."""
        # Check if safety switch is enabled
        safety_switch_entity_id = f"switch.fmd_{self._entry.data['id']}_device_wipe_safety"
        safety_switch_state = self.hass.states.get(safety_switch_entity_id)
        
        if not safety_switch_state or safety_switch_state.state != "on":
            _LOGGER.error("❌❌❌ DEVICE WIPE BLOCKED ❌❌❌")
            _LOGGER.error("⚠️ The 'Device Wipe Safety' switch is NOT enabled!")
            _LOGGER.error("⚠️ You must turn ON the safety switch before the wipe button will work")
            _LOGGER.error("⚠️ This is a safety feature to prevent accidental data loss")
            _LOGGER.error("💡 Steps: 1) Enable 'Device Wipe Safety' switch  2) Press this button within 60 seconds")
            return
        
        _LOGGER.critical("🚨🚨🚨 DEVICE WIPE COMMAND EXECUTING 🚨🚨🚨")
        _LOGGER.critical("⚠️ This will PERMANENTLY ERASE ALL DATA on the device!")
        _LOGGER.critical("⚠️ This action CANNOT be undone!")
        
        # Get the tracker to access its API
        tracker = self.hass.data[DOMAIN][self._entry.entry_id].get("tracker")
        if not tracker:
            _LOGGER.error("Could not find tracker to send wipe command")
            return
        
        try:
            # Send the delete/wipe command
            success = await tracker.api.send_command("delete")
            
            if success:
                _LOGGER.critical("✅ DEVICE WIPE COMMAND SENT TO SERVER")
                _LOGGER.critical("📱 The device will receive the wipe command and factory reset")
                _LOGGER.critical("🔄 All data on the device will be permanently erased")
                _LOGGER.critical("⚠️ This cannot be undone or cancelled once the device receives it")
                
                # Automatically disable the safety switch after use
                # This prevents accidental repeated presses
                safety_switch = self.hass.data[DOMAIN][self._entry.entry_id].get("wipe_safety_switch")
                if safety_switch:
                    await safety_switch.async_turn_off()
                    _LOGGER.warning("Safety switch automatically disabled to prevent repeated wipe commands")
            else:
                _LOGGER.error("❌ FAILED to send device wipe command to server")
                _LOGGER.error("The device was NOT wiped - check server connectivity and try again")
                
        except Exception as e:
            _LOGGER.error("Error sending wipe command: %s", e, exc_info=True)

