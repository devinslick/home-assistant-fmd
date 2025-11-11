"""Additional tests for FMD device tracker to improve coverage."""
from __future__ import annotations

# Removed unused imports (asyncio, json, timedelta) to satisfy flake8
from unittest.mock import AsyncMock, patch

import pytest
from conftest import get_mock_config_entry, setup_integration
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.fmd.const import DOMAIN


async def test_allow_inaccurate_true_uses_first_location(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """When allow_inaccurate_locations is True, use the most recent regardless of provider."""
    # Create a base entry and set allow_inaccurate_locations=True using async_update_entry
    config_entry = get_mock_config_entry()
    config_entry.add_to_hass(hass)

    new_data = dict(config_entry.data)
    new_data["allow_inaccurate_locations"] = True
    await hass.config_entries.async_update_entry(config_entry, data=new_data)

    # Most recent is an inaccurate provider
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 1.0,
            "lon": 2.0,
            "time": "2025-10-23T12:00:00Z",
            "provider": "beacondb",
        }
    ]

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert state.attributes["latitude"] == 1.0
    assert state.attributes["provider"] == "beacondb"


async def test_empty_blob_skipped_then_use_next(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Empty blobs should be skipped; next valid blob should be used."""
    # Return an empty blob first, then a valid-looking value handled by decrypt
    mock_fmd_api.create.return_value.get_locations.return_value = [None, "some_blob"]

    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    # Default decrypt side-effect returns a valid GPS location
    assert state is not None
    assert state.attributes["provider"] == "gps"


async def test_unknown_provider_treated_inaccurate(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Unknown provider should be treated as inaccurate and filtered out when blocking is enabled."""
    # Seed with a good location
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 10.0,
            "lon": 20.0,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
        }
    ]
    await setup_integration(hass, mock_fmd_api)

    # Now only return an unknown provider
    mock_fmd_api.create.return_value.get_locations.return_value = [
        {
            "lat": 30.0,
            "lon": 40.0,
            "time": "2025-10-23T12:05:00Z",
            "provider": "foo_provider",
        }
    ]
    tracker = hass.data[DOMAIN][list(hass.data[DOMAIN].keys())[0]]["tracker"]
    await tracker.async_update()
    tracker.async_write_ha_state()

    state = hass.states.get("device_tracker.fmd_test_user")
    # Should keep the original GPS location
    assert state.attributes["latitude"] == 10.0


async def test_authentication_error_raises_reauth(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Authentication errors should raise ConfigEntryAuthFailed to trigger reauth."""
    from fmd_api import AuthenticationError

    await setup_integration(hass, mock_fmd_api)

    tracker = hass.data[DOMAIN][list(hass.data[DOMAIN].keys())[0]]["tracker"]
    mock_fmd_api.create.return_value.get_locations.side_effect = AuthenticationError(
        "bad token"
    )

    with pytest.raises(ConfigEntryAuthFailed):
        await tracker.async_update()


async def test_operation_and_api_errors_do_not_raise(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """OperationError and FmdApiException should be handled without raising."""
    from fmd_api import FmdApiException, OperationError

    await setup_integration(hass, mock_fmd_api)

    tracker = hass.data[DOMAIN][list(hass.data[DOMAIN].keys())[0]]["tracker"]

    # OperationError should not raise
    mock_fmd_api.create.return_value.get_locations.side_effect = OperationError("conn")
    await tracker.async_update()

    # FmdApiException should not raise
    mock_fmd_api.create.return_value.get_locations.side_effect = FmdApiException(
        "server"
    )
    await tracker.async_update()


async def test_high_frequency_request_can_fail(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """If request_location returns False, the flow should continue without crash."""
    await setup_integration(hass, mock_fmd_api)

    # Make request_location return False
    mock_fmd_api.create.return_value.request_location.return_value = False

    # Speed up sleeps
    with patch("asyncio.sleep", new=AsyncMock()):
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": "switch.fmd_test_user_high_frequency_mode"},
            blocking=True,
        )

    # Should have attempted the request
    mock_fmd_api.create.return_value.request_location.assert_called()


async def test_change_high_frequency_interval_applies_when_active(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Changing the high-frequency interval while active applies immediately."""
    await setup_integration(hass, mock_fmd_api)
    tracker = hass.data[DOMAIN][list(hass.data[DOMAIN].keys())[0]]["tracker"]

    # Enable high-frequency mode with fast sleep
    with patch("asyncio.sleep", new=AsyncMock()):
        await tracker.set_high_frequency_mode(True)

    # Change the interval and ensure it applies
    tracker.set_high_frequency_interval(1)
    assert tracker.polling_interval == 1


async def test_last_poll_time_attribute_present(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """After an update, last_poll_time should be set in attributes."""
    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("device_tracker.fmd_test_user")
    assert state is not None
    assert "last_poll_time" in state.attributes
