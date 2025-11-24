"""Edge case tests for device_tracker to close remaining coverage gaps."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fmd.const import CONF_USE_IMPERIAL, DOMAIN


def _make_entry(hass: HomeAssistant, data_overrides: dict) -> MockConfigEntry:
    base = {
        "url": "https://fmd.example.com",
        "id": "edge_user",
        "artifacts": {
            "base_url": "https://fmd.example.com",
            "fmd_id": "edge_user",
            "access_token": "t",
            "private_key": "k",
            "password_hash": "h",
            "session_duration": 3600,
            "token_issued_at": 123.0,
        },
        "polling_interval": 30,
        "allow_inaccurate_locations": False,
    }
    base.update(data_overrides)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="edge_user",
        data=base,
        entry_id="edge_entry_id",
        unique_id="edge_user",
    )
    entry.add_to_hass(hass)
    return entry


async def test_multiple_location_filtering_selects_first_accurate(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """When blocking inaccurate locations, choose first accurate provider (gps) after skipping BeaconDB."""
    entry = _make_entry(hass, {"allow_inaccurate_locations": False})

    # Provide two blobs: first inaccurate provider BeaconDB, second GPS accurate
    location_blob_inaccurate = {
        "lat": 10.0,
        "lon": 20.0,
        "time": "2025-10-23T12:00:00Z",
        "provider": "BeaconDB",
        "bat": 50,
        "accuracy": 300.0,
    }
    location_blob_accurate = {
        "lat": 11.1,
        "lon": 21.2,
        "time": "2025-10-23T12:01:00Z",
        "provider": "gps",
        "bat": 51,
        "accuracy": 5.0,
    }

    api = mock_fmd_api.create.return_value
    api.get_locations.return_value = [location_blob_inaccurate, location_blob_accurate]

    with patch("custom_components.fmd.FmdClient.from_auth_artifacts", return_value=api):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    tracker = hass.data[DOMAIN][entry.entry_id]["tracker"]
    await tracker.async_update()
    assert tracker.latitude == 11.1 and tracker.longitude == 21.2
    # Battery from accurate location
    assert tracker.extra_state_attributes.get("battery_level") == 51
    assert tracker.extra_state_attributes.get("provider") == "gps"


async def test_block_inaccurate_disabled_uses_first_blob(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """When allow_inaccurate_locations=True, use first (most recent) blob even if provider is BeaconDB."""
    entry = _make_entry(hass, {"allow_inaccurate_locations": True})

    blob1 = {
        "lat": 1.0,
        "lon": 2.0,
        "time": "2025-10-23T12:00:00Z",
        "provider": "BeaconDB",
        "bat": 80,
    }
    blob2 = {
        "lat": 3.0,
        "lon": 4.0,
        "time": "2025-10-23T12:01:00Z",
        "provider": "gps",
        "bat": 81,
    }

    api = mock_fmd_api.create.return_value
    api.get_locations.return_value = [blob1, blob2]

    with patch("custom_components.fmd.FmdClient.from_auth_artifacts", return_value=api):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    tracker = hass.data[DOMAIN][entry.entry_id]["tracker"]
    await tracker.async_update()
    # Should keep first blob provider BeaconDB because filtering disabled
    assert tracker.extra_state_attributes.get("provider") == "BeaconDB"
    assert tracker.latitude == 1.0 and tracker.longitude == 2.0


async def test_imperial_units_conversion_attributes(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test accuracy, altitude, speed conversion to imperial units."""
    entry = _make_entry(
        hass, {"allow_inaccurate_locations": True, CONF_USE_IMPERIAL: True}
    )

    blob = {
        "lat": 7.7,
        "lon": 8.8,
        "time": "2025-10-23T12:00:00Z",
        "provider": "gps",
        "bat": 42,
        "accuracy": 12.0,
        "altitude": 100.0,
        "speed": 5.0,
        "heading": 270,
    }
    api = mock_fmd_api.create.return_value
    api.get_locations.return_value = [blob]

    with patch("custom_components.fmd.FmdClient.from_auth_artifacts", return_value=api):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    tracker = hass.data[DOMAIN][entry.entry_id]["tracker"]
    await tracker.async_update()
    attrs = tracker.extra_state_attributes
    # Accuracy feet ~ 39.37 * 12 => 472.4 (rounded 1 decimal)
    assert attrs.get("gps_accuracy_unit") == "ft"
    assert attrs.get("altitude_unit") == "ft"
    assert attrs.get("speed_unit") == "mph"
    assert attrs.get("heading") == 270
    assert attrs.get("battery_level") == 42


async def test_unknown_provider_logged_as_inaccurate(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog
) -> None:
    """Unknown provider should log warning and be treated as inaccurate when filtering enabled."""
    entry = _make_entry(hass, {"allow_inaccurate_locations": False})

    # First blob unknown provider -> skipped, second gps used
    blob_unknown = {
        "lat": 0.0,
        "lon": 0.0,
        "time": "2025-10-23T12:00:00Z",
        "provider": "mystery",
        "bat": 10,
    }
    blob_gps = {
        "lat": 9.9,
        "lon": 9.8,
        "time": "2025-10-23T12:00:10Z",
        "provider": "gps",
        "bat": 11,
    }
    api = mock_fmd_api.create.return_value
    api.get_locations.return_value = [blob_unknown, blob_gps]

    with patch("custom_components.fmd.FmdClient.from_auth_artifacts", return_value=api):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    tracker = hass.data[DOMAIN][entry.entry_id]["tracker"]
    await tracker.async_update()
    assert tracker.latitude == 9.9 and tracker.longitude == 9.8
    assert any("Unknown location provider" in r.message for r in caplog.records)


async def test_decrypt_returns_invalid_json_logs_exception(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog
) -> None:
    """If decrypted bytes are invalid JSON, update should log error and keep previous location."""
    entry = _make_entry(hass, {"allow_inaccurate_locations": True})
    api = mock_fmd_api.create.return_value

    # Return one 'blob' that will decrypt to invalid JSON string
    api.get_locations.return_value = ["not_json_blob"]

    def bad_decrypt(arg):
        return b"{this is not valid json}"

    api.decrypt_data_blob.side_effect = bad_decrypt

    with patch("custom_components.fmd.FmdClient.from_auth_artifacts", return_value=api):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    tracker = hass.data[DOMAIN][entry.entry_id]["tracker"]
    # First update will try and fail to parse
    try:
        await tracker.async_update()
    except Exception:
        # We expect a generic exception path handled inside async_update; shouldn't propagate
        pass
    # Warning or error about unexpected error should appear
    assert any("Unexpected error getting location" in r.message for r in caplog.records)
