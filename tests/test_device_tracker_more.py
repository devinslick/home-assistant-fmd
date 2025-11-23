"""Additional tests for device_tracker behavior and edge cases."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from conftest import setup_integration
from homeassistant.core import HomeAssistant

from custom_components.fmd.const import DOMAIN


async def test_high_frequency_request_provider_mapping(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """When high frequency is enabled, selected provider maps to the API request provider."""
    await setup_integration(hass, mock_fmd_api)

    # Get the tracker
    entry_id = list(hass.data[DOMAIN].keys())[0]
    tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Set the location source to GPS Only (Accurate) so provider should be 'gps'
    hass.states.async_set("select.fmd_test_user_location_source", "GPS Only (Accurate)")
    await hass.async_block_till_done()

    # Patch sleep to avoid waiting and ensure request_location returns True
    mock_api = mock_fmd_api.create.return_value
    mock_api.request_location.return_value = True

    # Force high frequency mode and patch the async_track_time_interval so the
    # update callback is executed immediately (to exercise provider mapping).
    def _fake_async_track(hass_obj, callback, interval):
        hass_obj.async_create_task(callback(None))
        return lambda: None

    with patch(
        "custom_components.fmd.device_tracker.async_track_time_interval",
        side_effect=_fake_async_track,
    ), patch("asyncio.sleep", new=AsyncMock()):
        tracker._high_frequency_mode = True
        tracker.start_polling()
        await hass.async_block_till_done()

    # request_location should have been called with provider 'gps'
    # Confirm the mock was awaited with provider 'gps' (it may be called multiple times)
    calls = mock_api.request_location.await_args_list
    assert any(kwargs.get("provider") == "gps" for _, kwargs in calls)
    # Polling interval change is only applied by set_high_frequency_mode; start_polling
    # itself does not change the poll interval, so we only assert the provider call.


async def test_high_frequency_request_failure_logs_warning(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog
) -> None:
    """When request_location returns False, a warning is emitted and no exception is raised."""
    await setup_integration(hass, mock_fmd_api)

    mock_api = mock_fmd_api.create.return_value
    mock_api.request_location.return_value = False

    # Force provider selection to 'all' by leaving select at default
    with patch("asyncio.sleep", new=AsyncMock()):
        tracker = hass.data[DOMAIN][list(hass.data[DOMAIN].keys())[0]]["tracker"]
        await tracker.set_high_frequency_mode(True)

    assert any("Failed to request location" in message for message in caplog.messages)


async def test_set_high_frequency_interval_applies_immediately_when_enabled(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Updating the high-frequency interval while enabled applies immediately."""
    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data[DOMAIN].keys())[0]
    tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Enable high frequency mode
    tracker._high_frequency_mode = True
    original_interval = tracker._polling_interval

    # Update the high-frequency interval - should apply to polling interval immediately
    tracker.set_high_frequency_interval(2)
    assert tracker._high_frequency_interval == 2
    assert tracker._polling_interval == 2
    assert tracker._polling_interval != original_interval


async def test_is_location_accurate_unknown_provider_logs_and_returns_false(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog
) -> None:
    """Unknown providers should be treated as inaccurate with a warning logged."""
    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data[DOMAIN].keys())[0]
    tracker = hass.data[DOMAIN][entry_id]["tracker"]

    result = tracker._is_location_accurate({"provider": "some_unknown_provider"})
    assert result is False
    assert any("Unknown location provider" in message for message in caplog.messages)


async def test_decrypt_blob_exception_logged(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog
) -> None:
    """If decrypt_data_blob raises, the async_update should handle it and log an error."""
    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data[DOMAIN].keys())[0]
    tracker = hass.data[DOMAIN][entry_id]["tracker"]

    mock_api = mock_fmd_api.create.return_value
    # Make the synchronous decrypt_data_blob raise
    mock_api.decrypt_data_blob.side_effect = Exception("decrypt failed")

    await tracker.async_update()

    assert any(
        "Unexpected error getting location" in message for message in caplog.messages
    )


async def test_invalid_battery_parsing_sets_none_and_logs(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog
) -> None:
    """If battery value cannot be parsed as int, a warning is logged and battery is None."""
    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data[DOMAIN].keys())[0]
    tracker = hass.data[DOMAIN][entry_id]["tracker"]

    # Provide a blob with invalid 'bat' value
    mock_api = mock_fmd_api.create.return_value
    # Make get_locations return a JSON-able dict blob (our decrypt function handles dicts)
    mock_api.get_locations.return_value = [
        {
            "lat": 1.1,
            "lon": 2.2,
            "provider": "gps",
            "time": "2025-10-23T12:00:00Z",
            "bat": "not_an_int",
        }
    ]

    await tracker.async_update()

    assert tracker._battery_level is None
    assert any("Invalid battery value" in message for message in caplog.messages)
