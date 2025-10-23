"""Test FMD select entities."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.core import HomeAssistant

from custom_components.fmd.const import DOMAIN


async def test_location_source_select(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test location source select."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "select.fmd_test_user_location_source"
    state = hass.states.get(entity_id)
    assert state is not None
    
    # Select GPS
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "GPS"},
        blocking=True,
    )
    
    state = hass.states.get(entity_id)
    assert state.state == "GPS"


async def test_location_source_placeholder_reset(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test location source resets to placeholder after API call."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "select.fmd_test_user_location_source"
    
    # Select GPS
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "GPS"},
        blocking=True,
    )
    
    # Should trigger location request
    mock_fmd_api.create.return_value.request_location.assert_called()
    
    # After API call, should reset to placeholder
    state = hass.states.get(entity_id)
    assert state.state == "Location Source"


async def test_bluetooth_select(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test bluetooth control select."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "select.fmd_test_user_bluetooth_control"
    state = hass.states.get(entity_id)
    assert state is not None
    
    # Enable Bluetooth
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "Enable"},
        blocking=True,
    )
    
    mock_fmd_api.create.return_value.toggle_bluetooth.assert_called_once_with(True)


async def test_dnd_select(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test do not disturb control select."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "select.fmd_test_user_do_not_disturb_control"
    state = hass.states.get(entity_id)
    assert state is not None
    
    # Enable DND
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "Enable"},
        blocking=True,
    )
    
    mock_fmd_api.create.return_value.toggle_do_not_disturb.assert_called_once_with(True)


async def test_ringer_mode_select(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ringer mode control select."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "select.fmd_test_user_ringer_mode_control"
    state = hass.states.get(entity_id)
    assert state is not None
    
    # Set to Silent
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "Silent"},
        blocking=True,
    )
    
    mock_fmd_api.create.return_value.set_ringer_mode.assert_called_once_with("silent")


async def test_ringer_mode_vibrate(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ringer mode set to vibrate."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "select.fmd_test_user_ringer_mode_control"
    
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "Vibrate"},
        blocking=True,
    )
    
    mock_fmd_api.create.return_value.set_ringer_mode.assert_called_once_with("vibrate")


async def test_ringer_mode_normal(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ringer mode set to normal."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "select.fmd_test_user_ringer_mode_control"
    
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "Normal"},
        blocking=True,
    )
    
    mock_fmd_api.create.return_value.set_ringer_mode.assert_called_once_with("normal")


def get_mock_config_entry():
    """Create a mock config entry."""
    from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_ID
    
    return MockConfigEntry(
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
        source="user",
        entry_id="test_entry_id",
        unique_id="test_user",
        options={},
        discovery_keys={},
    )


async def setup_integration(hass: HomeAssistant, mock_fmd_api: AsyncMock) -> None:
    """Set up integration for testing."""
    config_entry = get_mock_config_entry()
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.fmd.__init__.FmdApi", mock_fmd_api):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
