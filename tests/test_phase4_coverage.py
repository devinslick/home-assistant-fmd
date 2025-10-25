"""Phase 4 tests - Targeting 100% coverage for remaining gaps."""
from __future__ import annotations

from unittest.mock import AsyncMock

from conftest import setup_integration
from homeassistant.core import HomeAssistant


async def test_high_frequency_switch_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test high frequency switch when tracker not found in hass data."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id]["tracker"] = None

    # Turn off the switch (should log error but not crash)
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.fmd_test_user_high_frequency_mode"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should not raise an error


async def test_allow_inaccurate_switch_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test allow inaccurate switch when tracker not found in hass data."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id]["tracker"] = None

    # Turn off the switch (should log error but not crash)
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.fmd_test_user_location_allow_inaccurate_updates"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should not raise an error


async def test_wipe_safety_auto_disable_cancel(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe safety switch auto-disable cancellation."""
    await setup_integration(hass, mock_fmd_api)

    # Turn on the wipe safety switch
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

    # Turn it off before auto-disable (cancels the task)
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify it's off
    state = hass.states.get("switch.fmd_test_user_wipe_safety_switch")
    assert state.state == "off"


async def test_photo_cleanup_switch_turn_off(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo auto cleanup switch turn off."""
    await setup_integration(hass, mock_fmd_api)

    # Turn off the photo cleanup switch
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.fmd_test_user_photo_auto_cleanup"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify it's off
    state = hass.states.get("switch.fmd_test_user_photo_auto_cleanup")
    assert state.state == "off"


async def test_bluetooth_select_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test Bluetooth select when tracker not found in hass data."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id]["tracker"] = None

    # Try to select an option (should log error but not crash)
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_bluetooth_bluetooth_control",
            "option": "Enable Bluetooth",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should not raise an error


async def test_dnd_select_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test DND select when tracker not found in hass data."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id]["tracker"] = None

    # Try to select an option (should log error but not crash)
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_dnd_do_not_disturb_control",
            "option": "Enable Do Not Disturb",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should not raise an error


async def test_ringer_mode_select_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ringer mode select when tracker not found in hass data."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id]["tracker"] = None

    # Try to select an option (should log error but not crash)
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_ringer_ringer_mode_control",
            "option": "Silent",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should not raise an error
