"""Test FMD device tracker coverage for re-entrancy and error handling."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from conftest import setup_integration
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ID, CONF_PASSWORD, CONF_URL
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fmd.const import DOMAIN


async def test_device_tracker_update_locations_reentrancy(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test update_locations skips if already updating."""
    await setup_integration(hass, mock_fmd_api)

    tracker = hass.data[DOMAIN]["test_entry_id"]["tracker"]

    # Manually set _is_updating to True
    tracker._is_updating = True

    with patch(
        "custom_components.fmd.device_tracker.async_track_time_interval"
    ) as mock_track:
        tracker.start_polling()
        callback = mock_track.call_args[0][1]

        # Call the callback while _is_updating is True
        # We need to mock async_update to verify it wasn't called
        with patch.object(tracker, "async_update") as mock_update:
            await callback()
            mock_update.assert_not_called()


async def test_device_tracker_high_frequency_error_handling(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test error handling during high frequency poll."""
    await setup_integration(hass, mock_fmd_api)

    tracker = hass.data[DOMAIN]["test_entry_id"]["tracker"]

    # Enable high frequency mode manually
    tracker._high_frequency_mode = True

    # Mock request_location to raise an exception
    mock_fmd_api.create.return_value.request_location.side_effect = Exception(
        "Test Error"
    )

    # Capture the callback
    with patch(
        "custom_components.fmd.device_tracker.async_track_time_interval"
    ) as mock_track:
        tracker.start_polling()
        callback = mock_track.call_args[0][1]

        # Call the callback
        # It should catch the exception and log error, then proceed to async_update
        with patch.object(tracker, "async_update") as mock_update:
            await callback()

            # Verify async_update WAS called (it proceeds after error)
            mock_update.assert_called_once()

    # Also test the "else" branch where request_location returns False
    mock_fmd_api.create.return_value.request_location.side_effect = None
    mock_fmd_api.create.return_value.request_location.return_value = False

    with patch(
        "custom_components.fmd.device_tracker.async_track_time_interval"
    ) as mock_track:
        tracker.start_polling()
        callback = mock_track.call_args[0][1]

        with patch.object(tracker, "async_update") as mock_update:
            await callback()
            mock_update.assert_called_once()


async def test_device_tracker_setup_initial_location_generic_exception(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker setup handles generic exception during initial location fetch."""
    config_entry = MockConfigEntry(
        version=1,
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

    # Mock the API to fail with generic Exception (not FmdApiException etc)
    mock_fmd_api.create.return_value.get_locations.side_effect = Exception(
        "Generic Error"
    )

    with patch("custom_components.fmd.FmdClient.create", mock_fmd_api.create):
        result = await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    # Setup should succeed
    assert result
    assert config_entry.state == ConfigEntryState.LOADED
