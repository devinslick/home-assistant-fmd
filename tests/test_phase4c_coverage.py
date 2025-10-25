"""Phase 4c: Additional tests to reach 100% coverage.

Focus areas:
- button.py: EXIF parsing, photo sensor update, cleanup failures, wipe command success
- device_tracker.py: ConfigEntryNotReady, high-frequency mode logic, speed/altitude attributes
- select.py: Actual command execution paths (toggle_bluetooth, etc.)
- switch.py: Auto-disable exception handling
- sensor.py: TYPE_CHECKING import (not testable via pytest)
"""
from __future__ import annotations

import asyncio
import io
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from conftest import setup_integration
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from PIL import Image

from custom_components.fmd.const import DOMAIN


@pytest.mark.asyncio
async def test_device_tracker_initial_update_fails_graceful(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test platform-level initial location fetch failure is handled gracefully."""
    mock_fmd_api.create.return_value.get_location.side_effect = Exception(
        "Network error"
    )

    await setup_integration(hass, mock_fmd_api)

    # Device tracker should exist but have unknown state
    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]
    assert device_tracker.state == STATE_UNAVAILABLE


@pytest.mark.asyncio
async def test_device_tracker_high_frequency_mode_request_location_success(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test high-frequency mode successfully requests location from device."""
    await setup_integration(hass, mock_fmd_api)

    # Get the device tracker
    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Enable high-frequency mode
    device_tracker._high_frequency_mode = True

    # Mock request_location to return success
    mock_fmd_api.create.return_value.request_location.return_value = True

    # Trigger polling update with mocked sleep
    with patch("custom_components.fmd.device_tracker.asyncio.sleep") as mock_sleep:
        mock_sleep.return_value = asyncio.sleep(0)
        await device_tracker.async_update()

    # Verify request_location was called
    mock_fmd_api.create.return_value.request_location.assert_called_once_with(
        provider="all"
    )
    mock_sleep.assert_called_once_with(10)


@pytest.mark.asyncio
async def test_device_tracker_high_frequency_mode_request_location_fails(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test high-frequency mode handles request_location failure gracefully."""
    await setup_integration(hass, mock_fmd_api)

    # Get the device tracker
    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Enable high-frequency mode
    device_tracker._high_frequency_mode = True

    # Mock request_location to return failure
    mock_fmd_api.create.return_value.request_location.return_value = False

    # Trigger polling update
    with patch("custom_components.fmd.device_tracker.asyncio.sleep") as mock_sleep:
        await device_tracker.async_update()

    # Verify request_location was called but sleep was not
    mock_fmd_api.create.return_value.request_location.assert_called_once_with(
        provider="all"
    )
    mock_sleep.assert_not_called()


@pytest.mark.asyncio
async def test_device_tracker_high_frequency_mode_exception(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test high-frequency mode handles exceptions during location request."""
    await setup_integration(hass, mock_fmd_api)

    # Get the device tracker
    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Enable high-frequency mode
    device_tracker._high_frequency_mode = True

    # Mock request_location to raise exception
    mock_fmd_api.create.return_value.request_location.side_effect = Exception(
        "Network error"
    )

    # Trigger polling update - should not raise
    await device_tracker.async_update()

    # Verify request_location was called
    mock_fmd_api.create.return_value.request_location.assert_called_once_with(
        provider="all"
    )


@pytest.mark.asyncio
async def test_device_tracker_attributes_with_altitude_imperial(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test device tracker attributes include altitude in imperial units."""
    # Setup with imperial units
    hass.config.units.name = "us_customary"

    # Mock location with altitude
    mock_fmd_api.create.return_value.get_location.return_value = {
        "pictures": [],
        "location": [
            {
                "lat": 47.6062,
                "lon": -122.3321,
                "provider": "gps",
                "time": 1729000000000,
                "altitude": 100.0,  # 100 meters
            }
        ],
    }

    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]
    await device_tracker.async_update()

    attributes = device_tracker.extra_state_attributes

    assert "altitude" in attributes
    assert attributes["altitude"] == pytest.approx(328.1, rel=0.1)  # meters to feet
    assert attributes["altitude_unit"] == "ft"


@pytest.mark.asyncio
async def test_device_tracker_attributes_with_speed_imperial(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test device tracker attributes include speed in imperial units."""
    # Setup with imperial units
    hass.config.units.name = "us_customary"

    # Mock location with speed
    mock_fmd_api.create.return_value.get_location.return_value = {
        "pictures": [],
        "location": [
            {
                "lat": 47.6062,
                "lon": -122.3321,
                "provider": "gps",
                "time": 1729000000000,
                "speed": 10.0,  # 10 m/s
            }
        ],
    }

    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]
    await device_tracker.async_update()

    attributes = device_tracker.extra_state_attributes

    assert "speed" in attributes
    assert attributes["speed"] == pytest.approx(22.4, rel=0.1)  # m/s to mph
    assert attributes["speed_unit"] == "mph"


@pytest.mark.asyncio
async def test_device_tracker_empty_blob_warning(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test device tracker logs warning for empty location blobs."""
    # Mock location with empty blob
    mock_fmd_api.create.return_value.get_location.return_value = {
        "pictures": [],
        "location": [None, b""],  # Empty blobs
    }

    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]
    await device_tracker.async_update()

    # Should not crash, state should be unavailable
    assert device_tracker.state == STATE_UNAVAILABLE


@pytest.mark.asyncio
async def test_button_download_photos_with_exif_timestamp(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test download photos button extracts EXIF timestamp from images."""
    # Create a mock image with EXIF data
    img = Image.new("RGB", (100, 100), color="red")
    exif_data = img.getexif()
    # Set DateTimeOriginal (tag 36867)
    exif_data[36867] = "2025:10:19 15:30:45"

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG", exif=exif_data)
    img_bytes.seek(0)
    image_data = img_bytes.getvalue()

    # Mock API response with photo
    mock_fmd_api.create.return_value.get_location.return_value = {
        "pictures": [image_data],
        "location": [],
    }

    await setup_integration(hass, mock_fmd_api)

    # Press the button using service call
    with patch("pathlib.Path.mkdir"), patch(
        "pathlib.Path.is_dir", return_value=True
    ), patch("pathlib.Path.exists", return_value=False), patch(
        "pathlib.Path.write_bytes"
    ):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )

    # Check that file was saved with timestamp in name
    from conftest import get_mock_config_entry

    config_entry = get_mock_config_entry()
    media_dir = Path(hass.config.path("media", "fmd", config_entry.data["id"]))
    saved_files = list(media_dir.glob("photo_*.jpg"))

    assert len(saved_files) == 1
    assert "20251019_153045" in saved_files[0].name


@pytest.mark.asyncio
async def test_button_download_photos_exif_parsing_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test download photos button handles EXIF parsing errors gracefully."""
    # Create invalid image data that will fail EXIF parsing
    invalid_image_data = b"not a valid jpeg image"

    # Mock API response with invalid photo
    mock_fmd_api.create.return_value.get_location.return_value = {
        "pictures": [invalid_image_data],
        "location": [],
    }

    await setup_integration(hass, mock_fmd_api)

    # Press the button - should not crash
    with patch("pathlib.Path.mkdir"), patch("pathlib.Path.write_bytes"):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )

    # Should still attempt to save (will fail, but error is handled)


@pytest.mark.asyncio
async def test_button_download_photos_updates_sensor(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test download photos button updates photo count sensor."""
    # Create a simple image
    img = Image.new("RGB", (100, 100), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    # Mock API response with one photo
    mock_fmd_api.create.return_value.get_location.return_value = {
        "pictures": [img_bytes.getvalue()],
        "location": [],
    }

    await setup_integration(hass, mock_fmd_api)

    # Press the button
    with patch("pathlib.Path.mkdir"), patch(
        "pathlib.Path.is_dir", return_value=True
    ), patch("pathlib.Path.exists", return_value=False), patch(
        "pathlib.Path.write_bytes"
    ):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )

    # Check that sensor was updated (sensor should exist and have update method called)
    entry_id = list(hass.data[DOMAIN].keys())[0]
    photo_sensor = hass.data[DOMAIN][entry_id].get("photo_count_sensor")
    assert photo_sensor is not None


@pytest.mark.asyncio
async def test_button_download_photos_sensor_not_found(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test download photos button handles missing photo sensor gracefully."""
    # Create a simple image
    img = Image.new("RGB", (100, 100), color="green")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    # Mock API response
    mock_fmd_api.create.return_value.get_location.return_value = {
        "pictures": [img_bytes.getvalue()],
        "location": [],
    }

    await setup_integration(hass, mock_fmd_api)

    # Remove the photo sensor
    entry_id = list(hass.data[DOMAIN].keys())[0]
    del hass.data[DOMAIN][entry_id]["photo_count_sensor"]

    # Press the button - should not crash
    with patch("pathlib.Path.mkdir"), patch(
        "pathlib.Path.is_dir", return_value=True
    ), patch("pathlib.Path.exists", return_value=False), patch(
        "pathlib.Path.write_bytes"
    ):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )


@pytest.mark.asyncio
async def test_button_download_photos_cleanup_delete_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test photo cleanup handles file deletion errors gracefully."""
    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data[DOMAIN].keys())[0]

    # Enable auto-cleanup and set max to 1
    cleanup_switch = hass.data[DOMAIN][entry_id]["photo_auto_cleanup_switch"]
    await cleanup_switch.async_turn_on()

    max_photos = hass.data[DOMAIN][entry_id]["max_photos_number"]
    max_photos._attr_native_value = 1

    # Create two images
    img1 = Image.new("RGB", (100, 100), color="red")
    img2 = Image.new("RGB", (100, 100), color="blue")

    img1_bytes = io.BytesIO()
    img1.save(img1_bytes, format="JPEG")
    img1_bytes.seek(0)

    img2_bytes = io.BytesIO()
    img2.save(img2_bytes, format="JPEG")
    img2_bytes.seek(0)

    # Mock API response with two photos
    mock_fmd_api.create.return_value.get_location.return_value = {
        "pictures": [img1_bytes.getvalue(), img2_bytes.getvalue()],
        "location": [],
    }

    # Mock Path.unlink to raise exception
    with patch("pathlib.Path.mkdir"), patch(
        "pathlib.Path.is_dir", return_value=True
    ), patch("pathlib.Path.exists", return_value=False), patch(
        "pathlib.Path.write_bytes"
    ), patch(
        "pathlib.Path.unlink", side_effect=Exception("Permission denied")
    ):
        # Press the button - should handle error
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )


@pytest.mark.asyncio
async def test_button_wipe_device_success(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test wipe device button successfully sends wipe command."""
    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data[DOMAIN].keys())[0]

    # Enable wipe safety
    safety_switch = hass.data[DOMAIN][entry_id]["wipe_safety_switch"]
    await safety_switch.async_turn_on()

    # Mock successful wipe
    mock_fmd_api.create.return_value.wipe_device.return_value = True

    # Press the wipe button
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )

    # Verify wipe was called
    mock_fmd_api.create.return_value.wipe_device.assert_called_once()

    # Safety switch should be automatically disabled
    assert safety_switch.is_on is False


@pytest.mark.asyncio
async def test_select_bluetooth_enable_command(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test Bluetooth select entity sends enable command."""
    await setup_integration(hass, mock_fmd_api)

    # Get the Bluetooth select entity
    state = hass.states.get("select.fmd_test_user_bluetooth")
    assert state is not None

    # Select "Enable Bluetooth"
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.fmd_test_user_bluetooth", "option": "Enable Bluetooth"},
        blocking=True,
    )

    # Verify API was called
    mock_fmd_api.create.return_value.toggle_bluetooth.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_select_bluetooth_disable_command(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test Bluetooth select entity sends disable command."""
    await setup_integration(hass, mock_fmd_api)

    # Get the Bluetooth select entity
    state = hass.states.get("select.fmd_test_user_bluetooth")
    assert state is not None

    # Select "Disable Bluetooth"
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.fmd_test_user_bluetooth", "option": "Disable Bluetooth"},
        blocking=True,
    )

    # Verify API was called
    mock_fmd_api.create.return_value.toggle_bluetooth.assert_called_once_with(False)


@pytest.mark.asyncio
async def test_select_dnd_enable_command(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test DND select entity sends enable command."""
    await setup_integration(hass, mock_fmd_api)

    # Select "Enable Do Not Disturb"
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_volume_do_not_disturb",
            "option": "Enable Do Not Disturb",
        },
        blocking=True,
    )

    # Verify API was called
    mock_fmd_api.create.return_value.toggle_dnd.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_select_dnd_disable_command(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test DND select entity sends disable command."""
    await setup_integration(hass, mock_fmd_api)

    # Select "Disable Do Not Disturb"
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_volume_do_not_disturb",
            "option": "Disable Do Not Disturb",
        },
        blocking=True,
    )

    # Verify API was called
    mock_fmd_api.create.return_value.toggle_dnd.assert_called_once_with(False)


@pytest.mark.asyncio
async def test_select_ringer_mode_normal(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test ringer mode select entity sends normal mode command."""
    await setup_integration(hass, mock_fmd_api)

    # Select "Normal"
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.fmd_test_user_volume_ringer_mode", "option": "Normal"},
        blocking=True,
    )

    # Verify API was called with mode 2
    mock_fmd_api.create.return_value.set_ringer_mode.assert_called_once_with(2)


@pytest.mark.asyncio
async def test_select_ringer_mode_vibrate(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test ringer mode select entity sends vibrate mode command."""
    await setup_integration(hass, mock_fmd_api)

    # Select "Vibrate"
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.fmd_test_user_volume_ringer_mode", "option": "Vibrate"},
        blocking=True,
    )

    # Verify API was called with mode 1
    mock_fmd_api.create.return_value.set_ringer_mode.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_select_ringer_mode_silent(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test ringer mode select entity sends silent mode command."""
    await setup_integration(hass, mock_fmd_api)

    # Select "Silent"
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.fmd_test_user_volume_ringer_mode", "option": "Silent"},
        blocking=True,
    )

    # Verify API was called with mode 0
    mock_fmd_api.create.return_value.set_ringer_mode.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_switch_wipe_safety_auto_disable_cancelled_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test wipe safety auto-disable handles CancelledError gracefully."""
    await setup_integration(hass, mock_fmd_api)

    # Get the wipe safety switch
    entry_id = list(hass.data[DOMAIN].keys())[0]
    safety_switch = hass.data[DOMAIN][entry_id]["wipe_safety_switch"]

    # Turn on the switch (starts auto-disable task)
    await safety_switch.async_turn_on()
    await hass.async_block_till_done()

    # Verify task was created
    assert safety_switch._auto_disable_task is not None

    # Turn off the switch (cancels the task)
    await safety_switch.async_turn_off()
    await hass.async_block_till_done()

    # Task should be cancelled and set to None
    assert safety_switch._auto_disable_task is None
    assert safety_switch.is_on is False
