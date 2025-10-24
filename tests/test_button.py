"""Test FMD button entities."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant

from custom_components.fmd.const import DOMAIN
from conftest import setup_integration


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
        {"entity_id": "button.fmd_test_user_volume_ring_device"},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    mock_fmd_api.create.return_value.send_command.assert_called_once_with("ring")


async def test_lock_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test lock button."""
    await setup_integration(hass, mock_fmd_api)
    
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_lock_device"},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    mock_fmd_api.create.return_value.send_command.assert_called_once_with("lock")


async def test_capture_front_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test capture front photo button."""
    await setup_integration(hass, mock_fmd_api)
    
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_capture_front"},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    mock_fmd_api.create.return_value.take_picture.assert_called_once_with("front")


async def test_capture_rear_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test capture rear photo button."""
    await setup_integration(hass, mock_fmd_api)
    
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_capture_rear"},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    mock_fmd_api.create.return_value.take_picture.assert_called_once_with("back")


async def test_download_photos_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test download photos button."""
    import base64
    
    # Return encrypted blobs (just strings)
    mock_fmd_api.create.return_value.get_pictures.return_value = [
        "encrypted_blob_1",
        "encrypted_blob_2",
    ]
    
    # Mock decrypt_data_blob to return base64-encoded fake image data
    fake_image_1 = base64.b64encode(b"fake_jpeg_data_1").decode('utf-8')
    fake_image_2 = base64.b64encode(b"fake_jpeg_data_2").decode('utf-8')
    mock_fmd_api.create.return_value.decrypt_data_blob.side_effect = [
        fake_image_1,
        fake_image_2,
    ]
    
    # Setup integration BEFORE patching Path methods
    await setup_integration(hass, mock_fmd_api)
    
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.exists", return_value=False), \
         patch("pathlib.Path.write_bytes") as mock_write:
        
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )
        
        mock_fmd_api.create.return_value.get_pictures.assert_called_once()
        # Verify 2 photos were written
        assert mock_write.call_count == 2


async def test_download_photos_with_cleanup(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test download photos with auto-cleanup enabled."""
    import base64
    
    # Return encrypted blob
    mock_fmd_api.create.return_value.get_pictures.return_value = ["encrypted_blob_1"]
    
    # Mock decrypt_data_blob to return base64-encoded fake image data
    fake_image = base64.b64encode(b"fake_jpeg_data_1").decode('utf-8')
    mock_fmd_api.create.return_value.decrypt_data_blob.return_value = fake_image
    
    # Setup integration BEFORE patching Path methods
    await setup_integration(hass, mock_fmd_api)
    
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_photo_auto_cleanup"},
        blocking=True,
    )
    
    # Now patch only for the photo download operation
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.write_bytes"), \
         patch("pathlib.Path.exists", return_value=False), \
         patch("pathlib.Path.glob") as mock_glob:
    
        # Simulate old photos
        from unittest.mock import MagicMock
        old_photo = MagicMock()
        old_photo.stat.return_value.st_mtime = 0  # Very old timestamp
        old_photo.name = "old_photo.jpg"
        mock_glob.return_value = [old_photo]
    
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )
    
        # Verify photo.unlink() was called on the old photo
        old_photo.unlink.assert_called_once()
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
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    mock_fmd_api.create.return_value.send_command.assert_called_with("delete")
