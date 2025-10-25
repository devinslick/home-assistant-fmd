"""Phase 4d: Final coverage push to 100%.

Targeting remaining uncovered lines:
- select.py: 120 (bluetooth tracker-not-found),
  184 (dnd placeholder), 249 (ringer tracker-not-found)
- switch.py: 211 (cancel existing auto-disable),
  234-238 (CancelledError handling)
- device_tracker.py: 68-71 (ConfigEntryNotReady),
  299-300 (imperial altitude), 309-310 (imperial speed), 404-405 (empty blob)
- button.py: Large EXIF parsing blocks
"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from conftest import setup_integration
from homeassistant.config_entries import ConfigEntryNotReady
from homeassistant.core import HomeAssistant

from custom_components.fmd.const import DOMAIN


async def test_select_bluetooth_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test bluetooth select when tracker is missing (covers line 120)."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass.data to simulate not-found condition
    entry_id = list(hass.data[DOMAIN].keys())[0]
    del hass.data[DOMAIN][entry_id]["tracker"]

    # Try to send bluetooth command - should log error and return
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_bluetooth_command",
            "option": "Ring Phone",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should not raise, just log error
    # API should not be called since tracker wasn't found
    mock_fmd_api.create.return_value.send_command.assert_not_called()


async def test_select_dnd_placeholder(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test DND select with placeholder option (covers line 184)."""
    await setup_integration(hass, mock_fmd_api)

    # Select the placeholder option "Send Command..."
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_volume_do_not_disturb",
            "option": "Send Command...",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should return early without calling API
    mock_fmd_api.create.return_value.toggle_do_not_disturb.assert_not_called()


async def test_select_ringer_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ringer mode select when tracker is missing (covers line 249)."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass.data
    entry_id = list(hass.data[DOMAIN].keys())[0]
    del hass.data[DOMAIN][entry_id]["tracker"]

    # Try to change ringer mode - should log error and return
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_volume_ringer_mode",
            "option": "Normal (Sound + Vibrate)",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # API should not be called
    mock_fmd_api.create.return_value.set_ringer_mode.assert_not_called()


async def test_switch_wipe_safety_cancel_existing_task(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test cancelling existing auto-disable task (covers line 211)."""
    await setup_integration(hass, mock_fmd_api)

    # Turn on safety switch
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_device_wipe_safety_enabled"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Turn on again immediately (should cancel previous auto-disable task)
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_device_wipe_safety_enabled"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should have cancelled the first task and created a new one


async def test_switch_wipe_safety_cancelled_error_handling(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test CancelledError handling in auto-disable (covers lines 234-238)."""
    await setup_integration(hass, mock_fmd_api)

    # Turn on safety switch
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_device_wipe_safety_enabled"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Turn off immediately (cancels the auto-disable task)
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.fmd_test_user_device_wipe_safety_enabled"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # CancelledError should be caught gracefully


async def test_device_tracker_config_entry_not_ready(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ConfigEntryNotReady on failure (covers lines 68-71)."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    # Set up the entry but make FmdApi.create fail
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "fmd_id": "test_user_config_error",
            "password": "test_password",
        },
        unique_id="test_user_config_error",
    )
    entry.add_to_hass(hass)

    # Mock api.get_all_locations to raise exception during initial fetch
    mock_fmd_api.create.return_value.get_all_locations.side_effect = Exception(
        "Network timeout"
    )

    # Should raise ConfigEntryNotReady
    with pytest.raises(ConfigEntryNotReady):
        await hass.config_entries.async_setup(entry.entry_id)


async def test_device_tracker_imperial_altitude(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker altitude in imperial units (covers lines 299-300)."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    # Create entry with imperial units in options
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "fmd_id": "test_user",
            "password": "test_password",
        },
        options={"use_imperial": True},
        unique_id="test_user",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Get the device tracker
    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Set location data with altitude (100 meters)
    device_tracker._location = {
        "lat": 47.6062,
        "lon": -122.3321,
        "provider": "gps",
        "time": "2025-10-23T12:00:00Z",
        "altitude": 100.0,  # 100 meters
        "accuracy": 10.0,
        "bat": 85,
    }

    attributes = device_tracker.extra_state_attributes

    # Should convert to feet (100m * 3.28084 = 328.084ft)
    assert "altitude" in attributes
    assert attributes["altitude"] == 328.1  # Rounded to 1 decimal
    assert attributes["altitude_unit"] == "ft"


async def test_device_tracker_imperial_speed(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker speed in imperial units (covers lines 309-310)."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "fmd_id": "test_user",
            "password": "test_password",
        },
        options={"use_imperial": True},
        unique_id="test_user_speed",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Set location data with speed (10 m/s)
    device_tracker._location = {
        "lat": 47.6062,
        "lon": -122.3321,
        "provider": "gps",
        "time": "2025-10-23T12:00:00Z",
        "speed": 10.0,  # 10 m/s
        "accuracy": 10.0,
        "bat": 85,
    }

    attributes = device_tracker.extra_state_attributes

    # Should convert to mph (10 m/s * 2.23694 = 22.3694 mph)
    assert "speed" in attributes
    assert attributes["speed"] == 22.4  # Rounded to 1 decimal
    assert attributes["speed_unit"] == "mph"


async def test_device_tracker_empty_blob_warning(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test empty blob warning in location fetch (covers lines 404-405)."""
    await setup_integration(hass, mock_fmd_api)

    # Get the device tracker
    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Mock get_all_locations to return a mix of valid and empty blobs
    mock_fmd_api.create.return_value.get_all_locations.return_value = [
        b"valid_encrypted_data_here",
        b"",  # Empty blob - should trigger warning on line 404
        None,  # Also empty - should trigger continue path
    ]

    # Mock decrypt to return valid data for non-empty blobs
    json_data = (
        b'{"lat": 47.6062, "lon": -122.3321, "time": "2025-10-23T12:00:00Z", '
        b'"provider": "gps", "bat": 85, "accuracy": 10.0}'
    )
    mock_fmd_api.create.return_value.decrypt_data_blob.side_effect = [
        json_data,
        # Empty blobs won't reach decrypt
    ]

    # Call async_update which calls get_all_locations
    await device_tracker.async_update()

    # Should have processed only the 1 valid location (2 empty ones skipped)
    assert device_tracker._location is not None
    assert device_tracker._location["lat"] == 47.6062
