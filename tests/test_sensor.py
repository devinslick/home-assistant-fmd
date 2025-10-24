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
    mock_fmd_api.create.return_value.get_photos.return_value = [
        {"filename": "photo1.jpg", "content": b"photo_data_1"},
        {"filename": "photo2.jpg", "content": b"photo_data_2"},
        {"filename": "photo3.jpg", "content": b"photo_data_3"},
    ]
    
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.open"), \
         patch("pathlib.Path.glob") as mock_glob:
        
        await setup_integration(hass, mock_fmd_api)
        
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
    mock_fmd_api.create.return_value.get_photos.return_value = [
        {"filename": "photo1.jpg", "content": b"photo_data_1"},
        {"filename": "photo2.jpg", "content": b"photo_data_2"},
    ]
    
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.open"), \
         patch("pathlib.Path.glob") as mock_glob:
        
        await setup_integration(hass, mock_fmd_api)
        
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
    mock_fmd_api.create.return_value.get_photos.return_value = [
        {"filename": "photo1.jpg", "content": b"photo_data_1"},
    ]
    
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.open"), \
         patch("pathlib.Path.glob") as mock_glob, \
         patch("pathlib.Path.stat") as mock_stat, \
         patch("pathlib.Path.unlink"):
        
        await setup_integration(hass, mock_fmd_api)
        
        # Enable auto-cleanup
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": "switch.fmd_test_user_photo_auto_cleanup"},
            blocking=True,
        )
        
        # Simulate old photos exist
        old_photo = MagicMock()
        old_photo.stat.return_value.st_mtime = 0  # Very old
        mock_glob.return_value = [old_photo]
        
        # Download photos (will trigger cleanup)
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )
        
        # After cleanup, only new photo remains
        mock_glob.return_value = [MagicMock()]
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
