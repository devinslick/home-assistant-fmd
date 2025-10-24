"""Test FMD sensor entities."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from homeassistant.core import HomeAssistant

from custom_components.fmd.const import DOMAIN
from conftest import setup_integration


async def test_photo_count_sensor(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo count sensor."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "sensor.fmd_test_user_photo_count"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "0"


async def test_photo_count_after_download(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo count updates after download."""
    import base64
    
    # Return encrypted blobs
    mock_fmd_api.create.return_value.get_pictures.return_value = [
        "encrypted_blob_1",
        "encrypted_blob_2",
        "encrypted_blob_3",
    ]
    
    # Mock decrypt_data_blob to return base64-encoded fake image data
    fake_image = base64.b64encode(b"fake_jpeg_data").decode('utf-8')
    mock_fmd_api.create.return_value.decrypt_data_blob.return_value = fake_image
    
    # Setup integration BEFORE patching Path methods
    await setup_integration(hass, mock_fmd_api)
    
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.write_bytes"), \
         patch("pathlib.Path.exists", return_value=False), \
         patch("pathlib.Path.glob") as mock_glob:
        
        # Download photos
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )
        
        # Mock counting downloaded files
        mock_photo1 = MagicMock()
        mock_photo2 = MagicMock()
        mock_photo3 = MagicMock()
        mock_glob.return_value = [mock_photo1, mock_photo2, mock_photo3]
        
        # Trigger sensor update
        await hass.async_block_till_done()
        
        state = hass.states.get("sensor.fmd_test_user_photo_count")
        assert state.state == "3"


async def test_photo_count_attributes(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo count sensor attributes."""
    import base64
    
    # Return encrypted blobs
    mock_fmd_api.create.return_value.get_pictures.return_value = [
        "encrypted_blob_1",
        "encrypted_blob_2",
    ]
    
    # Mock decrypt_data_blob to return base64-encoded fake image data
    fake_image = base64.b64encode(b"fake_jpeg_data").decode('utf-8')
    mock_fmd_api.create.return_value.decrypt_data_blob.return_value = fake_image
    
    # Setup integration BEFORE patching Path methods
    await setup_integration(hass, mock_fmd_api)
    
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.write_bytes"), \
         patch("pathlib.Path.exists", return_value=False), \
         patch("pathlib.Path.glob") as mock_glob:
        
        # Download photos
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )
        
        # Mock files
        mock_glob.return_value = [MagicMock(), MagicMock()]
        
        await hass.async_block_till_done()
        
        state = hass.states.get("sensor.fmd_test_user_photo_count")
        assert "last_download_count" in state.attributes
        assert "last_download_time" in state.attributes
        assert state.attributes["last_download_count"] == 2


async def test_photo_count_after_cleanup(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo count updates after cleanup."""
    import base64
    
    # Return encrypted blob
    mock_fmd_api.create.return_value.get_pictures.return_value = ["encrypted_blob_1"]
    
    # Mock decrypt_data_blob to return base64-encoded fake image data
    fake_image = base64.b64encode(b"fake_jpeg_data").decode('utf-8')
    mock_fmd_api.create.return_value.decrypt_data_blob.return_value = fake_image
    
    # Setup integration BEFORE patching Path methods
    await setup_integration(hass, mock_fmd_api)
    
    # Enable auto-cleanup
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_photo_auto_cleanup"},
        blocking=True,
    )
    
    # Now patch for photo download operation
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.write_bytes"), \
         patch("pathlib.Path.exists", return_value=False), \
         patch("pathlib.Path.glob") as mock_glob, \
         patch("pathlib.Path.unlink"):
        
        # Simulate old photos exist, then after cleanup only new photo
        old_photo = MagicMock()
        old_photo.stat.return_value.st_mtime = 0  # Very old
        new_photo = MagicMock()
        new_photo.stat.return_value.st_mtime = 9999999999  # New
        
        # glob called multiple times: once to find photos to delete, once to count after
        mock_glob.side_effect = [
            [old_photo],  # First call - finds old photo to delete
            [new_photo],  # Second call - count after cleanup
        ]
        
        # Download photos (will trigger cleanup)
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )
        await hass.async_block_till_done()
        
        state = hass.states.get("sensor.fmd_test_user_photo_count")
        assert state.state == "1"


async def test_photo_count_icon(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo count sensor icon."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "sensor.fmd_test_user_photo_count"
    state = hass.states.get(entity_id)
    assert state.attributes["icon"] == "mdi:image-multiple"
