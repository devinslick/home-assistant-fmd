"""Phase 4b tests - Additional coverage for buttons, selects, and switches."""
from __future__ import annotations

from unittest.mock import AsyncMock

from conftest import setup_integration
from homeassistant.core import HomeAssistant


async def test_select_placeholder_option(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test select entities with placeholder option (no action)."""
    await setup_integration(hass, mock_fmd_api)

    # Select placeholder option for Bluetooth (should do nothing)
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_bluetooth_bluetooth_control",
            "option": "-- Select Command --",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Select placeholder option for DND (should do nothing)
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_dnd_do_not_disturb_control",
            "option": "-- Select Command --",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Select placeholder option for ringer mode (should do nothing)
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_ringer_ringer_mode_control",
            "option": "-- Select Command --",
        },
        blocking=True,
    )
    await hass.async_block_till_done()


async def test_button_ring_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ring button when tracker not found."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id]["tracker"] = None

    # Try to press ring button (should log error but not crash)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_volume_ring_device"},
        blocking=True,
    )
    await hass.async_block_till_done()


async def test_button_lock_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test lock button when tracker not found."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id]["tracker"] = None

    # Try to press lock button (should log error but not crash)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_lock_device"},
        blocking=True,
    )
    await hass.async_block_till_done()


async def test_button_capture_front_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test capture front button when tracker not found."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id]["tracker"] = None

    # Try to press capture front button (should log error but not crash)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_capture_front"},
        blocking=True,
    )
    await hass.async_block_till_done()


async def test_button_capture_rear_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test capture rear button when tracker not found."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id]["tracker"] = None

    # Try to press capture rear button (should log error but not crash)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_capture_rear"},
        blocking=True,
    )
    await hass.async_block_till_done()


async def test_button_ring_send_command_fails(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ring button when send_command returns False."""
    await setup_integration(hass, mock_fmd_api)

    # Make send_command return False
    api_instance = mock_fmd_api.create.return_value
    api_instance.send_command.reset_mock()
    api_instance.send_command.return_value = False

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_volume_ring_device"},
        blocking=True,
    )
    await hass.async_block_till_done()

    api_instance.send_command.assert_called_once_with("ring")


async def test_button_lock_device_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test lock button when device.lock() raises an exception."""
    await setup_integration(hass, mock_fmd_api)

    # Make device.lock() raise an exception
    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.lock.side_effect = Exception("Lock failed")

    # Press lock button - should handle error gracefully
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_lock_device"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify device.lock() was called
    device_mock.lock.assert_called_once_with(message=None)


async def test_button_capture_front_take_picture_fails(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test capture front button when take_picture returns False."""
    await setup_integration(hass, mock_fmd_api)

    # Make take_picture return False
    api_instance = mock_fmd_api.create.return_value
    api_instance.take_picture.reset_mock()
    api_instance.take_picture.return_value = False

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_capture_front"},
        blocking=True,
    )
    await hass.async_block_till_done()

    api_instance.take_picture.assert_called_once_with("front")


async def test_button_capture_rear_take_picture_fails(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test capture rear button when take_picture returns False."""
    await setup_integration(hass, mock_fmd_api)

    # Make take_picture return False
    api_instance = mock_fmd_api.create.return_value
    api_instance.take_picture.reset_mock()
    api_instance.take_picture.return_value = False

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_capture_rear"},
        blocking=True,
    )
    await hass.async_block_till_done()

    api_instance.take_picture.assert_called_once_with("back")


async def test_switch_wipe_safety_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe safety switch when tracker not found (for logging)."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id]["tracker"] = None

    # Turn on the wipe safety switch (should still work, just logs differently)
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify it's on
    state = hass.states.get("switch.fmd_test_user_wipe_safety_switch")
    assert state.state == "on"
