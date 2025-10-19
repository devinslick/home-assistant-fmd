"""Sensor platform for FMD integration."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

if TYPE_CHECKING:
    from .fmd_client.fmd_api import FmdApi

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FMD sensor entities."""
    api: FmdApi = hass.data[DOMAIN][entry.entry_id]["api"]
    device_info = hass.data[DOMAIN][entry.entry_id]["device_info"]

    sensors = [
        FmdPhotoCountSensor(hass, entry, api, device_info),
    ]

    async_add_entities(sensors)

    # Store sensor reference for download button to access
    hass.data[DOMAIN][entry.entry_id]["photo_count_sensor"] = sensors[0]


class FmdPhotoCountSensor(SensorEntity):
    """Sensor that tracks the number of photos available."""

    _attr_has_entity_name = True
    _attr_name = "Photo count"
    _attr_native_unit_of_measurement = "photos"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: FmdApi,
        device_info: dict,
    ) -> None:
        """Initialize the photo count sensor."""
        self.hass = hass
        self.entry = entry
        self.api = api
        self._attr_device_info = device_info
        self._attr_unique_id = f"{entry.entry_id}_photo_count"
        
        self._photo_count = 0
        self._last_download_time = None
        self._photos_in_media_folder = 0

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        return "mdi:image-multiple"

    @property
    def native_value(self) -> int:
        """Return the number of photos available on server."""
        return self._photo_count

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        return {
            "last_download_time": self._last_download_time.isoformat() if self._last_download_time else None,
            "photos_in_media_folder": self._photos_in_media_folder,
        }

    def update_photo_count(self, count: int) -> None:
        """Update the photo count after a download."""
        self._photo_count = count
        self._last_download_time = datetime.now()
        self._update_media_folder_count()

    def _update_media_folder_count(self) -> None:
        """Count photos in the media folder."""
        try:
            # Check /media first (Docker/Core), fall back to config/media (HAOS)
            media_base = Path("/media")
            if not media_base.exists() or not media_base.is_dir():
                media_base = Path(self.hass.config.path("media"))
            media_dir = media_base / "fmd"
            
            if media_dir.exists():
                self._photos_in_media_folder = len(list(media_dir.glob("*.jpg")))
            else:
                self._photos_in_media_folder = 0
        except Exception as e:
            _LOGGER.error(f"Failed to count media folder photos: {e}")
            self._photos_in_media_folder = 0
