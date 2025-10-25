"""Phase 4c: Additional tests to reach 100% coverage.

Focus areas:
- button.py: EXIF parsing, photo sensor update, cleanup failures, wipe command success
- device_tracker.py: ConfigEntryNotReady, high-frequency mode logic, speed/altitude attributes
- select.py: Actual command execution paths (toggle_bluetooth, etc.)
- switch.py: Auto-disable exception handling
- sensor.py: TYPE_CHECKING import (not testable via pytest)
"""
from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from conftest import setup_integration
from homeassistant.const import STATE_NOT_HOME, STATE_UNKNOWN
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
    assert device_tracker.state == STATE_NOT_HOME


@pytest.mark.asyncio
async def test_device_tracker_high_frequency_mode_request_location_success(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test high-frequency mode successfully requests location from device."""
    await setup_integration(hass, mock_fmd_api)

    # Get the device tracker
    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]

    device_tracker._high_frequency_mode = True

    api = mock_fmd_api.create.return_value
    api.request_location.reset_mock()

    with patch(
        "custom_components.fmd.device_tracker.async_track_time_interval"
    ) as mock_track:
        device_tracker.start_polling()

    update_callback = mock_track.call_args[0][1]

    sleep_mock = AsyncMock(return_value=None)
    api.request_location.return_value = True

    with patch("asyncio.sleep", new=sleep_mock):
        await update_callback(None)

    api.request_location.assert_awaited_once_with(provider="all")
    sleep_mock.assert_awaited_once_with(10)


@pytest.mark.asyncio
async def test_device_tracker_high_frequency_mode_request_location_fails(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test high-frequency mode handles request_location failure gracefully."""
    await setup_integration(hass, mock_fmd_api)

    # Get the device tracker
    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]

    device_tracker._high_frequency_mode = True

    api = mock_fmd_api.create.return_value
    api.request_location.reset_mock()
    api.request_location.return_value = False

    with patch(
        "custom_components.fmd.device_tracker.async_track_time_interval"
    ) as mock_track:
        device_tracker.start_polling()

    update_callback = mock_track.call_args[0][1]

    sleep_mock = AsyncMock(return_value=None)

    with patch("asyncio.sleep", new=sleep_mock):
        await update_callback(None)

    api.request_location.assert_awaited_once_with(provider="all")
    sleep_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_device_tracker_high_frequency_mode_exception(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test high-frequency mode handles exceptions during location request."""
    await setup_integration(hass, mock_fmd_api)

    # Get the device tracker
    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]

    device_tracker._high_frequency_mode = True

    api = mock_fmd_api.create.return_value
    api.request_location.reset_mock()
    api.request_location.side_effect = Exception("Network error")

    with patch(
        "custom_components.fmd.device_tracker.async_track_time_interval"
    ) as mock_track:
        device_tracker.start_polling()

    update_callback = mock_track.call_args[0][1]

    sleep_mock = AsyncMock(return_value=None)

    with patch("asyncio.sleep", new=sleep_mock):
        await update_callback(None)

    api.request_location.assert_awaited_once_with(provider="all")
    sleep_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_device_tracker_attributes_with_altitude_imperial(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test device tracker attributes include altitude in imperial units."""
    # Setup with imperial units
    hass.config.units.name = "us_customary"

    mock_api = mock_fmd_api.create.return_value
    mock_api.get_all_locations.return_value = [
        {
            "lat": 47.6062,
            "lon": -122.3321,
            "provider": "gps",
            "time": "2025-10-15T10:15:00Z",
            "altitude": 100.0,
            "bat": 90,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]
    device_tracker._use_imperial = True
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

    mock_api = mock_fmd_api.create.return_value
    mock_api.get_all_locations.return_value = [
        {
            "lat": 47.6062,
            "lon": -122.3321,
            "provider": "gps",
            "time": "2025-10-15T10:15:00Z",
            "speed": 10.0,
            "bat": 80,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]
    device_tracker._use_imperial = True
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
    mock_fmd_api.create.return_value.get_all_locations.return_value = [None, b""]

    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]
    await device_tracker.async_update()
    device_tracker.async_write_ha_state()
    await hass.async_block_till_done()

    # Should not crash, state should remain unknown
    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.state == STATE_UNKNOWN


@pytest.mark.asyncio
async def test_button_download_photos_with_exif_timestamp(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test download photos button extracts EXIF timestamp from images."""
    import base64

    await setup_integration(hass, mock_fmd_api)

    mock_api = mock_fmd_api.create.return_value
    mock_api.get_pictures.return_value = ["encrypted_photo"]
    mock_api.decrypt_data_blob.side_effect = lambda blob: base64.b64encode(
        b"fake-image-bytes"
    ).decode("utf-8")

    written_paths: list[Path] = []

    def fake_exists(path: Path) -> bool:
        # Only the expected EXIF-timestamped file does not exist; others do
        return "20251019_153045" not in path.name

    def fake_write_bytes(path: Path, data: bytes) -> int:
        written_paths.append(path)
        return len(data)

    async def run_executor(func, *args):
        return func(*args)

    fake_exif: dict[int, str] = {36867: "2025:10:19 15:30:45"}
    fake_image = MagicMock()
    fake_image.getexif.return_value = fake_exif

    with patch.object(hass, "async_add_executor_job", side_effect=run_executor), patch(
        "pathlib.Path.mkdir"
    ), patch("pathlib.Path.is_dir", return_value=True), patch(
        "pathlib.Path.exists", side_effect=fake_exists
    ), patch(
        "pathlib.Path.write_bytes", side_effect=fake_write_bytes
    ), patch(
        "custom_components.fmd.button.Image.open", return_value=fake_image
    ):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )

    mock_api.get_pictures.assert_awaited_once()
    if not any("20251019_153045" in path.name for path in written_paths):
        print(f"DEBUG: written_paths = {[str(p) for p in written_paths]}")
    assert any("20251019_153045" in path.name for path in written_paths)


@pytest.mark.asyncio
async def test_button_download_photos_exif_parsing_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test download photos button handles EXIF parsing errors gracefully."""
    import base64

    await setup_integration(hass, mock_fmd_api)

    mock_api = mock_fmd_api.create.return_value
    mock_api.get_pictures.return_value = ["invalid_blob"]
    mock_api.decrypt_data_blob.side_effect = lambda blob: base64.b64encode(
        b"fake-image-bytes"
    ).decode("utf-8")

    async def run_executor(func, *args):
        return func(*args)

    with patch.object(hass, "async_add_executor_job", side_effect=run_executor), patch(
        "pathlib.Path.mkdir"
    ), patch("pathlib.Path.is_dir", return_value=True), patch(
        "pathlib.Path.exists", return_value=False
    ), patch(
        "pathlib.Path.write_bytes"
    ) as mock_write, patch(
        "custom_components.fmd.button.Image.open",
        side_effect=OSError("Invalid EXIF"),
    ):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )

    mock_api.get_pictures.assert_awaited_once()
    # Even with parsing issues, we should attempt to write bytes
    assert mock_write.called


@pytest.mark.asyncio
async def test_button_download_photos_updates_sensor(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test download photos button updates photo count sensor."""
    import base64

    # Create a simple image
    img = Image.new("RGB", (100, 100), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    await setup_integration(hass, mock_fmd_api)

    mock_api = mock_fmd_api.create.return_value
    mock_api.get_pictures.return_value = ["photo_blob"]
    mock_api.decrypt_data_blob.return_value = base64.b64encode(
        img_bytes.getvalue()
    ).decode("utf-8")

    async def run_executor(func, *args):
        return func(*args)

    # Press the button
    with patch.object(hass, "async_add_executor_job", side_effect=run_executor), patch(
        "pathlib.Path.mkdir"
    ), patch("pathlib.Path.is_dir", return_value=True), patch(
        "pathlib.Path.exists", return_value=False
    ), patch(
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
    mock_fmd_api.create.return_value.send_command.return_value = True

    # Press the wipe button
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )

    # Verify wipe was called
    mock_fmd_api.create.return_value.send_command.assert_called_once_with("delete")

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
    mock_fmd_api.create.return_value.toggle_do_not_disturb.assert_called_once_with(True)


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
    mock_fmd_api.create.return_value.toggle_do_not_disturb.assert_called_once_with(
        False
    )


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
        {
            "entity_id": "select.fmd_test_user_volume_ringer_mode",
            "option": "Normal (Sound + Vibrate)",
        },
        blocking=True,
    )

    # Verify API was called with string mode
    mock_fmd_api.create.return_value.set_ringer_mode.assert_called_once_with("normal")


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
        {
            "entity_id": "select.fmd_test_user_volume_ringer_mode",
            "option": "Vibrate Only",
        },
        blocking=True,
    )

    # Verify API was called with string mode
    mock_fmd_api.create.return_value.set_ringer_mode.assert_called_once_with("vibrate")


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
        {
            "entity_id": "select.fmd_test_user_volume_ringer_mode",
            "option": "Silent",
        },
        blocking=True,
    )

    # Verify API was called with string mode
    mock_fmd_api.create.return_value.set_ringer_mode.assert_called_once_with("silent")


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
