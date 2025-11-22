"""Additional tests to improve coverage from 93% to 95%+."""

from unittest.mock import AsyncMock, patch

import pytest
from conftest import setup_integration
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fmd.const import DOMAIN

# ==============================================================================
# TEXT VALIDATION EDGE CASES
# ==============================================================================


async def test_wipe_pin_empty_validation(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe PIN validation with empty PIN."""
    await setup_integration(hass, mock_fmd_api)

    # Try to set empty PIN
    with pytest.raises(ValueError, match="PIN cannot be empty"):
        await hass.services.async_call(
            "text",
            "set_value",
            {"entity_id": "text.fmd_test_user_wipe_pin", "value": ""},
            blocking=True,
        )


async def test_wipe_pin_non_alphanumeric_validation(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe PIN validation with special characters."""
    await setup_integration(hass, mock_fmd_api)

    # Try to set PIN with special characters
    with pytest.raises(ValueError, match="must be alphanumeric"):
        await hass.services.async_call(
            "text",
            "set_value",
            {"entity_id": "text.fmd_test_user_wipe_pin", "value": "test@123!"},
            blocking=True,
        )


async def test_wipe_pin_with_spaces_validation(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe PIN validation with spaces."""
    await setup_integration(hass, mock_fmd_api)

    # Try to set PIN with spaces - gets caught by alphanumeric check
    with pytest.raises(ValueError, match="alphanumeric"):
        await hass.services.async_call(
            "text",
            "set_value",
            {"entity_id": "text.fmd_test_user_wipe_pin", "value": "test 123"},
            blocking=True,
        )


async def test_wipe_pin_non_ascii_validation(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe PIN validation with non-ASCII characters."""
    await setup_integration(hass, mock_fmd_api)

    # Try to set PIN with non-ASCII characters
    with pytest.raises(ValueError, match="ASCII characters"):
        await hass.services.async_call(
            "text",
            "set_value",
            {"entity_id": "text.fmd_test_user_wipe_pin", "value": "test123café"},
            blocking=True,
        )


async def test_lock_message_empty_validation(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test lock message validation allows empty."""
    await setup_integration(hass, mock_fmd_api)

    # Empty message should be allowed
    await hass.services.async_call(
        "text",
        "set_value",
        {"entity_id": "text.fmd_test_user_lock_message", "value": ""},
        blocking=True,
    )

    state = hass.states.get("text.fmd_test_user_lock_message")
    assert state.state == ""


# ==============================================================================
# SWITCH AUTO-DISABLE DUPLICATE TASK GUARD
# ==============================================================================


async def test_wipe_safety_switch_no_duplicate_auto_disable_task(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe safety switch doesn't create duplicate auto-disable tasks."""
    await setup_integration(hass, mock_fmd_api)

    # Turn on safety switch
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Get the switch entity
    entry_id = list(hass.data[DOMAIN].keys())[0]
    switch = hass.data[DOMAIN][entry_id]["wipe_safety_switch"]

    # Verify task was created
    assert switch._auto_disable_task is not None
    first_task = switch._auto_disable_task

    # Turn off manually
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Turn on again - should cancel old task and create new one
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify new task was created (not a duplicate)
    assert switch._auto_disable_task is not None
    assert switch._auto_disable_task is not first_task


# ==============================================================================
# INIT ERROR PATHS
# ==============================================================================


async def test_setup_entry_artifact_export_fails_with_warning(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test setup when artifact export fails but has password fallback."""
    # Create entry with password (legacy) but no artifacts
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="FMD test_user",
        data={
            "url": "https://fmd.example.com",
            "username": "test_user",
            "password": "test_password",
            "id": "test_user",
        },
        source="user",
        unique_id="test_user",
    )
    entry.add_to_hass(hass)

    # Mock the API to authenticate successfully but fail on artifact export
    mock_fmd_api.authenticate = AsyncMock()
    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.export_artifacts = AsyncMock(
        side_effect=Exception("Artifact export failed")
    )
    device_mock.get_locations = AsyncMock(
        return_value=[
            {
                "lat": 37.7749,
                "lon": -122.4194,
                "time": "2025-10-23T12:00:00Z",
                "provider": "gps",
                "bat": 85,
                "accuracy": 10.5,
            }
        ]
    )

    # Should setup successfully but log warning about artifact migration failure
    with patch.object(hass.config_entries, "async_update_entry"):
        result = await hass.config_entries.async_setup(entry.entry_id)
        assert result is True

    # Entry should be loaded despite artifact migration failure
    await hass.async_block_till_done()


async def test_setup_entry_missing_credentials_raises_valueerror(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test setup fails when entry has neither artifacts nor password."""
    # Create entry without artifacts OR password
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="FMD test_user",
        data={
            "url": "https://fmd.example.com",
            "username": "test_user",
            "id": "test_user",
            # No password, no artifacts
        },
        source="user",
        unique_id="test_user",
    )
    entry.add_to_hass(hass)

    # Should fail during setup
    result = await hass.config_entries.async_setup(entry.entry_id)
    assert result is False


# ==============================================================================
# DEVICE TRACKER EDGE CASES
# ==============================================================================


async def test_device_tracker_high_frequency_interval_boundary(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test high frequency mode with interval at boundary values."""
    await setup_integration(hass, mock_fmd_api)

    # Get the tracker
    entry_id = list(hass.data[DOMAIN].keys())[0]
    tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Enable high frequency mode
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_high_frequency_mode"},
        blocking=True,
    )

    # Set interval to minimum (1 minute)
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.fmd_test_user_high_frequency_interval", "value": 1},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify interval was updated
    assert tracker._high_frequency_interval == 1
