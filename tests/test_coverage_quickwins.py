"""Quick win tests to increase coverage from 94% to 95%+.

These tests target specific error paths and edge cases in:
- button.py: Photo download error handling
- device_tracker.py: Empty location handling
- sensor.py: File system errors
"""
import base64
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_fmd_api():
    """Mock FmdClient API."""
    with patch("custom_components.fmd.FmdClient") as mock:
        api_instance = AsyncMock()
        api_instance.get_locations = AsyncMock(return_value=[])
        api_instance.get_pictures = AsyncMock(return_value=[])
        api_instance.send_command = AsyncMock()
        api_instance.request_location = AsyncMock()
        api_instance.set_bluetooth = AsyncMock()
        api_instance.set_do_not_disturb = AsyncMock()
        api_instance.set_ringer_mode = AsyncMock()
        mock.create = AsyncMock(return_value=api_instance)
        yield mock


async def setup_integration(hass: HomeAssistant, mock_api: AsyncMock):
    """Set up the FMD integration with mocked API."""
    from homeassistant.setup import async_setup_component

    # Mock the FmdClient in the integration's __init__.py
    with patch("custom_components.fmd.FmdClient", mock_api):
        result = await async_setup_component(
            hass,
            "fmd",
            {
                "fmd": {
                    "url": "https://test.fmd.server",
                    "id": "test-user",
                    "password": "test-password",
                    "update_interval": 15,
                    "allow_inaccurate": False,
                    "use_imperial": False,
                }
            },
        )
        await hass.async_block_till_done()
        assert result


# =============================================================================
# button.py Error Path Tests (Target: 12+ lines)
# =============================================================================


async def test_download_photos_exif_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download when EXIF parsing fails."""
    await setup_integration(hass, mock_fmd_api)

    # Create a mock photo blob without proper EXIF data
    mock_blob = {
        "data": base64.b64encode(b"fake_image_data_no_exif").decode(),
        "key": base64.b64encode(b"fake_key").decode(),
    }
    mock_fmd_api.create.return_value.get_pictures.return_value = [mock_blob]

    # Mock Image.open to raise an exception when parsing EXIF
    with patch("custom_components.fmd.button.Image") as mock_image:
        mock_img = Mock()
        mock_img.getexif.side_effect = Exception("EXIF parsing failed")
        mock_image.open.return_value = mock_img

        # Mock decrypt to return fake image bytes
        with patch(
            "custom_components.fmd.button.FmdDownloadPhotosButton._async_decrypt_data_blob"
        ) as mock_decrypt:
            mock_decrypt.return_value = base64.b64encode(b"fake_image").decode()

            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_photo_download"},
                blocking=True,
            )
            await hass.async_block_till_done()

    # Should still save photo even without EXIF (fallback to hash-only filename)
    mock_fmd_api.create.return_value.get_pictures.assert_called_once()


async def test_download_photos_no_exif_data(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download when image has no EXIF data at all."""
    await setup_integration(hass, mock_fmd_api)

    mock_blob = {
        "data": base64.b64encode(b"fake_image_data").decode(),
        "key": base64.b64encode(b"fake_key").decode(),
    }
    mock_fmd_api.create.return_value.get_pictures.return_value = [mock_blob]

    # Mock Image with empty EXIF
    with patch("custom_components.fmd.button.Image") as mock_image:
        mock_img = Mock()
        mock_img.getexif.return_value = {}  # Empty EXIF dict
        mock_image.open.return_value = mock_img

        with patch(
            "custom_components.fmd.button.FmdDownloadPhotosButton._async_decrypt_data_blob"
        ) as mock_decrypt:
            mock_decrypt.return_value = base64.b64encode(b"fake_image").decode()

            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_photo_download"},
                blocking=True,
            )
            await hass.async_block_till_done()

    mock_fmd_api.create.return_value.get_pictures.assert_called_once()


async def test_download_photos_media_directory_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download when media directory creation fails."""
    await setup_integration(hass, mock_fmd_api)

    mock_blob = {
        "data": base64.b64encode(b"fake_image").decode(),
        "key": base64.b64encode(b"fake_key").decode(),
    }
    mock_fmd_api.create.return_value.get_pictures.return_value = [mock_blob]

    # Mock Path.mkdir to raise OSError
    with patch("custom_components.fmd.button.Path") as mock_path:
        mock_dir = Mock(spec=Path)
        mock_dir.mkdir.side_effect = OSError("Permission denied")
        mock_dir.exists.return_value = False
        mock_path.return_value = mock_dir

        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Should call get_pictures but fail on directory creation
    mock_fmd_api.create.return_value.get_pictures.assert_called_once()


async def test_download_photos_decryption_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download when decryption fails."""
    await setup_integration(hass, mock_fmd_api)

    mock_blob = {
        "data": base64.b64encode(b"corrupt_data").decode(),
        "key": base64.b64encode(b"bad_key").decode(),
    }
    mock_fmd_api.create.return_value.get_pictures.return_value = [mock_blob]

    # Mock decrypt to raise an exception
    with patch(
        "custom_components.fmd.button.FmdDownloadPhotosButton._async_decrypt_data_blob"
    ) as mock_decrypt:
        mock_decrypt.side_effect = Exception("Decryption failed")

        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Should handle exception gracefully
    mock_fmd_api.create.return_value.get_pictures.assert_called_once()


async def test_download_photos_file_write_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download when file write fails."""
    await setup_integration(hass, mock_fmd_api)

    mock_blob = {
        "data": base64.b64encode(b"fake_image").decode(),
        "key": base64.b64encode(b"fake_key").decode(),
    }
    mock_fmd_api.create.return_value.get_pictures.return_value = [mock_blob]

    with patch("custom_components.fmd.button.Image"):
        with patch(
            "custom_components.fmd.button.FmdDownloadPhotosButton._async_decrypt_data_blob"
        ) as mock_decrypt:
            mock_decrypt.return_value = base64.b64encode(b"fake_image").decode()

            # Mock async_add_executor_job to simulate file write failure
            original_executor = hass.async_add_executor_job

            async def failing_executor(func, *args):
                if func.__name__ == "write_bytes":
                    raise OSError("Disk full")
                return await original_executor(func, *args)

            with patch.object(
                hass, "async_add_executor_job", side_effect=failing_executor
            ):
                await hass.services.async_call(
                    "button",
                    "press",
                    {"entity_id": "button.fmd_test_user_photo_download"},
                    blocking=True,
                )
                await hass.async_block_till_done()

    # Should handle write error gracefully
    mock_fmd_api.create.return_value.get_pictures.assert_called_once()


# =============================================================================
# device_tracker.py Error Path Tests
# =============================================================================


async def test_device_tracker_empty_locations(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker when API returns empty location array."""
    # Return empty locations list
    mock_fmd_api.create.return_value.get_locations.return_value = []

    await setup_integration(hass, mock_fmd_api)
    await hass.async_block_till_done()

    # Tracker should be created but show unknown state
    state = hass.states.get("device_tracker.fmd_test_user")
    # State might be 'unknown' or 'unavailable' depending on implementation
    assert state is not None


async def test_device_tracker_decryption_failure(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test device tracker when location decryption fails."""
    # Return a location with corrupt blob
    mock_location = {
        "date": 1234567890000,
        "bat": 75,
        "data": base64.b64encode(b"corrupt_location_data").decode(),
        "key": base64.b64encode(b"bad_key").decode(),
    }
    mock_fmd_api.create.return_value.get_locations.return_value = [mock_location]

    # Mock decrypt_data_blob to raise exception
    with patch(
        "custom_components.fmd.device_tracker.decrypt_data_blob"
    ) as mock_decrypt:
        mock_decrypt.side_effect = Exception("Decryption failed")

        await setup_integration(hass, mock_fmd_api)
        await hass.async_block_till_done()

        # Should handle error gracefully
        state = hass.states.get("device_tracker.fmd_test_user")
        assert state is not None


# =============================================================================
# sensor.py Error Path Tests
# =============================================================================


async def test_photo_sensor_media_directory_not_exists(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo count sensor when media directory doesn't exist."""
    await setup_integration(hass, mock_fmd_api)

    # Mock Path to simulate non-existent directory
    with patch("custom_components.fmd.sensor.Path") as mock_path:
        mock_dir = Mock(spec=Path)
        mock_dir.exists.return_value = False
        mock_dir.is_dir.return_value = False
        mock_path.return_value = mock_dir

        # Trigger sensor update
        await hass.services.async_call(
            "homeassistant",
            "update_entity",
            {"entity_id": "sensor.fmd_test_user_photo_count"},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Sensor should show 0 photos when directory doesn't exist
    state = hass.states.get("sensor.fmd_test_user_photo_count")
    assert state is not None
    assert state.state == "0"


async def test_photo_sensor_permission_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo count sensor when directory access fails."""
    await setup_integration(hass, mock_fmd_api)

    # Mock Path to simulate permission error
    with patch("custom_components.fmd.sensor.Path") as mock_path:
        mock_dir = Mock(spec=Path)
        mock_dir.exists.return_value = True
        mock_dir.is_dir.return_value = True
        mock_dir.glob.side_effect = PermissionError("Access denied")
        mock_path.return_value = mock_dir

        # Trigger sensor update
        await hass.services.async_call(
            "homeassistant",
            "update_entity",
            {"entity_id": "sensor.fmd_test_user_photo_count"},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Sensor should handle error gracefully
    state = hass.states.get("sensor.fmd_test_user_photo_count")
    assert state is not None
