"""The FMD integration.

Home Assistant integration for FMD (Find My Device).
Built to work with the FMD-FOSS project: https://fmd-foss.org

FMD Project Attribution:
- Created by Nulide (http://nulide.de)
- Maintained by Thore (https://thore.io) and the FMD-FOSS team
- FMD Android: https://gitlab.com/fmd-foss/fmd-android
- FMD Server: https://gitlab.com/fmd-foss/fmd-server

This Integration:
- MIT License - Copyright (c) 2025 Devin Slick
- https://github.com/devinslick/home-assistant-fmd
- A third-party client for FMD servers
"""
from __future__ import annotations

from fmd_api import FmdClient
from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS: list[Platform] = [
    Platform.DEVICE_TRACKER,
    Platform.NUMBER,
    Platform.BUTTON,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FMD from a config entry.

    Raises ConfigEntryNotReady if the device/service is unreachable during setup,
    allowing Home Assistant to retry with exponential backoff.
    """
    # Initialize storage for this entry
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    try:
        # Create API client instance and device info that all platforms can use
        api = await FmdClient.create(
            entry.data["url"], entry.data["id"], entry.data["password"]
        )
    except Exception as err:
        # Raise ConfigEntryNotReady for any connection/authentication issues
        # This allows Home Assistant to retry with exponential backoff instead of
        # failing the entire entry setup permanently
        raise ConfigEntryNotReady(
            f"Failed to connect to FMD server at {entry.data['url']}: {err}"
        ) from err

    hass.data[DOMAIN][entry.entry_id]["api"] = api
    hass.data[DOMAIN][entry.entry_id]["device_info"] = {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": f"FMD {entry.data['id']}",
        "manufacturer": "FMD",
        "model": "Device Tracker",
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
