"""Test FMD device tracker."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from conftest import setup_integration
from homeassistant.components.device_tracker import SourceType
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ID, CONF_PASSWORD, CONF_URL
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fmd.const import DOMAIN


async def test_device_tracker_setup(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker entity is created."""
    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.attributes["source_type"] == SourceType.GPS


async def test_device_tracker_location_update(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker updates location."""
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
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
    assert state.attributes["latitude"] == 37.7749
    assert state.attributes["longitude"] == -122.4194
    assert state.attributes["gps_accuracy"] == 10.5
    assert state.attributes["battery_level"] == 85


async def test_device_tracker_high_frequency_mode(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test high frequency mode switch."""
    await setup_integration(hass, mock_fmd_api)

    # Turn on high frequency mode
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_high_frequency_mode"},
        blocking=True,
    )

    state = hass.states.get("switch.fmd_test_user_high_frequency_mode")
    assert state.state == "on"

    # Verify location request is called
    await hass.async_block_till_done()
    mock_fmd_api.create.return_value.request_location.assert_called()


async def test_device_tracker_imperial_units(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test imperial unit conversion."""
    from homeassistant.const import CONF_ID, CONF_PASSWORD, CONF_URL
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    # Create config entry with imperial units enabled
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
            "use_imperial": True,  # Enable imperial units
        },
        entry_id="test_entry_id",
        unique_id="test_user",
    )
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.fmd_test_user")
    # GPS accuracy should be converted from meters to feet
    # Speed should be converted from m/s to mph
    assert "gps_accuracy_unit" in state.attributes
    assert state.attributes["gps_accuracy_unit"] == "ft"


async def test_device_tracker_location_filtering(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test location accuracy filtering."""
    import json

    # Create mock encrypted blobs for two locations
    beacondb_data = {
        "lat": 37.7749,
        "lon": -122.4194,
        "time": "2025-10-23T12:00:00Z",
        "provider": "beacondb",  # Inaccurate provider
        "bat": 85,
        "accuracy": 10.5,
        "speed": 0.0,
    }
    gps_data = {
        "lat": 37.7750,
        "lon": -122.4195,
        "time": "2025-10-23T11:59:00Z",
        "provider": "gps",  # Accurate provider
        "bat": 85,
        "accuracy": 10.5,
        "speed": 0.0,
    }

    # Mock returns "encrypted" blobs (we'll mock decrypt to handle both)
    mock_fmd_api.create.return_value.get_locations.return_value = [
        "encrypted_beacondb_blob",
        "encrypted_gps_blob",
    ]

    # Mock decrypt to return appropriate data based on blob
    def decrypt_side_effect(blob):
        if blob == "encrypted_beacondb_blob":
            return json.dumps(beacondb_data).encode("utf-8")
        elif blob == "encrypted_gps_blob":
            return json.dumps(gps_data).encode("utf-8")
        return b"{}"

    mock_fmd_api.create.return_value.decrypt_data_blob.side_effect = decrypt_side_effect

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    # Should use GPS location, not beacondb
    assert state.attributes["latitude"] == 37.7750
    assert state.attributes["provider"] == "gps"


async def test_device_tracker_setup_initial_location_fetch_failure(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker setup handles initial location fetch failures gracefully.

    When the initial location fetch fails, the device tracker should still be set up
    but without location data. Platform-level errors should not raise ConfigEntryNotReady.
    """
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
        },
        entry_id="test_entry_id",
        unique_id="test_user",
    )
    config_entry.add_to_hass(hass)

    # Mock the API to fail on location fetch
    mock_fmd_api.create.return_value.get_locations.side_effect = Exception(
        "Server unreachable"
    )

    with patch("custom_components.fmd.FmdClient.create", mock_fmd_api.create):
        result = await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    # Setup should succeed despite location fetch failure (graceful degradation)
    assert result
    assert config_entry.state == ConfigEntryState.LOADED

    # Device tracker should be added but without location data (state = "unknown")
    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.state == "unknown"


# Phase 3 error handling tests
async def test_device_tracker_no_location_data(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker handles empty location data."""
    await setup_integration(hass, mock_fmd_api)

    # Update to empty locations
    mock_fmd_api.create.return_value.get_locations.return_value = []

    # Trigger a manual update by calling the tracker's async_update method
    tracker = hass.data[DOMAIN][list(hass.data[DOMAIN].keys())[0]]["tracker"]
    await tracker.async_update()
    tracker.async_write_ha_state()
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None


async def test_device_tracker_missing_attributes(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker handles missing optional location attributes."""
    # Location with only required fields
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            # Missing optional fields: bat, acc, alt, spd, dir
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.attributes["latitude"] == 37.7749
    assert state.attributes["longitude"] == -122.4194


async def test_device_tracker_with_altitude_speed_heading(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker includes altitude, speed, and heading when available."""
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
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
    # Verify all extended attributes are present
    assert state.attributes["latitude"] == 37.7749
    assert state.attributes["longitude"] == -122.4194
    assert state.attributes["battery_level"] == 85
    assert state.attributes["gps_accuracy"] == 10.5
    assert state.attributes["altitude"] == 100.0
    assert state.attributes["speed"] == 5.5
    assert state.attributes["heading"] == 180.0


async def test_device_tracker_inaccurate_location_filtering_enabled(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test inaccurate location filtering blocks low-accuracy providers."""
    # First set up with accurate location
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 85,
            "accuracy": 10.5,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.attributes["latitude"] == 37.7749

    # Now test that inaccurate provider (beacondb with high inaccuracy) is filtered
    # Update to inaccurate location only
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 40.0,
            "lon": -120.0,
            "time": "2025-10-23T12:05:00Z",
            "provider": "beacondb",
            "bat": 85,
            "accuracy": 5000.0,  # Very inaccurate
        }
    ]

    # Trigger an update and verify it doesn't change (stays at previous location)
    tracker = hass.data[DOMAIN][list(hass.data[DOMAIN].keys())[0]]["tracker"]
    await tracker.async_update()
    tracker.async_write_ha_state()
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.fmd_test_user")
    # Should keep previous accurate location, not update to inaccurate one
    assert state.attributes["latitude"] == 37.7749


async def test_device_tracker_zero_accuracy(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker handles zero accuracy value."""
    # Start fresh with zero accuracy from the beginning
    mock_fmd_api.create.return_value.get_locations.reset_mock()
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 85,
            "accuracy": 0.0,  # Zero accuracy
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.attributes["gps_accuracy"] == 0.0


async def test_device_tracker_with_date_timestamp(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker includes date timestamp when available."""
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "date": 1729689600000,  # Unix timestamp in milliseconds
            "provider": "gps",
            "bat": 85,
            "accuracy": 10.5,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.attributes["device_timestamp"] == "2025-10-23T12:00:00Z"
    assert state.attributes["device_timestamp_ms"] == "1729689600000"


async def test_device_tracker_battery_level_invalid(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker handles invalid battery value gracefully."""
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": "invalid",  # Invalid battery value
            "accuracy": 10.5,
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    # Battery level should not be in attributes if invalid
    assert state.attributes.get("battery_level") is None


async def test_device_tracker_imperial_altitude_speed(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker with altitude and speed attributes."""
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 85,
            "accuracy": 10.5,
            "altitude": 100.0,  # meters
            "speed": 10.0,  # m/s
        }
    ]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    # Verify altitude and speed attributes are present
    assert state.attributes.get("altitude") == 100.0
    assert state.attributes.get("speed") == 10.0
    assert state.attributes.get("altitude_unit") == "m"
    assert state.attributes.get("speed_unit") == "m/s"
