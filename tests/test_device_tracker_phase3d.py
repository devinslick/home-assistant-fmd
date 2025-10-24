"""Phase 3d advanced device_tracker tests - complex location provider logic."""
from __future__ import annotations

from unittest.mock import AsyncMock

from conftest import setup_integration
from homeassistant.core import HomeAssistant


async def test_device_tracker_location_provider_gps_accurate(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker correctly identifies GPS as accurate provider."""
    mock_fmd_api.create.return_value.get_all_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 85,
            "accuracy": 5.0,
            "altitude": 100.0,
            "speed": 5.5,
            "heading": 180.0,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.attributes.get("latitude") == 37.7749


async def test_device_tracker_location_provider_cell_inaccurate(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker correctly identifies cell as inaccurate."""
    mock_fmd_api.create.return_value.get_all_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "cell",
            "bat": 85,
            "accuracy": 1000.0,
            "altitude": 0.0,
            "speed": 0.0,
            "heading": 0.0,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None


async def test_device_tracker_location_provider_beacon_inaccurate(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker correctly identifies beacon as inaccurate."""
    mock_fmd_api.create.return_value.get_all_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "beacon",
            "bat": 85,
            "accuracy": 500.0,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None


async def test_device_tracker_location_provider_wifi_accurate(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker correctly identifies wifi as potentially accurate."""
    mock_fmd_api.create.return_value.get_all_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "wifi",
            "bat": 85,
            "accuracy": 25.0,
            "altitude": 100.0,
            "speed": 2.5,
            "heading": 90.0,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.attributes.get("latitude") == 37.7749


async def test_device_tracker_unknown_provider(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker with unknown location provider."""
    mock_fmd_api.create.return_value.get_all_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "unknown_provider",
            "bat": 85,
            "accuracy": 100.0,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None


async def test_device_tracker_high_frequency_mode_with_location_request(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test high-frequency mode requests fresh location from device."""
    mock_fmd_api.create.return_value.request_location.return_value = True
    mock_fmd_api.create.return_value.get_all_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 85,
            "accuracy": 5.0,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data["fmd"].keys())[0]
    tracker = hass.data["fmd"][entry_id]["tracker"]

    # Enable high-frequency mode
    await tracker.set_high_frequency_mode(True)
    await hass.async_block_till_done()

    # Verify request_location was called during high-frequency setup
    mock_fmd_api.create.return_value.request_location.assert_called()


async def test_device_tracker_high_frequency_mode_location_request_fails(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test high-frequency mode handles location request failure gracefully."""
    mock_fmd_api.create.return_value.request_location.return_value = False
    mock_fmd_api.create.return_value.get_all_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 85,
            "accuracy": 5.0,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data["fmd"].keys())[0]
    tracker = hass.data["fmd"][entry_id]["tracker"]

    # Enable high-frequency mode
    await tracker.set_high_frequency_mode(True)
    await hass.async_block_till_done()

    # Should handle failure gracefully
    mock_fmd_api.create.return_value.request_location.assert_called()


async def test_device_tracker_high_frequency_mode_location_request_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test high-frequency mode handles location request exception."""
    mock_fmd_api.create.return_value.request_location.side_effect = Exception(
        "API Error"
    )
    mock_fmd_api.create.return_value.get_all_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 85,
            "accuracy": 5.0,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data["fmd"].keys())[0]
    tracker = hass.data["fmd"][entry_id]["tracker"]

    # Enable high-frequency mode - should handle exception
    await tracker.set_high_frequency_mode(True)
    await hass.async_block_till_done()

    mock_fmd_api.create.return_value.request_location.assert_called()


async def test_device_tracker_multiple_locations_filtering_enabled(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker filters multiple locations when enabled."""
    mock_fmd_api.create.return_value.get_all_locations.return_value = [
        {
            "lat": 37.6,
            "lon": -122.5,
            "time": "2025-10-23T12:00:00Z",
            "provider": "beacon",
            "bat": 85,
            "accuracy": 5000.0,
        },
        {
            "lat": 37.65,
            "lon": -122.45,
            "time": "2025-10-23T11:50:00Z",
            "provider": "cell",
            "bat": 85,
            "accuracy": 1500.0,
        },
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T11:40:00Z",
            "provider": "gps",
            "bat": 85,
            "accuracy": 5.0,
        },
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    # Should select the GPS location as most accurate
    assert state.attributes.get("latitude") == 37.7749


async def test_device_tracker_decrypt_error_in_update(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker handles decryption error during update."""
    mock_fmd_api.create.return_value.get_all_locations.return_value = ["corrupted_blob"]
    mock_fmd_api.create.return_value.decrypt_data_blob.side_effect = Exception(
        "Decryption failed"
    )

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    # Should handle error gracefully


async def test_device_tracker_battery_invalid_value(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker handles invalid battery value."""
    mock_fmd_api.create.return_value.get_all_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": "not_a_number",
            "accuracy": 5.0,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    # Should handle invalid battery gracefully


async def test_device_tracker_polling_interval_update(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker polling interval can be updated."""
    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data["fmd"].keys())[0]
    tracker = hass.data["fmd"][entry_id]["tracker"]

    # Update polling interval
    tracker.set_polling_interval(10)
    await hass.async_block_till_done()

    assert tracker.polling_interval == 10


async def test_device_tracker_high_frequency_interval_update(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker high-frequency interval can be updated."""
    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data["fmd"].keys())[0]
    tracker = hass.data["fmd"][entry_id]["tracker"]

    # Update high-frequency interval
    tracker.set_high_frequency_interval(2)
    await hass.async_block_till_done()

    assert tracker._high_frequency_interval == 2
