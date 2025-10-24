"""Test FMD switch entities."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF

from custom_components.fmd.const import DOMAIN
from conftest import setup_integration


async def test_high_frequency_mode_switch(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test high frequency mode switch."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "switch.fmd_test_user_high_frequency_mode"
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF
    
    # Turn on
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )
    
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    
    # Turn off
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": entity_id},
        blocking=True,
    )
    
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF


async def test_allow_inaccurate_switch(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test allow inaccurate locations switch."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "switch.fmd_test_user_location_allow_inaccurate_updates"
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF
    
    # Turn on
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )
    
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON


async def test_photo_auto_cleanup_switch(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo auto-cleanup switch."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "switch.fmd_test_user_photo_auto_cleanup"
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF
    
    # Turn on
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )
    
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON


async def test_wipe_safety_switch(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe safety switch."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "switch.fmd_test_user_wipe_safety_switch"
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF
    
    # Turn on
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )
    
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    
    # Turn off manually
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": entity_id},
        blocking=True,
    )
    
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF


async def test_wipe_safety_auto_timeout(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe safety switch auto-timeout after wipe."""
    await setup_integration(hass, mock_fmd_api)
    
    # Enable safety switch
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    
    # Wipe device
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    # Safety switch should turn off after wipe
    state = hass.states.get("switch.fmd_test_user_wipe_safety_switch")
    assert state.state == STATE_OFF
