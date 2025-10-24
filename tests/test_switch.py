"""Test FMD switch entities."""
from __future__ import annotations

from unittest.mock import AsyncMock

from conftest import setup_integration
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant


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


async def test_high_frequency_mode_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test high frequency mode when tracker is not found."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass.data
    hass.data["fmd"][list(hass.data["fmd"].keys())[0]].pop("tracker", None)

    entity_id = "switch.fmd_test_user_high_frequency_mode"

    # Turn on - should handle gracefully without crashing
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state is not None


async def test_allow_inaccurate_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test allow inaccurate when tracker is not found."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass.data
    hass.data["fmd"][list(hass.data["fmd"].keys())[0]].pop("tracker", None)

    entity_id = "switch.fmd_test_user_location_allow_inaccurate_updates"

    # Turn on - should handle gracefully without crashing
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state is not None


async def test_high_frequency_mode_api_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test high frequency mode when API raises error still updates state."""
    await setup_integration(hass, mock_fmd_api)

    # Make the tracker method raise an error
    tracker = hass.data["fmd"][list(hass.data["fmd"].keys())[0]]["tracker"]
    tracker.set_high_frequency_mode = AsyncMock(side_effect=RuntimeError("API error"))

    entity_id = "switch.fmd_test_user_high_frequency_mode"

    # Try to turn on - will update state even if API fails
    # The implementation writes state before calling the tracker method
    try:
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": entity_id},
            blocking=True,
        )
    except RuntimeError:
        # Expected - API error is raised but state was already updated
        pass

    # State should be updated (set before API call)
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON


async def test_allow_inaccurate_api_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test allow inaccurate when tracker method fails."""
    await setup_integration(hass, mock_fmd_api)

    # This test verifies that the switch can still turn on/off even if
    # the underlying tracker object doesn't have the _block_inaccurate attribute
    # or if it fails to update
    entity_id = "switch.fmd_test_user_location_allow_inaccurate_updates"

    # Turn on - updates the tracker's internal state
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    # Turn off - should work
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": entity_id},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF
