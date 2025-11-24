"""Focus 2: Device tracker concurrency skip + failure branches.

Targets remaining untested branches:
- Lines 95-96: Overlapping poll skip when _is_updating=True
- Lines 163-164: High-frequency mode request_location returns False warning
- Lines 210-212: Unknown provider warning during accuracy check in update loop
- Line 10: TYPE_CHECKING import (cannot execute, acceptable residual)
"""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, patch

from conftest import setup_integration
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed


async def test_device_tracker_poll_skip_when_already_updating(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog
) -> None:
    """When update is already in progress, scheduled poll logs warning and skips."""
    await setup_integration(hass, mock_fmd_api)

    # Get the tracker
    entry_id = list(hass.data["fmd"].keys())[0]
    tracker = hass.data["fmd"][entry_id]["tracker"]

    # Manually set _is_updating to True to simulate ongoing update
    tracker._is_updating = True

    # Mock async_update to verify it's not called
    with patch.object(tracker, "async_update") as mock_update:
        # Advance time to trigger the scheduled poll
        # The polling interval is 30 minutes by default
        next_update = dt_util.now() + timedelta(minutes=30)
        async_fire_time_changed(hass, next_update)
        await hass.async_block_till_done()

        # Verify async_update was NOT called
        mock_update.assert_not_called()

    # Verify warning was logged
    assert any(
        "Previous update still in progress" in record.message
        for record in caplog.records
    )


async def test_device_tracker_high_frequency_initial_request_returns_false(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog
) -> None:
    """High-frequency mode poll with request_location returning False logs warning."""
    await setup_integration(hass, mock_fmd_api)

    # Get the tracker
    entry_id = list(hass.data["fmd"].keys())[0]
    tracker = hass.data["fmd"][entry_id]["tracker"]

    # Enable high-frequency mode first
    await tracker.set_high_frequency_mode(True)

    # Mock request_location to return False (failure during poll)
    mock_fmd_api.create.return_value.request_location.return_value = False

    caplog.clear()

    # Advance time to trigger the scheduled poll
    # High frequency interval is 5 minutes by default
    # Add a small buffer to ensure the timer fires
    next_update = dt_util.now() + timedelta(minutes=5, seconds=1)
    async_fire_time_changed(hass, next_update)
    await hass.async_block_till_done()

    # Verify request_location was called
    mock_fmd_api.create.return_value.request_location.assert_called()

    # Verify warning was logged
    assert any(
        "Failed to request location from device" in record.message
        for record in caplog.records
    )


async def test_device_tracker_update_all_blobs_inaccurate_previous_location_retained(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog
) -> None:
    """When all location blobs are inaccurate and filtering enabled, previous location retained."""
    await setup_integration(hass, mock_fmd_api)

    # Get the tracker
    entry_id = list(hass.data["fmd"].keys())[0]
    tracker = hass.data["fmd"][entry_id]["tracker"]

    # Store initial location
    initial_lat = tracker.latitude
    initial_lon = tracker.longitude

    # Mock get_locations to return multiple blobs, all with unknown/inaccurate providers
    import json

    # Create inaccurate location blobs (BeaconDB, unknown, etc.)
    inaccurate_blob_1 = json.dumps(
        {
            "lat": 40.0,
            "lon": -120.0,
            "provider": "BeaconDB",  # Inaccurate
            "time": "2025-11-22T14:00:00Z",
            "bat": 75,
        }
    )
    inaccurate_blob_2 = json.dumps(
        {
            "lat": 41.0,
            "lon": -121.0,
            "provider": "",  # Unknown/empty
            "time": "2025-11-22T14:01:00Z",
            "bat": 74,
        }
    )
    inaccurate_blob_3 = json.dumps(
        {
            "lat": 42.0,
            "lon": -122.0,
            "provider": "mystery_provider",  # Unknown provider triggers warning
            "time": "2025-11-22T14:02:00Z",
            "bat": 73,
        }
    )

    mock_fmd_api.create.return_value.get_locations.return_value = [
        inaccurate_blob_1,
        inaccurate_blob_2,
        inaccurate_blob_3,
    ]

    # Mock decrypt to return the same data (already JSON strings)
    mock_fmd_api.create.return_value.decrypt_data_blob.side_effect = [
        inaccurate_blob_1.encode(),
        inaccurate_blob_2.encode(),
        inaccurate_blob_3.encode(),
    ]

    caplog.clear()
    # Trigger update
    await tracker.async_update()

    # Verify warning about no accurate locations was logged
    assert any(
        "No accurate locations found" in record.message for record in caplog.records
    )

    # Verify warning about unknown provider was logged (lines 210-212)
    assert any(
        "Unknown location provider" in record.message
        and "mystery_provider" in record.message
        for record in caplog.records
    )

    # Verify previous location was retained (not updated to inaccurate locations)
    assert tracker.latitude == initial_lat
    assert tracker.longitude == initial_lon


async def test_device_tracker_high_frequency_poll_request_failure_logs_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog
) -> None:
    """During high-frequency polling, request_location failure logs error."""
    await setup_integration(hass, mock_fmd_api)

    # Get the tracker
    entry_id = list(hass.data["fmd"].keys())[0]
    tracker = hass.data["fmd"][entry_id]["tracker"]

    # Enable high-frequency mode first (with successful initial request)
    mock_fmd_api.create.return_value.request_location.return_value = True
    await tracker.set_high_frequency_mode(True)

    # Now mock request_location to raise exception during poll
    mock_fmd_api.create.return_value.request_location.side_effect = RuntimeError(
        "network failure"
    )

    caplog.clear()

    # Advance time to trigger the scheduled poll
    # Add a small buffer to ensure the timer fires
    next_update = dt_util.now() + timedelta(minutes=5, seconds=1)
    async_fire_time_changed(hass, next_update)
    await hass.async_block_till_done()

    # Verify error was logged
    assert any(
        "Error requesting location during high-frequency poll" in record.message
        for record in caplog.records
    )


async def test_device_tracker_empty_blob_warning_then_next_blob_used(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog
) -> None:
    """Empty blob at index 0 logs warning, then next blob is checked and used."""
    await setup_integration(hass, mock_fmd_api)

    # Get the tracker
    entry_id = list(hass.data["fmd"].keys())[0]
    tracker = hass.data["fmd"][entry_id]["tracker"]

    import json

    # First blob is empty, second is valid JSON string
    valid_blob = json.dumps(
        {
            "lat": 38.0,
            "lon": -123.0,
            "provider": "gps",
            "time": "2025-11-22T15:00:00Z",
            "bat": 80,
            "acc": 10.5,
        }
    )

    mock_fmd_api.create.return_value.get_locations.return_value = [
        None,  # Empty blob (triggers warning at line 471)
        valid_blob,  # String blob
    ]

    # Mock decrypt to return bytes (JSON string as bytes)
    # The actual flow: decrypt_data_blob returns bytes, then json.loads parses them
    mock_fmd_api.create.return_value.decrypt_data_blob.side_effect = [
        valid_blob.encode()  # Return bytes, will be parsed by json.loads
    ]

    caplog.clear()
    await tracker.async_update()

    # Verify warning about empty blob was logged (line 471)
    assert any("Empty blob at index" in record.message for record in caplog.records)

    # Verify the valid second blob was used
    assert tracker.latitude == 38.0
    assert tracker.longitude == -123.0
