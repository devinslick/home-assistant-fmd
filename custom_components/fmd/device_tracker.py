"""Device tracker for FMD integration."""
from datetime import datetime, timedelta
import json
import logging

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import DOMAIN, DEFAULT_POLLING_INTERVAL, DEFAULT_HIGH_FREQUENCY_INTERVAL
from .fmd_client.fmd_api import FmdApi

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the FMD device tracker."""
    _LOGGER.info("Setting up FMD device tracker for %s", entry.data["id"])
    api = await FmdApi.create(entry.data["url"], entry.data["id"], entry.data["password"])
    polling_interval = entry.data.get("polling_interval", DEFAULT_POLLING_INTERVAL)
    # Get allow_inaccurate setting, defaulting to False (blocking enabled)
    # For backward compatibility, also check old "block_inaccurate" key
    allow_inaccurate = entry.data.get("allow_inaccurate_locations", 
                                      not entry.data.get("block_inaccurate", True))
    block_inaccurate = not allow_inaccurate  # Internal logic still uses block

    tracker = FmdDeviceTracker(hass, entry, api, polling_interval, block_inaccurate)
    
    # Store tracker in hass.data for access by other entities
    hass.data[DOMAIN][entry.entry_id]["tracker"] = tracker
    
    # Fetch initial location before adding the entity
    _LOGGER.info("Fetching initial location data...")
    await tracker.async_update()
    _LOGGER.info("Initial location: %s", tracker._location)
    
    async_add_entities([tracker])
    _LOGGER.info("FMD device tracker added")

    # Start the polling timer
    tracker.start_polling()

class FmdDeviceTracker(TrackerEntity):
    """Represent a tracked device."""

    _attr_has_entity_name = True
    _attr_entity_category = None  # Explicitly set to None to ensure it's a primary entity

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: FmdApi, polling_interval: int, block_inaccurate: bool):
        """Initialize the device tracker."""
        self.hass = hass
        self._entry = entry
        self.api = api
        self._normal_interval = polling_interval  # Normal polling interval
        self._polling_interval = polling_interval  # Current active interval
        self._high_frequency_interval = DEFAULT_HIGH_FREQUENCY_INTERVAL  # High-freq interval
        self._high_frequency_mode = False  # Whether high-freq mode is active
        self._block_inaccurate = block_inaccurate
        self._location = None
        self._attr_name = None  # Use device name only, no suffix
        self._battery_level = None
        self._last_poll_time = None  # When we last polled FMD server
        self._remove_timer = None

    @property
    def polling_interval(self):
        """Return the polling interval."""
        return self._polling_interval

    def start_polling(self):
        """Start the polling timer."""
        if self._remove_timer:
            self._remove_timer()
        
        async def update_locations(now=None):
            """Update device locations."""
            await self.async_update()
            self.async_write_ha_state()
        
        _LOGGER.info("Starting polling with interval: %s minutes", self._polling_interval)
        self._remove_timer = async_track_time_interval(
            self.hass, 
            update_locations, 
            timedelta(minutes=self._polling_interval)
        )

    def set_polling_interval(self, interval_minutes: int):
        """Update the polling interval and restart the timer."""
        _LOGGER.info("Updating polling interval from %s to %s minutes", self._polling_interval, interval_minutes)
        self._polling_interval = interval_minutes
        # If not in high-frequency mode, also update the stored normal interval
        if not self._high_frequency_mode:
            self._normal_interval = interval_minutes
        self.start_polling()

    def set_high_frequency_interval(self, interval_minutes: int):
        """Update the high-frequency interval value."""
        _LOGGER.info("Setting high-frequency interval to %s minutes", interval_minutes)
        self._high_frequency_interval = interval_minutes
        # If already in high-frequency mode, apply the new interval immediately
        if self._high_frequency_mode:
            _LOGGER.info("High-frequency mode is active, applying new interval immediately")
            self.set_polling_interval(interval_minutes)

    async def set_high_frequency_mode(self, enabled: bool):
        """Enable or disable high-frequency mode."""
        _LOGGER.info("High-frequency mode %s", "enabled" if enabled else "disabled")
        self._high_frequency_mode = enabled
        
        if enabled:
            # Request an immediate location update from the device
            _LOGGER.info("Requesting immediate location update from device...")
            try:
                success = await self.api.request_location(provider="all")
                if success:
                    _LOGGER.info("Location request sent. Waiting 10 seconds for device response...")
                    import asyncio
                    await asyncio.sleep(10)
                    
                    # Fetch the updated location
                    await self.async_update()
                    self.async_write_ha_state()
                    _LOGGER.info("Initial high-frequency location update completed")
                else:
                    _LOGGER.warning("Failed to request location from device")
            except Exception as e:
                _LOGGER.error("Error requesting location in high-frequency mode: %s", e, exc_info=True)
            
            # Switch to high-frequency polling interval
            self.set_polling_interval(self._high_frequency_interval)
        else:
            # Switch back to normal polling interval
            self.set_polling_interval(self._normal_interval)

    async def async_will_remove_from_hass(self) -> None:
        """Clean up when entity is removed."""
        if self._remove_timer:
            self._remove_timer()
            self._remove_timer = None

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._entry.entry_id}_tracker"

    @property
    def device_info(self):
        """Return device info to link entities together."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"FMD {self._entry.data['id']}",
            "manufacturer": "FMD",
            "model": "Device Tracker",
        }

    @property
    def latitude(self):
        """Return latitude value of the device."""
        return self._location.get("lat") if self._location else None

    @property
    def longitude(self):
        """Return longitude value of the device."""
        return self._location.get("lon") if self._location else None

    @property
    def source_type(self) -> SourceType:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        attributes = {}
        
        if self._battery_level is not None:
            attributes["battery_level"] = self._battery_level
        
        # Add timestamp when we polled the FMD server
        if self._last_poll_time is not None:
            attributes["last_poll_time"] = self._last_poll_time
        
        # Add other location metadata if available
        if self._location:
            if "provider" in self._location:
                attributes["provider"] = self._location["provider"]
            
            # Time when FMD client sent location to server (human-readable)
            if "time" in self._location:
                attributes["device_timestamp"] = self._location["time"]
            
            # Unix timestamp (milliseconds) when FMD client sent location to server
            # Store as string to prevent comma formatting in UI
            if "date" in self._location:
                attributes["device_timestamp_ms"] = str(self._location["date"])
            
            # GPS accuracy in meters (optional)
            if "accuracy" in self._location:
                attributes["gps_accuracy"] = self._location["accuracy"]
            
            # Altitude in meters (optional)
            if "altitude" in self._location:
                attributes["altitude"] = self._location["altitude"]
            
            # Speed in m/s - only present when moving (optional)
            if "speed" in self._location:
                attributes["speed"] = self._location["speed"]
            
            # Heading/direction 0-360° - only present when moving (optional)
            if "heading" in self._location:
                attributes["heading"] = self._location["heading"]
        
        return attributes

    def _is_location_accurate(self, location_data: dict) -> bool:
        """
        Determine if a location is accurate based on the provider.
        
        Accuracy hierarchy (most to least accurate):
        1. fused - Android Fused Location Provider (combines GPS, WiFi, cell, sensors - highly accurate)
        2. gps - Direct GPS satellite positioning (highly accurate)
        3. network - Cell tower + WiFi triangulation (moderate accuracy)
        4. BeaconDB - WiFi beacon database lookup (least accurate, often blocked)
        
        Returns True if location is considered accurate, False otherwise.
        """
        provider = location_data.get("provider", "").lower()
        
        # Fused, GPS, and network are considered accurate
        if provider in ("fused", "gps", "network"):
            return True
        
        # BeaconDB and unknown providers are considered inaccurate
        if provider in ("beacondb", ""):
            return False
        
        # For any other unknown providers, log a warning and consider them inaccurate
        _LOGGER.warning("Unknown location provider '%s', treating as inaccurate", provider)
        return False

    async def async_update(self):
        """Update the device location."""
        try:
            _LOGGER.info("=== Starting location update ===")
            
            # Record the time when we're polling the FMD server
            poll_time = dt_util.now()
            
            # If filtering is enabled, fetch multiple recent locations to handle cases
            # where the most recent location is inaccurate (e.g., BeaconDB) but a slightly
            # older accurate location (e.g., GPS) exists. If filtering is disabled, just
            # fetch the most recent location.
            num_locations_to_check = 5 if self._block_inaccurate else 1
            
            _LOGGER.debug("Fetching up to %d recent location(s) (filtering %s)...", 
                         num_locations_to_check, "enabled" if self._block_inaccurate else "disabled")
            location_blobs = await self.api.get_all_locations(num_to_get=num_locations_to_check, skip_empty=True)
            _LOGGER.info(f"=== Received {len(location_blobs)} location blob(s) ===")
            _LOGGER.debug("Received %d location blobs", len(location_blobs) if location_blobs else 0)
            
            if location_blobs:
                selected_location = None
                
                # Decrypt and check each location blob, most recent first
                for idx, blob in enumerate(location_blobs):
                    _LOGGER.debug("Checking location blob %d/%d (type: %s, length: %d)", 
                                idx + 1, len(location_blobs), type(blob).__name__, len(blob) if blob else 0)
                    
                    if not blob:
                        _LOGGER.warning("Empty blob at index %d", idx)
                        continue
                    
                    # Decrypt and parse the location blob (synchronous call)
                    _LOGGER.debug("Decrypting location blob %d...", idx)
                    decrypted_bytes = self.api.decrypt_data_blob(blob)
                    location_data = json.loads(decrypted_bytes)
                    
                    provider = location_data.get("provider", "unknown")
                    _LOGGER.debug("Location %d: provider=%s", idx, provider)
                    
                    # If filtering is disabled, use the first (most recent) location
                    if not self._block_inaccurate:
                        _LOGGER.debug("Filtering disabled, using most recent location (index %d)", idx)
                        selected_location = location_data
                        break
                    
                    # If filtering is enabled, look for the most recent accurate location
                    if self._is_location_accurate(location_data):
                        _LOGGER.info("Found accurate location at index %d (provider: %s)", idx, provider)
                        selected_location = location_data
                        break
                    else:
                        _LOGGER.debug("Location %d from provider '%s' is inaccurate, checking next...", idx, provider)
                
                # Check if we found a suitable location
                if selected_location:
                    self._location = selected_location
                    provider = self._location.get("provider", "unknown")
                    _LOGGER.debug("Using location from provider: %s", provider)
                    
                    # Store the poll time (when we queried the server)
                    self._last_poll_time = poll_time.isoformat()
                    
                    # Update battery level when location is updated
                    if "bat" in self._location:
                        try:
                            self._battery_level = int(self._location["bat"])
                            _LOGGER.debug("Battery level: %s%%", self._battery_level)
                        except (ValueError, TypeError):
                            _LOGGER.warning("Invalid battery value: %s", self._location.get("bat"))
                            self._battery_level = None
                    
                    _LOGGER.info("Updated location: lat=%s, lon=%s, battery=%s%%, time=%s", 
                                self._location.get('lat'), 
                                self._location.get('lon'),
                                self._battery_level,
                                self._location.get('time'))
                else:
                    _LOGGER.warning(
                        "No accurate locations found in the %d most recent location(s). "
                        "Keeping previous location. Toggle 'Allow Inaccurate Locations' to accept all locations.",
                        len(location_blobs)
                    )
            else:
                _LOGGER.warning("No location blobs returned from API")
        except Exception as e:
            _LOGGER.error("Error getting location: %s", e, exc_info=True)