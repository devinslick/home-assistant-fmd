"""Tests to push coverage from 94% to 95%+.

Targets specific uncovered lines in:
- sensor.py: datetime parsing exception, logging paths
- switch.py: auto-disable task cancellation, asyncio.CancelledError
- select.py: tracker not found errors, provider map fallback
"""
import asyncio
from unittest.mock import AsyncMock, patch

from conftest import setup_integration
from homeassistant.core import HomeAssistant

# =============================================================================
# sensor.py Coverage Tests
# =============================================================================


async def test_photo_sensor_invalid_datetime_restoration(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo count sensor when restoring invalid datetime from config entry."""
    from homeassistant.const import CONF_ID, CONF_PASSWORD, CONF_URL
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.fmd.const import DOMAIN

    # Create config entry with INVALID datetime string
    config_entry = MockConfigEntry(
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
            "photo_count_photos_in_media_folder": 5,
            "photo_count_last_download_count": 3,
            "photo_count_last_download_time": "invalid_datetime_string",  # Invalid!
        },
        entry_id="test_entry_id",
        unique_id="test_user",
    )
    config_entry.add_to_hass(hass)

    # Mock async_add_executor_job
    async def mock_executor_job(func, *args):
        return func(*args)

    with patch.object(hass, "async_add_executor_job", side_effect=mock_executor_job):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    # Sensor should be created despite invalid datetime (falls back to None)
    sensor = hass.data[DOMAIN][config_entry.entry_id]["photo_count_sensor"]
    assert sensor._last_download_time is None  # Should fall back to None


# =============================================================================
# switch.py Coverage Tests
# =============================================================================


async def test_device_wipe_safety_cancel_auto_disable(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test cancelling auto-disable task when safety switch turned off."""
    await setup_integration(hass, mock_fmd_api)

    # Turn safety switch ON
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Get the switch entity to check task is running
    switch = hass.data["fmd"]["test_entry_id"]["wipe_safety_switch"]
    assert switch._auto_disable_task is not None
    assert not switch._auto_disable_task.done()

    # Turn safety switch OFF (should cancel task)
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Task should be cancelled and cleaned up
    assert switch._auto_disable_task is None


async def test_device_wipe_safety_auto_disable_cancelled(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test _auto_disable handles asyncio.CancelledError gracefully."""
    await setup_integration(hass, mock_fmd_api)

    # Turn safety switch ON
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Get the switch and task
    switch = hass.data["fmd"]["test_entry_id"]["wipe_safety_switch"]
    task = switch._auto_disable_task
    assert task is not None

    # Cancel the task to trigger CancelledError handling
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass  # Expected

    # Switch should still be on (task was cancelled before timeout)
    state = hass.states.get("switch.fmd_test_user_wipe_safety_switch")
    assert state.state == "on"


# =============================================================================
# select.py Coverage Tests
# =============================================================================


async def test_location_source_invalid_option_fallback(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test location source returns 'all' for invalid/unmapped options."""
    # Unit-style test of the mapping logic via the public method
    from homeassistant.const import CONF_ID, CONF_PASSWORD, CONF_URL
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.fmd.const import DOMAIN
    from custom_components.fmd.select import FmdLocationSourceSelect

    # Minimal config entry for constructing the entity
    config_entry = MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="test_user",
        data={
            CONF_URL: "https://fmd.example.com",
            CONF_ID: "test_user",
            CONF_PASSWORD: "test_password",
        },
        entry_id="test_entry_id",
        unique_id="test_user",
    )
    config_entry.add_to_hass(hass)

    # Instantiate select and set an invalid option
    location_source = FmdLocationSourceSelect(hass, config_entry)
    location_source._attr_current_option = "Invalid Option Not In Map"

    # Public API should fallback to "all"
    provider = location_source.get_provider_value()
    assert provider == "all"


async def test_bluetooth_select_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test Bluetooth select when tracker is not found in hass.data."""
    await setup_integration(hass, mock_fmd_api)

    # Remove the tracker from hass.data to simulate error condition
    del hass.data["fmd"]["test_entry_id"]["tracker"]

    # Try to select an option (should log error and return early)
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_bluetooth",
            "option": "Enable Bluetooth",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should complete without error (logs error internally)


async def test_ringer_mode_select_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test Ringer Mode select when tracker is not found in hass.data."""
    await setup_integration(hass, mock_fmd_api)

    # Remove the tracker from hass.data to simulate error condition
    del hass.data["fmd"]["test_entry_id"]["tracker"]

    # Try to select an option (should log error and return early)
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_volume_ringer_mode",
            "option": "Normal (Sound + Vibrate)",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should complete without error (logs error internally)


async def test_dnd_select_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test DND select when tracker is not found in hass.data."""
    await setup_integration(hass, mock_fmd_api)

    # Remove the tracker from hass.data to simulate error condition
    del hass.data["fmd"]["test_entry_id"]["tracker"]

    # Try to select an option (should log error and return early)
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_volume_do_not_disturb",
            "option": "Enable Do Not Disturb",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should complete without error (logs error internally)
