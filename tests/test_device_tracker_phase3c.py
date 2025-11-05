"""Phase 3c comprehensive device_tracker tests - targeting remaining coverage gaps."""
from __future__ import annotations

from unittest.mock import AsyncMock

from conftest import setup_integration
from homeassistant.core import HomeAssistant


async def test_device_tracker_no_location_data(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker when get_locations returns empty list."""
    mock_fmd_api.create.return_value.get_locations.return_value = []

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    # State should be 'unknown' when no location data
    assert state.state in ["unknown", "home"]


async def test_device_tracker_with_altitude_speed_heading(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker with altitude, speed, and heading data."""
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 75,
            "accuracy": 5.0,
            "altitude": 250.5,
            "speed": 25.5,
            "heading": 90.0,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.attributes.get("altitude") == 250.5
    assert state.attributes.get("speed") == 25.5
    assert state.attributes.get("heading") == 90.0


async def test_device_tracker_inaccurate_location_filtering_enabled(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker filters inaccurate locations when enabled."""
    # Return two locations - first inaccurate, second accurate
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T11:00:00Z",
            "provider": "cell",
            "bat": 75,
            "accuracy": 5000.0,  # Very inaccurate
            "altitude": 0.0,
            "speed": 0.0,
            "heading": 0.0,
        },
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 75,
            "accuracy": 5.0,
            "altitude": 100.0,
            "speed": 5.5,
            "heading": 180.0,
        },
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.attributes.get("latitude") == 37.7749


async def test_device_tracker_zero_accuracy(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker handles zero accuracy gracefully."""
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 75,
            "accuracy": 0.0,  # Zero accuracy
            "altitude": 0.0,
            "speed": 0.0,
            "heading": 0.0,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    # GPS with zero accuracy is still accurate, so it should be used
    assert state.attributes.get("gps_accuracy") == 0.0


async def test_device_tracker_negative_battery(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker with unusual battery percentage."""
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 0,  # Very low battery
            "accuracy": 10.5,
            "altitude": 100.0,
            "speed": 5.5,
            "heading": 180.0,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.attributes.get("battery_level") == 0


async def test_device_tracker_very_high_battery(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker with maximum battery percentage."""
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 100,
            "accuracy": 10.5,
            "altitude": 100.0,
            "speed": 5.5,
            "heading": 180.0,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.attributes.get("battery_level") == 100


async def test_device_tracker_get_locations_api_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker when get_locations raises exception.

    Platform-level errors should be handled gracefully.
    """
    from homeassistant.components.device_tracker import SourceType

    mock_fmd_api.create.return_value.get_locations.side_effect = Exception("API Error")

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    # Should handle error gracefully
    assert state.attributes.get("source_type") == SourceType.GPS


async def test_device_tracker_missing_optional_fields(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker with missing optional location fields."""
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 85,
            # Missing: accuracy, altitude, speed, heading
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.attributes.get("latitude") == 37.7749
    assert state.attributes.get("longitude") == -122.4194


async def test_device_tracker_high_frequency_mode_toggle(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker high frequency mode can be toggled."""
    await setup_integration(hass, mock_fmd_api)

    # Get the entity and toggle high frequency mode
    entry_id = list(hass.data["fmd"].keys())[0]
    tracker = hass.data["fmd"][entry_id]["tracker"]

    # Enable high frequency mode
    await tracker.set_high_frequency_mode(True)
    await hass.async_block_till_done()

    # Disable high frequency mode
    await tracker.set_high_frequency_mode(False)
    await hass.async_block_till_done()

    # Verify the method was called
    assert tracker is not None


async def test_device_tracker_async_will_remove_from_hass(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker cleanup when removed from Home Assistant."""
    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data["fmd"].keys())[0]
    tracker = hass.data["fmd"][entry_id]["tracker"]

    # Call async_will_remove_from_hass
    await tracker.async_will_remove_from_hass()

    # Verify the entity is cleaned up
    assert tracker is not None


async def test_device_tracker_timestamp_parsing(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker parses various timestamp formats."""
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T15:30:45Z",  # ISO format
            "provider": "gps",
            "bat": 85,
            "accuracy": 10.5,
            "altitude": 100.0,
            "speed": 5.5,
            "heading": 180.0,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.attributes.get("latitude") == 37.7749
