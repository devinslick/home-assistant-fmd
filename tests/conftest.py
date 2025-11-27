"""Fixtures for FMD integration tests."""
from __future__ import annotations

import sys
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

# Force enable sockets on Windows to avoid pytest-socket blocking ProactorEventLoop
if sys.platform.startswith("win"):
    try:
        import pytest_socket

        pytest_socket.enable_socket()

        # Monkeypatch disable_socket to be a no-op so it can't be re-enabled
        def _no_disable_socket(*args, **kwargs):
            pass

        pytest_socket.disable_socket = _no_disable_socket
    except ImportError:
        # If pytest_socket is not installed, skip socket monkeypatching.
        # This is safe: tests will run without socket blocking workaround.
        pass

import asyncio  # noqa: E402

import pytest  # noqa: E402
from homeassistant import loader  # noqa: E402


@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def enable_custom_integrations(hass):
    """Enable custom integrations defined in the test dir."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS)


@pytest.fixture(autouse=True)
async def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def mock_fmd_api():
    """Mock FmdClient for testing."""
    api_instance = AsyncMock()

    # Mock authentication artifact methods (fmd_api 2.0.4+)
    api_instance.export_auth_artifacts = AsyncMock(
        return_value={
            "base_url": "https://fmd.example.com",
            "fmd_id": "test_user",
            "access_token": "mock_access_token",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMOCK_KEY\n-----END PRIVATE KEY-----",
            "password_hash": "mock_password_hash",
            "session_duration": 3600,
            "token_issued_at": 1234567890.0,
        }
    )
    api_instance.close = AsyncMock(return_value=None)

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

    # Mock device method for new API (fmd_api 2.0.4+)
    mock_device = AsyncMock()
    mock_device.get_picture_blobs = AsyncMock(return_value=[])

    # Mock PhotoResult for decode_picture
    from datetime import datetime

    mock_photo_result = MagicMock()
    mock_photo_result.data = b"fake_image_data"
    mock_photo_result.mime_type = "image/jpeg"
    mock_photo_result.timestamp = datetime(2025, 10, 23, 12, 0, 0)
    mock_photo_result.raw = {}
    mock_device.decode_picture = AsyncMock(return_value=mock_photo_result)

    # Mock wipe and lock with new parameters
    mock_device.wipe = AsyncMock(return_value=None)
    mock_device.lock = AsyncMock(return_value=None)

    api_instance.device = MagicMock(return_value=mock_device)

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

    # Create a mock for FmdClient.from_auth_artifacts (fmd_api 2.0.4+)
    from_artifacts_mock = AsyncMock(return_value=api_instance)

    # Store api_instance on create_mock.return_value for tests that access it that way
    create_mock.return_value = api_instance
    from_artifacts_mock.return_value = api_instance

    # Mock Device class constructor to return our mock_device
    # When called as Device(client, id), it should return mock_device
    def device_constructor_side_effect(*args, **kwargs):
        """Return the pre-configured mock_device regardless of arguments."""
        return mock_device

    device_class_mock = MagicMock(side_effect=device_constructor_side_effect)

    # Patch where FmdClient is USED (custom_components.fmd), not where it's defined (fmd_api)
    with patch("custom_components.fmd.FmdClient.create", create_mock), patch(
        "custom_components.fmd.FmdClient.from_auth_artifacts", from_artifacts_mock
    ), patch("custom_components.fmd.config_flow.FmdClient.create", create_mock), patch(
        "custom_components.fmd.config_flow.FmdClient.from_auth_artifacts",
        from_artifacts_mock,
    ), patch(
        "custom_components.fmd.button.Device", device_class_mock
    ):
        # Yield a mock that has .create and .from_auth_artifacts attributes for test assertions
        mock_api_class = MagicMock()
        mock_api_class.create = create_mock
        mock_api_class.from_auth_artifacts = from_artifacts_mock
        mock_api_class.device = MagicMock(
            return_value=mock_device
        )  # Keep for backward compat
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
    """Return a mock config entry with artifacts (fmd_api 2.0.4+)."""
    return {
        "url": "https://fmd.example.com",
        "id": "test_user",
        "artifacts": {
            "base_url": "https://fmd.example.com",
            "fmd_id": "test_user",
            "access_token": "mock_access_token",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMOCK_KEY\n-----END PRIVATE KEY-----",
            "password_hash": "mock_password_hash",
            "session_duration": 3600,
            "token_issued_at": 1234567890.0,
        },
        "polling_interval": 30,
        "allow_inaccurate_locations": False,
        "use_imperial": False,
    }
