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

###############################################################################
# FINAL: Config Entry Unload/Cleanup Test (should run last)
###############################################################################


async def test_config_entry_unload_cleans_up_entities_and_data(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test unloading a config entry cleans up entities and hass.data."""
    await setup_integration(hass, mock_fmd_api)

    entry = hass.config_entries.async_entries("fmd")[0]
    entry_id = entry.entry_id

    # Confirm entities exist before unload
    assert hass.states.get("switch.fmd_test_user_photo_auto_cleanup") is not None
    assert hass.states.get("sensor.fmd_test_user_photo_count") is not None
    assert "fmd" in hass.data and entry_id in hass.data["fmd"]

    # Unload the config entry
    result = await hass.config_entries.async_unload(entry_id)
    await hass.async_block_till_done()
    assert result is True

    # Entities should be removed or unavailable (restored state)
    state = hass.states.get("switch.fmd_test_user_photo_auto_cleanup")
    assert state is None or (
        state.state == "unavailable" and state.attributes.get("restored")
    )

    state = hass.states.get("sensor.fmd_test_user_photo_count")
    assert state is None or (
        state.state == "unavailable" and state.attributes.get("restored")
    )

    # hass.data for this entry should be cleaned up
    assert entry_id not in hass.data["fmd"]


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


async def test_photo_auto_cleanup_switch_toggle_and_persistence(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test toggling photo auto-cleanup switch and persistence."""
    await setup_integration(hass, mock_fmd_api)

    entity_id = "switch.fmd_test_user_photo_auto_cleanup"
    # Turn on
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "on"

    # Turn off
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "off"

    # Check persistence in config entry
    entry = hass.config_entries.async_entries("fmd")[0]
    assert entry.data["photo_auto_cleanup_is_on"] is False


async def test_high_frequency_mode_switch_toggle_and_tracker_missing(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test toggling high-frequency mode switch and error when tracker missing."""
    await setup_integration(hass, mock_fmd_api)

    entity_id = "switch.fmd_test_user_high_frequency_mode"
    # Turn on
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "on"

    # Remove tracker and turn off (should log error, not raise)
    hass.data["fmd"]["test_entry_id"].pop("tracker", None)
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state is not None and state.state == "off"


async def test_allow_inaccurate_location_switch_toggle_and_tracker_missing(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test toggling allow inaccurate location switch and tracker missing error path."""
    await setup_integration(hass, mock_fmd_api)

    entity_id = "switch.fmd_test_user_location_allow_inaccurate"
    # Turn on
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "on"

    # Remove tracker and turn off (should log error, not raise)
    hass.data["fmd"]["test_entry_id"].pop("tracker", None)
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    # Entity might not exist after tracker removal, or should be "off"
    assert state is None or state.state == "off"


# =============================================================================
# Additional Coverage Tests
# =============================================================================


async def test_device_tracker_polling_interval_switch(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test switching between normal and high-frequency polling intervals."""
    await setup_integration(hass, mock_fmd_api)

    tracker = hass.data["fmd"]["test_entry_id"]["tracker"]
    # Initial interval should be normal
    assert tracker.polling_interval == tracker._normal_interval

    # Set high-frequency interval and enable high-frequency mode
    tracker.set_high_frequency_interval(1)
    await tracker.set_high_frequency_mode(True)
    assert tracker.polling_interval == 1

    # Disable high-frequency mode, should revert to normal
    await tracker.set_high_frequency_mode(False)
    assert tracker.polling_interval == tracker._normal_interval


async def test_sensor_update_media_folder_count_error_handling(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test sensor error handling in _update_media_folder_count."""
    await setup_integration(hass, mock_fmd_api)

    sensor = hass.data["fmd"]["test_entry_id"]["photo_count_sensor"]

    # Patch Path.exists to raise an exception
    from unittest.mock import patch

    with patch("pathlib.Path.exists", side_effect=Exception("fail")):
        sensor._update_media_folder_count()
        assert sensor._photos_in_media_folder == 0


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
