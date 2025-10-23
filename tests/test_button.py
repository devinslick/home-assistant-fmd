"""Test FMD button entities."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.core import HomeAssistant

from custom_components.fmd.const import DOMAIN


async def test_location_update_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test location update button."""
    await setup_integration(hass, mock_fmd_api)
    
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_location_update"},
        blocking=True,
    )
    
    mock_fmd_api.create.return_value.request_location.assert_called_once()


async def test_ring_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ring button."""
    await setup_integration(hass, mock_fmd_api)
    
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_ring"},
        blocking=True,
    )
    
    mock_fmd_api.create.return_value.ring.assert_called_once()


async def test_lock_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test lock button."""
    await setup_integration(hass, mock_fmd_api)
    
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_lock"},
        blocking=True,
    )
    
    mock_fmd_api.create.return_value.lock.assert_called_once()


async def test_capture_front_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test capture front photo button."""
    await setup_integration(hass, mock_fmd_api)
    
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_capture_front_photo"},
        blocking=True,
    )
    
    mock_fmd_api.create.return_value.capture_photo.assert_called_once_with("front")


async def test_capture_rear_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test capture rear photo button."""
    await setup_integration(hass, mock_fmd_api)
    
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_capture_rear_photo"},
        blocking=True,
    )
    
    mock_fmd_api.create.return_value.capture_photo.assert_called_once_with("rear")


async def test_download_photos_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test download photos button."""
    mock_fmd_api.create.return_value.get_photos.return_value = [
        {"filename": "photo1.jpg", "content": b"photo_data_1"},
        {"filename": "photo2.jpg", "content": b"photo_data_2"},
    ]
    
    with patch("pathlib.Path.mkdir"), patch("pathlib.Path.open") as mock_open:
        await setup_integration(hass, mock_fmd_api)
        
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_download_photos"},
            blocking=True,
        )
        
        mock_fmd_api.create.return_value.get_photos.assert_called_once()
        # Verify photos were written
        assert mock_open.call_count == 2


async def test_download_photos_with_cleanup(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test download photos with auto-cleanup enabled."""
    mock_fmd_api.create.return_value.get_photos.return_value = [
        {"filename": "photo1.jpg", "content": b"photo_data_1"},
    ]
    
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.open"), \
         patch("pathlib.Path.glob") as mock_glob, \
         patch("pathlib.Path.stat") as mock_stat, \
         patch("pathlib.Path.unlink") as mock_unlink:
        
        # Setup integration and enable cleanup
        await setup_integration(hass, mock_fmd_api)
        
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": "switch.fmd_test_user_photo_auto_cleanup"},
            blocking=True,
        )
        
        # Simulate old photos
        from unittest.mock import MagicMock
        old_photo = MagicMock()
        mock_glob.return_value = [old_photo]
        mock_stat.return_value.st_mtime = 0  # Very old timestamp
        
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_download_photos"},
            blocking=True,
        )
        
        mock_unlink.assert_called_once()


async def test_wipe_device_button_blocked(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe device button is blocked without safety switch."""
    await setup_integration(hass, mock_fmd_api)
    
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_device"},
        blocking=True,
    )
    
    # Should NOT call wipe API
    mock_fmd_api.create.return_value.wipe_device.assert_not_called()


async def test_wipe_device_button_allowed(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe device button works with safety switch enabled."""
    await setup_integration(hass, mock_fmd_api)
    
    # Enable safety switch
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_device"},
        blocking=True,
    )
    
    mock_fmd_api.create.return_value.wipe_device.assert_called_once()


def get_mock_config_entry():
    """Create a mock config entry."""
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_ID
    
    return ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="test_user",
        data={
            CONF_URL: "https://fmd.example.com",
            CONF_ID: "test_user",
            CONF_PASSWORD: "test_password",
            "polling_interval": 30,
            "allow_inaccurate_locations": False,
            "use_imperial": False,
        },
        source="user",
        entry_id="test_entry_id",
        unique_id="test_user",
        options={},
        discovery_keys={},
    )


async def setup_integration(hass: HomeAssistant, mock_fmd_api: AsyncMock) -> None:
    """Set up integration for testing."""
    config_entry = get_mock_config_entry()
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.fmd.__init__.FmdApi", mock_fmd_api):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
