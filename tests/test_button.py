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
    
    # Mock decrypt_data_blob to return DIFFERENT base64-encoded fake image data
    # So they don't hash to the same value and get skipped as duplicates
    # Note: decrypt_data_blob is a sync function called in executor
    fake_image_1 = base64.b64encode(b"fake_jpeg_data_1_unique").decode('utf-8')
    fake_image_2 = base64.b64encode(b"fake_jpeg_data_2_different").decode('utf-8')
    
    # Use a function instead of list to avoid StopIteration issues
    decrypt_values = {
        "encrypted_blob_1": fake_image_1,
        "encrypted_blob_2": fake_image_2,
    }
    mock_fmd_api.create.return_value.decrypt_data_blob.side_effect = lambda blob: decrypt_values.get(blob, fake_image_1)
    
    # Setup integration BEFORE patching Path methods
    await setup_integration(hass, mock_fmd_api)
    
    # Use a callable for exists() to handle any number of calls
    # Returns True for directories, False for photo files
    def exists_side_effect(self):
        return "photo_" not in str(self)
    
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.is_dir", return_value=True), \
         patch("pathlib.Path.exists", exists_side_effect), \
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
    from datetime import datetime, timedelta
    
    # Return encrypted blob
    mock_fmd_api.create.return_value.get_pictures.return_value = ["encrypted_blob_1"]
    
    # Mock decrypt_data_blob to return base64-encoded fake image data
    fake_image = base64.b64encode(b"fake_jpeg_data_cleanup_test").decode('utf-8')
    mock_fmd_api.create.return_value.decrypt_data_blob.return_value = fake_image
    
    # Setup integration BEFORE patching Path methods
    await setup_integration(hass, mock_fmd_api)
    
    # Set max photos to 3
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.fmd_test_user_max_photos", "value": 3},
        blocking=True,
    )
    
    # Enable auto-cleanup
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_photo_auto_cleanup"},
        blocking=True,
    )
    
    # Create mock old photos (4 old photos + will add 1 new = 5 total, limit is 3, so 2 should be deleted)
    from unittest.mock import MagicMock
    old_photos = []
    for i in range(4):
        photo = MagicMock()
        photo.stat.return_value.st_mtime = (datetime.now() - timedelta(days=i+1)).timestamp()
        photo.name = f"old_photo_{i}.jpg"
        old_photos.append(photo)
    
    # The new photo that will be downloaded
    new_photo = MagicMock()
    new_photo.stat.return_value.st_mtime = datetime.now().timestamp()
    new_photo.name = "new_photo.jpg"
    
    # Use a callable for exists() that returns True for directories, False for photo files
    def exists_side_effect(self):
        return "photo_" not in str(self)
    
    # Now patch only for the photo download operation
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.write_bytes"), \
         patch("pathlib.Path.is_dir", return_value=True), \
         patch("pathlib.Path.exists", exists_side_effect), \
         patch("pathlib.Path.glob") as mock_glob:
    
        # glob returns all photos (4 old + 1 new = 5) when cleanup runs
        mock_glob.return_value = old_photos + [new_photo]
    
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )
    
        # Verify the 2 oldest photos were deleted (5 photos - 3 limit = 2 to delete)
        # The photos are sorted by timestamp, so photos[0] and photos[1] are oldest
        old_photos[0].unlink.assert_called_once()
        old_photos[1].unlink.assert_called_once()
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
