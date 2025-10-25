"""Phase 4 tests - Targeting 100% coverage for remaining gaps."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from conftest import setup_integration
from homeassistant.config_entries import ConfigEntryNotReady
from homeassistant.core import HomeAssistant


async def test_device_tracker_initial_fetch_fails(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device_tracker setup when initial location fetch fails."""
    # Make get_all_locations raise an exception
    mock_fmd_api.create.return_value.get_all_locations.side_effect = Exception(
        "Network error"
    )

    from homeassistant.const import CONF_ID, CONF_PASSWORD, CONF_URL

    from custom_components.fmd.const import DOMAIN

    mock_config_entry = pytest.importorskip(
        "pytest_homeassistant_custom_component.common"
    ).MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="test_user",
        data={
            CONF_URL: "https://fmd.example.com",
            CONF_ID: "test_user",
            CONF_PASSWORD: "test_password",
            "polling_interval": 30,
            "allow_inaccurate_locations": False,
            "use_imperial": False,
        },
        entry_id="test_entry_id",
        unique_id="test_user",
    )
    mock_config_entry.add_to_hass(hass)

    # Mock async_add_executor_job
    async def mock_executor_job(func, *args):
        return func(*args)

    with patch.object(hass, "async_add_executor_job", side_effect=mock_executor_job):
        # Should raise ConfigEntryNotReady
        with pytest.raises(ConfigEntryNotReady):
            await hass.config_entries.async_setup(mock_config_entry.entry_id)


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
        {"entity_id": "switch.fmd_test_user_location_update_high_frequency_mode"},
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
        {"entity_id": "switch.fmd_test_user_location_filter_allow_inaccurate"},
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
        {"entity_id": "switch.fmd_test_user_wipe_safety_wipe_safety"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify it's on
    state = hass.states.get("switch.fmd_test_user_wipe_safety_wipe_safety")
    assert state.state == "on"

    # Turn it off before auto-disable (cancels the task)
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.fmd_test_user_wipe_safety_wipe_safety"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify it's off
    state = hass.states.get("switch.fmd_test_user_wipe_safety_wipe_safety")
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
        {"entity_id": "switch.fmd_test_user_photo_photo_auto_cleanup"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify it's off
    state = hass.states.get("switch.fmd_test_user_photo_photo_auto_cleanup")
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
