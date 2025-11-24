"""Test FMD button coverage."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from conftest import setup_integration
from fmd_api import AuthenticationError, FmdApiException, OperationError
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.fmd.const import DOMAIN


async def test_ring_button_home_assistant_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test ring button re-raises HomeAssistantError."""
    await setup_integration(hass, mock_fmd_api)

    # Mock send_command to raise HomeAssistantError
    tracker = hass.data[DOMAIN]["test_entry_id"]["tracker"]
    tracker.api.send_command.side_effect = HomeAssistantError("Test Error")

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_volume_ring_device"},
            blocking=True,
        )


async def test_lock_button_exceptions(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test lock button handles exceptions gracefully (logs but doesn't raise)."""
    await setup_integration(hass, mock_fmd_api)

    # We need to patch 'custom_components.fmd.button.Device' because it's instantiated inside async_press
    with patch("custom_components.fmd.button.Device") as mock_device_cls:
        mock_device = mock_device_cls.return_value

        # Test AuthenticationError
        mock_device.lock.side_effect = AuthenticationError("Auth Error")
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_lock_device"},
            blocking=True,
        )

        # Test OperationError
        mock_device.lock.side_effect = OperationError("Op Error")
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_lock_device"},
            blocking=True,
        )

        # Test FmdApiException
        mock_device.lock.side_effect = FmdApiException("API Error")
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_lock_device"},
            blocking=True,
        )


async def test_download_photos_cleanup_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test photo cleanup handles deletion errors."""
    await setup_integration(hass, mock_fmd_api)

    # Mock the switch entity to return True for is_on
    mock_switch = MagicMock()
    mock_switch.is_on = True
    hass.data[DOMAIN]["test_entry_id"]["photo_auto_cleanup_switch"] = mock_switch

    # Mock max photos number to 1 so we trigger cleanup with 2 photos
    mock_number = MagicMock()
    mock_number.native_value = 1
    hass.data[DOMAIN]["test_entry_id"]["max_photos_number"] = mock_number

    # Mock Device to return blobs
    with patch("custom_components.fmd.button.Device") as mock_device_cls:
        mock_device = mock_device_cls.return_value
        # Make async methods return futures/be async
        mock_device.get_picture_blobs = AsyncMock(return_value=[b"1", b"2"])

        mock_photo_result = MagicMock()
        mock_photo_result.data = b"image_data"
        mock_photo_result.mime_type = "image/jpeg"
        mock_photo_result.timestamp = None
        mock_device.decode_picture = AsyncMock(return_value=mock_photo_result)

        # Mock Path
        with patch("custom_components.fmd.button.Path") as mock_path_cls:
            mock_base = MagicMock()
            mock_base.exists.return_value = True
            mock_base.is_dir.return_value = True
            mock_path_cls.return_value = mock_base

            mock_fmd = MagicMock()
            mock_base.__truediv__.return_value = mock_fmd

            mock_media_dir = MagicMock()
            mock_fmd.__truediv__.return_value = mock_media_dir

            # Create mock photos
            mock_photo1 = MagicMock()
            mock_photo1.stat.return_value.st_mtime = 100
            mock_photo1.name = "photo1.jpg"
            # unlink raises exception
            mock_photo1.unlink.side_effect = Exception("Delete failed")

            mock_photo2 = MagicMock()
            mock_photo2.stat.return_value.st_mtime = 200
            mock_photo2.name = "photo2.jpg"

            # glob returns list of photos
            mock_media_dir.glob.return_value = [mock_photo1, mock_photo2]

            # Trigger download
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_photo_download"},
                blocking=True,
            )

            # Verify unlink was called
            mock_photo1.unlink.assert_called()


async def test_download_photos_cleanup_error_logs(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Test photo cleanup logs error when deletion fails."""
    await setup_integration(hass, mock_fmd_api)

    # Mock the switch entity to return True for is_on
    mock_switch = MagicMock()
    mock_switch.is_on = True
    hass.data[DOMAIN]["test_entry_id"]["photo_auto_cleanup_switch"] = mock_switch

    # Mock max photos number to 1 so we trigger cleanup with 2 photos
    mock_number = MagicMock()
    mock_number.native_value = 1
    hass.data[DOMAIN]["test_entry_id"]["max_photos_number"] = mock_number

    # Mock Device to return blobs
    with patch("custom_components.fmd.button.Device") as mock_device_cls:
        mock_device = mock_device_cls.return_value
        mock_device.get_picture_blobs = AsyncMock(return_value=[b"1", b"2"])

        mock_photo_result = MagicMock()
        mock_photo_result.data = b"image_data"
        mock_photo_result.mime_type = "image/jpeg"
        mock_photo_result.timestamp = None
        mock_device.decode_picture = AsyncMock(return_value=mock_photo_result)

        # Mock Path
        with patch("custom_components.fmd.button.Path") as mock_path_cls:
            mock_base = MagicMock()
            mock_base.exists.return_value = True
            mock_base.is_dir.return_value = True
            mock_path_cls.return_value = mock_base

            mock_fmd = MagicMock()
            mock_base.__truediv__.return_value = mock_fmd

            mock_media_dir = MagicMock()
            mock_fmd.__truediv__.return_value = mock_media_dir

            # Create mock photos
            mock_photo1 = MagicMock()
            mock_photo1.stat.return_value.st_mtime = 100
            mock_photo1.name = "photo1.jpg"
            # unlink raises exception
            mock_photo1.unlink.side_effect = Exception("Delete failed")

            mock_photo2 = MagicMock()
            mock_photo2.stat.return_value.st_mtime = 200
            mock_photo2.name = "photo2.jpg"

            # glob returns list of photos
            mock_media_dir.glob.return_value = [mock_photo1, mock_photo2]

            # Trigger download
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_photo_download"},
                blocking=True,
            )

            # Verify error log
            assert "Failed to delete photo photo1.jpg: Delete failed" in caplog.text


async def test_wipe_button_auth_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test wipe button handles AuthenticationError."""
    await setup_integration(hass, mock_fmd_api)

    # Enable safety switch
    hass.states.async_set("switch.fmd_test_user_wipe_safety_switch", "on")

    # Mock PIN text entity
    mock_text = MagicMock()
    mock_text.native_value = "1234"
    hass.data[DOMAIN]["test_entry_id"]["wipe_pin_text"] = mock_text

    # Patch Device
    with patch("custom_components.fmd.button.Device") as mock_device_cls:
        mock_device = mock_device_cls.return_value
        mock_device.wipe.side_effect = AuthenticationError("Auth Fail")

        with pytest.raises(HomeAssistantError, match="Authentication failed"):
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_wipe_execute"},
                blocking=True,
            )


async def test_wipe_button_fmd_api_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Test wipe button handles FmdApiException."""
    await setup_integration(hass, mock_fmd_api)

    # Enable safety switch
    hass.states.async_set("switch.fmd_test_user_wipe_safety_switch", "on")

    # Mock PIN text entity
    mock_text = MagicMock()
    mock_text.native_value = "1234"
    hass.data[DOMAIN]["test_entry_id"]["wipe_pin_text"] = mock_text

    # Patch Device
    with patch("custom_components.fmd.button.Device") as mock_device_cls:
        mock_device = mock_device_cls.return_value
        mock_device.wipe.side_effect = FmdApiException("API Fail")

        with pytest.raises(HomeAssistantError, match="Wipe command failed"):
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_wipe_execute"},
                blocking=True,
            )

        assert "FMD API error: API Fail" in caplog.text
