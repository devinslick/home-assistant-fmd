"""Phase 4c: Final tests targeting specific uncovered lines.

Targeting:
- select.py: Lines 66-72 (bluetooth enable), 120/132-134 (dnd enable),
  184/196-198 (ringer normal), 249 (ringer vibrate)
- switch.py: Lines 211, 234-238 (auto-disable exception handling)
- device_tracker.py: Lines 299-300 (altitude), 309-310 (speed)
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from conftest import setup_integration
from homeassistant.core import HomeAssistant

from custom_components.fmd.const import DOMAIN


async def test_select_bluetooth_enable(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test Bluetooth select sends enable command (covers lines 66-72)."""
    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.fmd_test_user_bluetooth", "option": "Enable Bluetooth"},
        blocking=True,
    )

    mock_fmd_api.create.return_value.toggle_bluetooth.assert_called_once_with(True)


async def test_select_bluetooth_disable(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test Bluetooth select sends disable command."""
    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.fmd_test_user_bluetooth", "option": "Disable Bluetooth"},
        blocking=True,
    )

    mock_fmd_api.create.return_value.toggle_bluetooth.assert_called_once_with(False)


async def test_select_dnd_enable(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test DND select sends enable command (covers lines 120, 132-134)."""
    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_do_not_disturb",
            "option": "Enable Do Not Disturb",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Assert on the mocked API instance
    mock_fmd_api.create.return_value.toggle_do_not_disturb.assert_called_once_with(True)


async def test_select_dnd_disable(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test DND select sends disable command."""
    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_do_not_disturb",
            "option": "Disable Do Not Disturb",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Assert on the mocked API instance
    mock_fmd_api.create.return_value.toggle_do_not_disturb.assert_called_once_with(
        False
    )


async def test_select_ringer_mode_normal(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ringer mode normal command (covers lines 184, 196-198)."""
    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_ringer_mode",
            "option": "Normal (Sound + Vibrate)",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Assert on the mocked API instance - API expects string "normal"
    mock_fmd_api.create.return_value.set_ringer_mode.assert_called_once_with("normal")


async def test_select_ringer_mode_vibrate(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ringer mode vibrate command (covers line 249)."""
    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_ringer_mode",
            "option": "Vibrate Only",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Assert on the mocked API instance - API expects string "vibrate"
    mock_fmd_api.create.return_value.set_ringer_mode.assert_called_once_with("vibrate")


async def test_select_ringer_mode_silent(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ringer mode silent command."""
    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.fmd_test_user_ringer_mode", "option": "Silent"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Assert on the mocked API instance - API expects string "silent"
    mock_fmd_api.create.return_value.set_ringer_mode.assert_called_once_with("silent")


async def test_switch_wipe_safety_auto_disable_task_cancellation(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe safety auto-disable task cancellation (covers lines 211, 234-238)."""
    await setup_integration(hass, mock_fmd_api)

    # Turn on the wipe safety (starts auto-disable task)
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )

    # Get the switch entity
    entry_id = list(hass.data[DOMAIN].keys())[0]
    safety_switch = hass.data[DOMAIN][entry_id]["wipe_safety_switch"]

    # Verify task was created
    assert safety_switch._auto_disable_task is not None

    # Turn off the switch (cancels the task - this hits the except CancelledError block)
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )

    # Task should be cancelled and set to None
    assert safety_switch._auto_disable_task is None
    assert safety_switch.is_on is False


async def test_device_tracker_altitude_attribute_metric(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker includes altitude attribute (covers lines 299-300)."""
    await setup_integration(hass, mock_fmd_api)

    # Get the device tracker (stored as "tracker" not "device_tracker")
    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Set location data with altitude
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

    assert "altitude" in attributes
    assert attributes["altitude"] == 100.0
    assert attributes["altitude_unit"] == "m"


async def test_device_tracker_speed_attribute_metric(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker includes speed attribute (covers lines 309-310)."""
    await setup_integration(hass, mock_fmd_api)

    # Get the device tracker (stored as "tracker" not "device_tracker")
    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Set location data with speed
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

    assert "speed" in attributes
    assert attributes["speed"] == 10.0
    assert attributes["speed_unit"] == "m/s"


async def test_device_tracker_high_frequency_mode_request_success(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test high-frequency mode requests location (covers lines 131-153)."""
    await setup_integration(hass, mock_fmd_api)

    # Get the device tracker (stored as "tracker" not "device_tracker")
    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Enable high-frequency mode
    device_tracker._high_frequency_mode = True

    # Mock successful location request
    mock_fmd_api.create.return_value.request_location.return_value = True

    # Mock asyncio.sleep to avoid waiting (patch asyncio.sleep directly)
    with patch("asyncio.sleep", return_value=asyncio.sleep(0)):
        await device_tracker.async_update()

    # Verify request_location was called with "all" provider
    mock_fmd_api.create.return_value.request_location.assert_called_with(provider="all")


async def test_device_tracker_high_frequency_mode_request_fails(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test high-frequency mode handles request failure."""
    await setup_integration(hass, mock_fmd_api)

    # Get the device tracker (stored as "tracker" not "device_tracker")
    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Enable high-frequency mode
    device_tracker._high_frequency_mode = True

    # Mock failed location request
    mock_fmd_api.create.return_value.request_location.return_value = False

    # Should not wait/sleep if request failed
    await device_tracker.async_update()

    # Verify request_location was called
    mock_fmd_api.create.return_value.request_location.assert_called_with(provider="all")


async def test_device_tracker_high_frequency_mode_exception(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test high-frequency mode handles exceptions gracefully."""
    await setup_integration(hass, mock_fmd_api)

    # Get the device tracker (stored as "tracker" not "device_tracker")
    entry_id = list(hass.data[DOMAIN].keys())[0]
    device_tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Enable high-frequency mode
    device_tracker._high_frequency_mode = True

    # Mock request_location to raise exception
    mock_fmd_api.create.return_value.request_location.side_effect = Exception(
        "Network error"
    )

    # Should not raise - just log error
    await device_tracker.async_update()

    # Verify request_location was attempted
    mock_fmd_api.create.return_value.request_location.assert_called_with(provider="all")
