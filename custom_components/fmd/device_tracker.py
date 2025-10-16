"""Device tracker for FMD integration."""
from datetime import timedelta
import json
import logging

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, DEFAULT_POLLING_INTERVAL
from .fmd_client.fmd_api import FmdApi

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the FMD device tracker."""
    _LOGGER.info("Setting up FMD device tracker for %s", entry.data["id"])
    api = await FmdApi.create(entry.data["url"], entry.data["id"], entry.data["password"])
    polling_interval = entry.data.get("polling_interval", DEFAULT_POLLING_INTERVAL)

    tracker = FmdDeviceTracker(hass, api, polling_interval)
    
    # Fetch initial location before adding the entity
    _LOGGER.info("Fetching initial location data...")
    await tracker.async_update()
    _LOGGER.info("Initial location: %s", tracker._location)
    
    async_add_entities([tracker])
    _LOGGER.info("FMD device tracker added")

    async def update_locations(now=None):
        """Update device locations."""
        await tracker.async_update()
        tracker.async_write_ha_state()

    async_track_time_interval(hass, update_locations, timedelta(minutes=tracker.polling_interval))

class FmdDeviceTracker(TrackerEntity):
    """Represent a tracked device."""

    def __init__(self, hass: HomeAssistant, api: FmdApi, polling_interval: int):
        """Initialize the device tracker."""
        self.hass = hass
        self.api = api
        self._polling_interval = polling_interval
        self._location = None
        self._name = api.fmd_id

    @property
    def polling_interval(self):
        """Return the polling interval."""
        return self._polling_interval

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self.api.fmd_id

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

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

    async def async_update(self):
        """Update the device location."""
        try:
            _LOGGER.info("=== Starting location update ===")
            _LOGGER.debug("Fetching location data...")
            location_blobs = await self.api.get_all_locations(num_to_get=1)
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
                
                # Decrypt and parse the location blob
                _LOGGER.debug("Decrypting location blob...")
                decrypted_bytes = self.api.decrypt_data_blob(blob)
                _LOGGER.debug("Decrypted bytes: %s", decrypted_bytes)
                
                self._location = json.loads(decrypted_bytes)
                _LOGGER.info("Updated location: lat=%s, lon=%s, time=%s", 
                            self._location.get('lat'), 
                            self._location.get('lon'),
                            self._location.get('time'))
            else:
                _LOGGER.warning("No location blobs returned from API")
        except Exception as e:
            _LOGGER.error("Error getting location: %s", e, exc_info=True)