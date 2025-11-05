"""Fixtures for FMD integration tests."""
from __future__ import annotations

import asyncio
import sys
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_socket
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fmd.const import DOMAIN

# Explicitly load only the plugins we need. Auto-loading is disabled in sitecustomize.py
pytest_plugins = [
    "pytest_asyncio",
    "pytest_cov",
    "pytest_homeassistant_custom_component.plugins",
]


@pytest.fixture(scope="session", autouse=True)
def _enable_sockets_session():
    """Ensure sockets are enabled for event loop creation on Windows."""
    import socket as _socket

    pytest_socket.enable_socket()
    # Debug: confirm socket class
    try:
        clsname = _socket.socket.__qualname__
        print(f"[conftest] socket enabled, socket class: {clsname}")
    except Exception as e:
        print(f"[conftest] socket enable check failed: {e}")
    yield
    pytest_socket.enable_socket()


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


# On Windows, use the SelectorEventLoop to avoid socketpair() during loop creation,
# which some environments block via pytest-socket.
@pytest.fixture(scope="session", autouse=True)
def _windows_selector_event_loop_policy():
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    yield


@pytest.fixture
def mock_fmd_api():
    """Mock FmdClient for testing."""
    api_instance = AsyncMock()

    # Mock async methods - these should match the actual fmd-api v2 methods
    api_instance.get_locations = AsyncMock(
        return_value=[
            {
                "lat": 37.7749,
                "lon": -122.4194,
                "time": "2025-10-23T12:00:00Z",
                "provider": "gps",
                "bat": 85,
                "accuracy": 10.5,  # GPS accuracy in meters
            }
        ]
    )
    api_instance.request_location = AsyncMock(return_value=True)
    api_instance.send_command = AsyncMock(
        return_value=True
    )  # Used for ring, lock, delete, etc.
    api_instance.set_bluetooth = AsyncMock(return_value=True)
    api_instance.set_do_not_disturb = AsyncMock(return_value=True)
    api_instance.set_ringer_mode = AsyncMock(return_value=True)
    api_instance.take_picture = AsyncMock(return_value=True)  # Used for camera capture
    api_instance.get_pictures = AsyncMock(return_value=[])
    api_instance.get_photos = AsyncMock(return_value=[])  # Alias for get_pictures

    # Mock synchronous decrypt_data_blob method
    # It should return JSON bytes that can be parsed
    # Use side_effect to handle both the test dict inputs and default behavior
    def decrypt_blob_side_effect(blob_input):
        """Decrypt blob - if it's a dict (from test), return it as JSON bytes."""
        import json

        if isinstance(blob_input, dict):
            # Test is passing a dict directly, convert it to JSON bytes
            return json.dumps(blob_input).encode("utf-8")
        # Otherwise return the default mock location data
        mock_location_data = {
            "lat": 37.7749,
            "lon": -122.4194,
            "time": "2025-10-23T12:00:00Z",
            "provider": "gps",
            "bat": 85,
            "accuracy": 10.5,  # GPS accuracy in meters
            "speed": 0.0,
        }
        return json.dumps(mock_location_data).encode("utf-8")

    api_instance.decrypt_data_blob = MagicMock(side_effect=decrypt_blob_side_effect)

    # Create a mock for FmdClient.create that returns api_instance
    create_mock = AsyncMock(return_value=api_instance)

    # Store api_instance on create_mock.return_value for tests that access it that way
    create_mock.return_value = api_instance

    # Patch where FmdClient is USED (custom_components.fmd), not where it's defined (fmd_api)
    with patch("custom_components.fmd.FmdClient.create", create_mock):
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
    from homeassistant.const import CONF_ID, CONF_URL

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

    # Mock async_add_executor_job to actually execute the callable
    # This is needed because device_tracker uses it to run decrypt_data_blob
    async def mock_executor_job(func, *args):
        return func(*args)

    config_entry = get_mock_config_entry()
    config_entry.add_to_hass(hass)

    with patch.object(hass, "async_add_executor_job", side_effect=mock_executor_job):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
