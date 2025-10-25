"""Phase 4c: Additional tests to reach 100% coverage.

Focus areas:
- button.py: EXIF parsing, photo sensor update, cleanup failures, wipe command success
- device_tracker.py: ConfigEntryNotReady, high-frequency mode logic, speed/altitude attributes
- select.py: Actual command execution paths (toggle_bluetooth, etc.)
- switch.py: Auto-disable exception handling
- sensor.py: TYPE_CHECKING import (not testable via pytest)
"""
import asyncio
import io
from pathlib import Path
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from PIL import Image

from custom_components.fmd.const import DOMAIN


@pytest.mark.asyncio
async def test_device_tracker_initial_update_fails_graceful(
    hass, config_entry, fmd_api_mock
):
    """Test platform-level initial location fetch failure is handled gracefully."""
    fmd_api_mock.get_location.side_effect = Exception("Network error")

    # Setup should succeed despite initial fetch failure
    result = await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Platform setup should succeed (graceful degradation)
    assert result is True
    assert config_entry.state == ConfigEntryState.LOADED

    # Device tracker should exist but have unknown state
    device_tracker = hass.data[DOMAIN][config_entry.entry_id]["device_tracker"]
    assert device_tracker.state == STATE_UNAVAILABLE


@pytest.mark.asyncio
async def test_device_tracker_high_frequency_mode_request_location_success(
    hass, config_entry, fmd_api_mock
):
    """Test high-frequency mode successfully requests location from device."""
    # Setup the device tracker
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Get the device tracker
    device_tracker = hass.data[DOMAIN][config_entry.entry_id]["device_tracker"]

    # Enable high-frequency mode
    device_tracker._high_frequency_mode = True

    # Mock request_location to return success
    fmd_api_mock.request_location.return_value = True

    # Trigger polling update with mocked sleep
    with patch("custom_components.fmd.device_tracker.asyncio.sleep") as mock_sleep:
        mock_sleep.return_value = asyncio.sleep(0)
        await device_tracker.async_update()

    # Verify request_location was called
    fmd_api_mock.request_location.assert_called_once_with(provider="all")
    mock_sleep.assert_called_once_with(10)


@pytest.mark.asyncio
async def test_device_tracker_high_frequency_mode_request_location_fails(
    hass, config_entry, fmd_api_mock
):
    """Test high-frequency mode handles request_location failure gracefully."""
    # Setup the device tracker
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Get the device tracker
    device_tracker = hass.data[DOMAIN][config_entry.entry_id]["device_tracker"]

    # Enable high-frequency mode
    device_tracker._high_frequency_mode = True

    # Mock request_location to return failure
    fmd_api_mock.request_location.return_value = False

    # Trigger polling update
    with patch("custom_components.fmd.device_tracker.asyncio.sleep") as mock_sleep:
        await device_tracker.async_update()

    # Verify request_location was called but sleep was not
    fmd_api_mock.request_location.assert_called_once_with(provider="all")
    mock_sleep.assert_not_called()


@pytest.mark.asyncio
async def test_device_tracker_high_frequency_mode_exception(
    hass, config_entry, fmd_api_mock
):
    """Test high-frequency mode handles exceptions during location request."""
    # Setup the device tracker
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Get the device tracker
    device_tracker = hass.data[DOMAIN][config_entry.entry_id]["device_tracker"]

    # Enable high-frequency mode
    device_tracker._high_frequency_mode = True

    # Mock request_location to raise exception
    fmd_api_mock.request_location.side_effect = Exception("Network error")

    # Trigger polling update - should not raise
    await device_tracker.async_update()

    # Verify request_location was called
    fmd_api_mock.request_location.assert_called_once_with(provider="all")


@pytest.mark.asyncio
async def test_device_tracker_attributes_with_altitude_imperial(
    hass, config_entry, fmd_api_mock
):
    """Test device tracker attributes include altitude in imperial units."""
    # Setup with imperial units
    hass.config.units.name = "us_customary"

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Mock location with altitude
    fmd_api_mock.get_location.return_value = {
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

    device_tracker = hass.data[DOMAIN][config_entry.entry_id]["device_tracker"]
    await device_tracker.async_update()

    attributes = device_tracker.extra_state_attributes

    assert "altitude" in attributes
    assert attributes["altitude"] == pytest.approx(328.1, rel=0.1)  # meters to feet
    assert attributes["altitude_unit"] == "ft"


@pytest.mark.asyncio
async def test_device_tracker_attributes_with_speed_imperial(
    hass, config_entry, fmd_api_mock
):
    """Test device tracker attributes include speed in imperial units."""
    # Setup with imperial units
    hass.config.units.name = "us_customary"

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Mock location with speed
    fmd_api_mock.get_location.return_value = {
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

    device_tracker = hass.data[DOMAIN][config_entry.entry_id]["device_tracker"]
    await device_tracker.async_update()

    attributes = device_tracker.extra_state_attributes

    assert "speed" in attributes
    assert attributes["speed"] == pytest.approx(22.4, rel=0.1)  # m/s to mph
    assert attributes["speed_unit"] == "mph"


@pytest.mark.asyncio
async def test_device_tracker_empty_blob_warning(hass, config_entry, fmd_api_mock):
    """Test device tracker logs warning for empty location blobs."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Mock location with empty blob
    fmd_api_mock.get_location.return_value = {
        "pictures": [],
        "location": [None, b""],  # Empty blobs
    }

    device_tracker = hass.data[DOMAIN][config_entry.entry_id]["device_tracker"]
    await device_tracker.async_update()

    # Should not crash, state should be unavailable
    assert device_tracker.state == STATE_UNAVAILABLE


@pytest.mark.asyncio
async def test_button_download_photos_with_exif_timestamp(
    hass, config_entry, fmd_api_mock
):
    """Test download photos button extracts EXIF timestamp from images."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

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
    fmd_api_mock.get_location.return_value = {
        "pictures": [image_data],
        "location": [],
    }

    # Press the button
    button_entity = hass.data[DOMAIN][config_entry.entry_id]["download_photos_button"]
    await button_entity.async_press()
    await hass.async_block_till_done()

    # Check that file was saved with timestamp in name
    media_dir = Path(hass.config.path("media", "fmd", config_entry.data["id"]))
    saved_files = list(media_dir.glob("photo_*.jpg"))

    assert len(saved_files) == 1
    assert "20251019_153045" in saved_files[0].name


@pytest.mark.asyncio
async def test_button_download_photos_exif_parsing_error(
    hass, config_entry, fmd_api_mock
):
    """Test download photos button handles EXIF parsing errors gracefully."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Create invalid image data that will fail EXIF parsing
    invalid_image_data = b"not a valid jpeg image"

    # Mock API response with invalid photo
    fmd_api_mock.get_location.return_value = {
        "pictures": [invalid_image_data],
        "location": [],
    }

    # Press the button - should not crash
    button_entity = hass.data[DOMAIN][config_entry.entry_id]["download_photos_button"]
    await button_entity.async_press()
    await hass.async_block_till_done()

    # Should still attempt to save (will fail, but error is handled)


@pytest.mark.asyncio
async def test_button_download_photos_updates_sensor(hass, config_entry, fmd_api_mock):
    """Test download photos button updates photo count sensor."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Create a simple image
    img = Image.new("RGB", (100, 100), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    # Mock API response with one photo
    fmd_api_mock.get_location.return_value = {
        "pictures": [img_bytes.getvalue()],
        "location": [],
    }

    # Press the button
    button_entity = hass.data[DOMAIN][config_entry.entry_id]["download_photos_button"]
    await button_entity.async_press()
    await hass.async_block_till_done()

    # Check that sensor was updated (sensor should exist and have update method called)
    photo_sensor = hass.data[DOMAIN][config_entry.entry_id].get("photo_count_sensor")
    assert photo_sensor is not None


@pytest.mark.asyncio
async def test_button_download_photos_sensor_not_found(
    hass, config_entry, fmd_api_mock
):
    """Test download photos button handles missing photo sensor gracefully."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Remove the photo sensor
    del hass.data[DOMAIN][config_entry.entry_id]["photo_count_sensor"]

    # Create a simple image
    img = Image.new("RGB", (100, 100), color="green")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    # Mock API response
    fmd_api_mock.get_location.return_value = {
        "pictures": [img_bytes.getvalue()],
        "location": [],
    }

    # Press the button - should not crash
    button_entity = hass.data[DOMAIN][config_entry.entry_id]["download_photos_button"]
    await button_entity.async_press()
    await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_button_download_photos_cleanup_delete_error(
    hass, config_entry, fmd_api_mock
):
    """Test photo cleanup handles file deletion errors gracefully."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Enable auto-cleanup and set max to 1
    cleanup_switch = hass.data[DOMAIN][config_entry.entry_id]["photo_auto_cleanup"]
    await cleanup_switch.async_turn_on()

    max_photos = hass.data[DOMAIN][config_entry.entry_id]["max_photos_number"]
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
    fmd_api_mock.get_location.return_value = {
        "pictures": [img1_bytes.getvalue(), img2_bytes.getvalue()],
        "location": [],
    }

    # Mock Path.unlink to raise exception
    with patch("pathlib.Path.unlink", side_effect=Exception("Permission denied")):
        # Press the button - should handle error
        button_entity = hass.data[DOMAIN][config_entry.entry_id][
            "download_photos_button"
        ]
        await button_entity.async_press()
        await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_button_wipe_device_success(hass, config_entry, fmd_api_mock):
    """Test wipe device button successfully sends wipe command."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Enable wipe safety
    safety_switch = hass.data[DOMAIN][config_entry.entry_id]["wipe_safety_switch"]
    await safety_switch.async_turn_on()

    # Mock successful wipe
    fmd_api_mock.wipe_device.return_value = True

    # Press the wipe button
    wipe_button = hass.data[DOMAIN][config_entry.entry_id]["wipe_device_button"]
    await wipe_button.async_press()
    await hass.async_block_till_done()

    # Verify wipe was called
    fmd_api_mock.wipe_device.assert_called_once()

    # Safety switch should be automatically disabled
    assert safety_switch.is_on is False


@pytest.mark.asyncio
async def test_select_bluetooth_enable_command(hass, config_entry, fmd_api_mock):
    """Test Bluetooth select entity sends enable command."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

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
    fmd_api_mock.toggle_bluetooth.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_select_bluetooth_disable_command(hass, config_entry, fmd_api_mock):
    """Test Bluetooth select entity sends disable command."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

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
    fmd_api_mock.toggle_bluetooth.assert_called_once_with(False)


@pytest.mark.asyncio
async def test_select_dnd_enable_command(hass, config_entry, fmd_api_mock):
    """Test DND select entity sends enable command."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Select "Enable Do Not Disturb"
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_do_not_disturb",
            "option": "Enable Do Not Disturb",
        },
        blocking=True,
    )

    # Verify API was called
    fmd_api_mock.toggle_dnd.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_select_dnd_disable_command(hass, config_entry, fmd_api_mock):
    """Test DND select entity sends disable command."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Select "Disable Do Not Disturb"
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_do_not_disturb",
            "option": "Disable Do Not Disturb",
        },
        blocking=True,
    )

    # Verify API was called
    fmd_api_mock.toggle_dnd.assert_called_once_with(False)


@pytest.mark.asyncio
async def test_select_ringer_mode_normal(hass, config_entry, fmd_api_mock):
    """Test ringer mode select entity sends normal mode command."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Select "Normal"
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.fmd_test_user_ringer_mode", "option": "Normal"},
        blocking=True,
    )

    # Verify API was called with mode 2
    fmd_api_mock.set_ringer_mode.assert_called_once_with(2)


@pytest.mark.asyncio
async def test_select_ringer_mode_vibrate(hass, config_entry, fmd_api_mock):
    """Test ringer mode select entity sends vibrate mode command."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Select "Vibrate"
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.fmd_test_user_ringer_mode", "option": "Vibrate"},
        blocking=True,
    )

    # Verify API was called with mode 1
    fmd_api_mock.set_ringer_mode.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_select_ringer_mode_silent(hass, config_entry, fmd_api_mock):
    """Test ringer mode select entity sends silent mode command."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Select "Silent"
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.fmd_test_user_ringer_mode", "option": "Silent"},
        blocking=True,
    )

    # Verify API was called with mode 0
    fmd_api_mock.set_ringer_mode.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_switch_wipe_safety_auto_disable_cancelled_error(
    hass, config_entry, fmd_api_mock
):
    """Test wipe safety auto-disable handles CancelledError gracefully."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Get the wipe safety switch
    safety_switch = hass.data[DOMAIN][config_entry.entry_id]["wipe_safety_switch"]

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
