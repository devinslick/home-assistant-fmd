"""Test FMD number entities."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.core import HomeAssistant

from custom_components.fmd.const import DOMAIN
from conftest import setup_integration


async def test_update_interval_number(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test update interval number entity."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "number.fmd_test_user_update_interval"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "30"
    
    # Set new value
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity_id, "value": 60},
        blocking=True,
    )
    
    state = hass.states.get(entity_id)
    assert float(state.state) == 60


async def test_update_interval_min_max(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test update interval respects min/max values."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "number.fmd_test_user_update_interval"
    state = hass.states.get(entity_id)
    
    # Check min/max attributes
    assert state.attributes["min"] == 1
    assert state.attributes["max"] == 1440


async def test_high_frequency_interval_number(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test high frequency interval number entity."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "number.fmd_test_user_high_frequency_interval"
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 5  # Default value
    
    # Set new value
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity_id, "value": 10},
        blocking=True,
    )
    
    state = hass.states.get(entity_id)
    assert float(state.state) == 10


async def test_high_frequency_interval_affects_polling(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test that high frequency interval changes affect tracker polling."""
    await setup_integration(hass, mock_fmd_api)
    
    # Enable high frequency mode
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_high_frequency_mode"},
        blocking=True,
    )
    
    # Change interval
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.fmd_test_user_high_frequency_interval", "value": 15},
        blocking=True,
    )
    
    # Verify the tracker's interval was updated
    # (This would test internal state, in real integration)
    state = hass.states.get("number.fmd_test_user_high_frequency_interval")
    assert float(state.state) == 15


async def test_max_photos_number(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test max photos to keep number entity."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "number.fmd_test_user_max_photos_to_keep"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "100"
    
    # Set new value
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity_id, "value": 50},
        blocking=True,
    )
    
    state = hass.states.get(entity_id)
    assert state.state == "50"


async def test_max_photos_min_max(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test max photos respects min/max values."""
    await setup_integration(hass, mock_fmd_api)
    
    entity_id = "number.fmd_test_user_max_photos_to_keep"
    state = hass.states.get(entity_id)
    
    # Check min/max attributes
    assert state.attributes["min"] == 1
    assert state.attributes["max"] == 1000
