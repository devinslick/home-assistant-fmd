"""Test FMD select entities."""
from __future__ import annotations

from unittest.mock import AsyncMock

from conftest import setup_integration
from homeassistant.core import HomeAssistant


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
        {"entity_id": entity_id, "option": "GPS Only (Accurate)"},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state.state == "GPS Only (Accurate)"


async def test_location_source_placeholder_reset(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test location source select changes option."""
    await setup_integration(hass, mock_fmd_api)

    entity_id = "select.fmd_test_user_location_source"

    # Initially should be default
    state = hass.states.get(entity_id)
    assert state.state == "All Providers (Default)"

    # Select GPS
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "GPS Only (Accurate)"},
        blocking=True,
    )

    # Should update to GPS
    state = hass.states.get(entity_id)
    assert state.state == "GPS Only (Accurate)"


async def test_bluetooth_select(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test bluetooth command select."""
    await setup_integration(hass, mock_fmd_api)

    entity_id = "select.fmd_test_user_bluetooth"
    state = hass.states.get(entity_id)
    assert state is not None

    # Enable Bluetooth
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "Enable Bluetooth"},
        blocking=True,
    )

    mock_fmd_api.create.return_value.toggle_bluetooth.assert_called_once_with(True)


async def test_dnd_select(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test Do Not Disturb command select."""
    await setup_integration(hass, mock_fmd_api)

    entity_id = "select.fmd_test_user_volume_do_not_disturb"
    state = hass.states.get(entity_id)
    assert state is not None

    # Enable DND
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "Enable Do Not Disturb"},
        blocking=True,
    )

    mock_fmd_api.create.return_value.toggle_do_not_disturb.assert_called_once_with(True)


async def test_ringer_mode_select(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ringer mode control select."""
    await setup_integration(hass, mock_fmd_api)

    entity_id = "select.fmd_test_user_volume_ringer_mode"
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

    entity_id = "select.fmd_test_user_volume_ringer_mode"

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "Vibrate Only"},
        blocking=True,
    )

    mock_fmd_api.create.return_value.set_ringer_mode.assert_called_once_with("vibrate")


async def test_ringer_mode_normal(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ringer mode set to normal."""
    await setup_integration(hass, mock_fmd_api)

    entity_id = "select.fmd_test_user_volume_ringer_mode"

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "Normal (Sound + Vibrate)"},
        blocking=True,
    )

    mock_fmd_api.create.return_value.set_ringer_mode.assert_called_once_with("normal")
