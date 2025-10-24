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
    mock_fmd_api.create.return_value.get_all_locations.return_value = [
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 85,
            "acc": 10.5,
            "alt": 100.0,
            "spd": 5.5,
            "dir": 180.0,
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
    mock_fmd_api.create.return_value.get_all_locations.return_value = [
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
    """Test device tracker setup fails gracefully if initial location fetch fails.

    When the initial location fetch fails, ConfigEntryNotReady should be raised,
    signaling to Home Assistant to retry with exponential backoff instead of
    permanently failing the setup.
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
    mock_fmd_api.create.return_value.get_all_locations.side_effect = Exception(
        "Server unreachable"
    )

    with patch("custom_components.fmd.__init__.FmdApi", mock_fmd_api):
        result = await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    # Setup should fail due to ConfigEntryNotReady being raised
    assert not result
    assert config_entry.state == ConfigEntryState.SETUP_ERROR

    # Device tracker should not be added if setup fails
    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is None
