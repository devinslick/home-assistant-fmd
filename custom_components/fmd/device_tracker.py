"""Device tracker for FMD integration."""
from datetime import timedelta
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
    api = await FmdApi.create(entry.data["url"], entry.data["id"], entry.data["password"])
    polling_interval = entry.data.get("polling_interval", DEFAULT_POLLING_INTERVAL)

    tracker = FmdDeviceTracker(hass, api, polling_interval)
    async_add_entities([tracker])

    async def update_locations(now=None):
        """Update device locations."""
        await tracker.async_update()
        tracker.async_write_ha_state()

    await update_locations()

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
        return self._location["latitude"] if self._location else None

    @property
    def longitude(self):
        """Return longitude value of the device."""
        return self._location["longitude"] if self._location else None

    @property
    def source_type(self) -> SourceType:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    async def async_update(self):
        """Update the device location."""
        try:
            locations = await self.api.get_all_locations()
            if locations:
                self._location = locations[0]
        except Exception as e:
            _LOGGER.error("Error getting location: %s", e)