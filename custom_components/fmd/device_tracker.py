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

from .const import DOMAIN, DEFAULT_POLLING_INTERVAL
from .fmd_client.fmd_api import FmdApi

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the FMD device tracker."""
    _LOGGER.info("Setting up FMD device tracker for %s", entry.data["id"])
    api = await FmdApi.create(entry.data["url"], entry.data["id"], entry.data["password"])
    polling_interval = entry.data.get("polling_interval", DEFAULT_POLLING_INTERVAL)
    block_inaccurate = entry.data.get("block_inaccurate", True)

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
        self._polling_interval = polling_interval
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
        self.start_polling()

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
        
        return attributes

    def _is_location_accurate(self, location_data: dict) -> bool:
        """
        Determine if a location is accurate based on the provider.
        
        Accuracy hierarchy (most to least accurate):
        1. gps - Direct GPS satellite positioning (most accurate)
        2. network - Cell tower + WiFi triangulation (moderate accuracy)
        3. BeaconDB - WiFi beacon database lookup (least accurate, often blocked)
        
        Returns True if location is considered accurate, False otherwise.
        """
        provider = location_data.get("provider", "").lower()
        
        # GPS and network are considered accurate
        if provider in ("gps", "network"):
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
            
            _LOGGER.debug("Fetching location data...")
            location_blobs = await self.api.get_all_locations(num_to_get=1, skip_empty=True)
            _LOGGER.info(f"=== Received {len(location_blobs)} location blob(s) ===")
            _LOGGER.debug("Received %d location blobs", len(location_blobs) if location_blobs else 0)
            
            if location_blobs:
                blob = location_blobs[0]
                _LOGGER.debug("Location blob type: %s, length: %d", type(blob).__name__, len(blob) if blob else 0)
                if blob:
                    _LOGGER.debug("First 100 chars of blob: %s", blob[:100] if len(blob) > 100 else blob)
                else:
                    _LOGGER.warning("Received empty blob from server")
                    return
                
                # Decrypt and parse the location blob (synchronous call)
                _LOGGER.debug("Decrypting location blob...")
                decrypted_bytes = self.api.decrypt_data_blob(blob)
                _LOGGER.debug("Decrypted bytes: %s", decrypted_bytes)
                
                location_data = json.loads(decrypted_bytes)
                
                # Check if location should be filtered based on accuracy
                if self._block_inaccurate and not self._is_location_accurate(location_data):
                    provider = location_data.get("provider", "unknown")
                    _LOGGER.info(
                        "Skipping inaccurate location update from provider '%s' (filtering enabled)",
                        provider
                    )
                    return
                
                # Location is accurate (or filtering is disabled), accept the update
                self._location = location_data
                provider = self._location.get("provider", "unknown")
                _LOGGER.debug("Accepted location from provider: %s", provider)
                
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
                _LOGGER.warning("No location blobs returned from API")
        except Exception as e:
            _LOGGER.error("Error getting location: %s", e, exc_info=True)