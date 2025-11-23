"""Focus 3: Tests for __init__.py artifact export error handling (lines 85-86).

Target: Cover exception handler when export_auth_artifacts() fails during
password→artifact migration in async_setup_entry.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fmd.const import DOMAIN


@pytest.mark.asyncio
async def test_artifact_export_failure_during_password_migration_logs_warning(
    hass: HomeAssistant, caplog
):
    """Test that artifact export failure during migration logs warning and continues.

    Target: Lines 85-86 in __init__.py
    Scenario: Config entry has password but no artifacts, export_auth_artifacts()
              raises exception during migration attempt.
    Expected: Warning logged, setup continues with password-based auth (no crash).
    """
    # Create a config entry with password only (no artifacts)
    entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="TestDevice",
        data={
            "url": "https://fmd.example.com",
            "id": "test-device-1",
            "password": "test_password",
            # No "artifacts" key - triggers migration path
        },
        source="user",
        unique_id="test-device-1",
    )
    entry.add_to_hass(hass)

    # Mock platforms to prevent actual platform setup
    mock_device = AsyncMock()
    mock_device.wipe = AsyncMock()
    mock_device.lock = AsyncMock()
    mock_device.decode_picture = AsyncMock()
    mock_device.get_picture_blobs = AsyncMock(return_value=[])
    device_class_mock = MagicMock(return_value=mock_device)

    # Mock the FMD API client
    with (
        patch("custom_components.fmd.FmdClient.create") as mock_create,
        patch("custom_components.fmd.button.Device", device_class_mock),
    ):
        mock_api = AsyncMock()
        mock_create.return_value = mock_api

        # Mock export_auth_artifacts to raise an exception
        mock_api.export_auth_artifacts = AsyncMock(
            side_effect=RuntimeError("Network error during artifact export")
        )

        # Mock get_devices to return an empty list (to keep setup simple)
        mock_api.device = MagicMock(return_value=mock_device)
        mock_api.get_devices = AsyncMock(return_value=[])

        # Attempt setup using hass.config_entries.async_setup
        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Verify setup succeeded despite artifact export failure
        assert result is True

        # Verify warning was logged
        assert any(
            "Could not export artifacts for test-device-1" in record.message
            and "will retry on next startup" in record.message
            and "Network error during artifact export" in record.message
            for record in caplog.records
        )

        # Verify authenticate was called with password
        # Verify FmdClient.create was called with password
        mock_create.assert_called_once_with(
            "https://fmd.example.com",
            "test-device-1",
            "test_password",
            drop_password=True,
        )

        # Verify export_auth_artifacts was called
        mock_api.export_auth_artifacts.assert_called_once()


@pytest.mark.asyncio
async def test_artifact_export_generic_exception_during_migration(
    hass: HomeAssistant, caplog
):
    """Test generic exception during artifact export logs warning with exception details.

    Target: Lines 85-86 in __init__.py (exception handler)
    Scenario: export_auth_artifacts() raises a different exception type.
    Expected: Warning logged with exception details, setup continues.
    """
    entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="TestDevice2",
        data={
            "url": "https://fmd.example.com",
            "id": "device-2",
            "password": "pass123",
        },
        source="user",
        unique_id="device-2",
    )
    entry.add_to_hass(hass)

    # Mock platforms to prevent actual platform setup
    mock_device = AsyncMock()
    mock_device.wipe = AsyncMock()
    mock_device.lock = AsyncMock()
    mock_device.decode_picture = AsyncMock()
    mock_device.get_picture_blobs = AsyncMock(return_value=[])
    device_class_mock = MagicMock(return_value=mock_device)

    with (
        patch("custom_components.fmd.FmdClient.create") as mock_create,
        patch("custom_components.fmd.button.Device", device_class_mock),
    ):
        mock_api = AsyncMock()
        mock_create.return_value = mock_api
        mock_api.export_auth_artifacts = AsyncMock(
            side_effect=ValueError("Invalid artifact format from server")
        )
        mock_api.device = MagicMock(return_value=mock_device)
        mock_api.get_devices = AsyncMock(return_value=[])

        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert result is True
        assert any(
            "Could not export artifacts for device-2" in record.message
            and "Invalid artifact format from server" in record.message
            for record in caplog.records
        )
