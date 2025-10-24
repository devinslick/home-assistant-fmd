"""Fixtures for FMD integration tests."""
from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant

from custom_components.fmd.const import DOMAIN


# Load pytest-homeassistant-custom-component plugins
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_fmd_api():
    """Mock FmdApi for testing."""
    import json
    
    api_instance = AsyncMock()
    
    # Mock async methods - these should match the actual fmd-api methods
    api_instance.get_all_locations = AsyncMock(return_value=[
        {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 85,
            "accuracy": 10.5,  # GPS accuracy in meters
        }
    ])
    api_instance.request_location = AsyncMock(return_value=True)
    api_instance.send_command = AsyncMock(return_value=True)  # Used for ring, lock, delete, etc.
    api_instance.toggle_bluetooth = AsyncMock(return_value=True)
    api_instance.toggle_do_not_disturb = AsyncMock(return_value=True)
    api_instance.set_ringer_mode = AsyncMock(return_value=True)
    api_instance.take_picture = AsyncMock(return_value=True)  # Used for camera capture
    api_instance.get_pictures = AsyncMock(return_value=[])
    api_instance.get_photos = AsyncMock(return_value=[])  # Alias for get_pictures
    
    # Mock synchronous decrypt_data_blob method
    # It should return JSON bytes that can be parsed
    mock_location_data = {
        "lat": 37.7749,
        "lon": -122.4194,
        "time": "2025-10-23T12:00:00Z",
        "provider": "gps",
        "bat": 85,
        "accuracy": 10.5,  # GPS accuracy in meters
        "speed": 0.0,
    }
    api_instance.decrypt_data_blob = MagicMock(return_value=json.dumps(mock_location_data).encode('utf-8'))
    
    # Create a mock for FmdApi.create that returns api_instance
    create_mock = AsyncMock(return_value=api_instance)
    
    # Store api_instance on create_mock.return_value for tests that access it that way
    create_mock.return_value = api_instance
    
    # Patch where FmdApi is USED (custom_components.fmd), not where it's defined (fmd_api)
    with patch("custom_components.fmd.FmdApi.create", create_mock):
        # Yield a mock that has .create attribute for test assertions
        mock_api_class = MagicMock()
        mock_api_class.create = create_mock
        yield mock_api_class


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.fmd.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    return {
        "url": "https://fmd.example.com",
        "id": "test_user",
        "password": "test_password",
        "polling_interval": 30,
        "allow_inaccurate_locations": False,
        "use_imperial": False,
    }


def get_mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry for testing.
    
    Returns a MockConfigEntry that can be modified before being added to hass.
    """
    from homeassistant.const import CONF_URL, CONF_ID
    
    return MockConfigEntry(
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


async def setup_integration(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Set up the FMD integration for testing.
    
    This is a helper function, not a fixture, so tests can call it directly.
    """
    config_entry = get_mock_config_entry()
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
