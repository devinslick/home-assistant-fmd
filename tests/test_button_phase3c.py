"""Phase 3c comprehensive button tests - targeting edge cases and error paths."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from conftest import setup_integration
from fmd_api import OperationError
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError


async def test_location_update_button_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test location update button when tracker not found in hass data."""
    await setup_integration(hass, mock_fmd_api)

    # Simulate tracker being removed from hass data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id]["tracker"] = None

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_location_update"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should not raise and API should not be called
    mock_fmd_api.create.return_value.request_location.assert_not_called()


async def test_location_update_button_request_fails(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test location update button when request_location fails."""
    mock_fmd_api.create.return_value.request_location.return_value = False

    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_location_update"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_fmd_api.create.return_value.request_location.assert_called_once()


async def test_location_update_button_api_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test location update button when API raises exception."""
    mock_fmd_api.create.return_value.request_location.side_effect = Exception(
        "API Error"
    )

    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_location_update"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should handle exception gracefully
    mock_fmd_api.create.return_value.request_location.assert_called_once()


async def test_location_update_button_select_entity_missing(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test location update button when select entity for location source missing."""
    mock_fmd_api.create.return_value.request_location.return_value = True

    await setup_integration(hass, mock_fmd_api)

    # Remove the location source select entity state
    entity_id = "select.fmd_test_user_location_source"
    hass.states.async_remove(entity_id)

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_location_update"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should still call with default provider
    mock_fmd_api.create.return_value.request_location.assert_called()


async def test_ring_button_api_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ring button when send_command raises exception."""
    import pytest
    from homeassistant.exceptions import HomeAssistantError

    mock_fmd_api.create.return_value.send_command.side_effect = Exception("API Error")

    await setup_integration(hass, mock_fmd_api)

    # Should raise HomeAssistantError wrapping the API error
    with pytest.raises(HomeAssistantError, match="Ring command failed"):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_volume_ring_device"},
            blocking=True,
        )
        await hass.async_block_till_done()

    mock_fmd_api.create.return_value.send_command.assert_called_once_with("ring")


async def test_ring_button_command_fails(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ring button when send_command returns false - should just log warning."""
    mock_fmd_api.create.return_value.send_command.return_value = False

    await setup_integration(hass, mock_fmd_api)

    # Should not raise, just log warning when command returns False
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_volume_ring_device"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_fmd_api.create.return_value.send_command.assert_called_once_with("ring")


async def test_lock_button_api_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test lock button when device.lock() raises exception."""
    import pytest
    from homeassistant.exceptions import HomeAssistantError

    await setup_integration(hass, mock_fmd_api)

    # Get device mock and configure to fail
    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.lock.side_effect = RuntimeError("API Error")

    # Should raise HomeAssistantError wrapping the API error
    with pytest.raises(HomeAssistantError, match="Lock command failed"):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_lock_device"},
            blocking=True,
        )
        await hass.async_block_till_done()

    device_mock.lock.assert_called_once()


async def test_capture_front_camera_button_api_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test front camera button when take_picture raises exception."""
    await setup_integration(hass, mock_fmd_api)

    # Get the actual API instance and configure mock to fail
    api_instance = mock_fmd_api.create.return_value

    # Reset the mock call count before reconfiguring
    api_instance.take_picture.reset_mock()
    api_instance.take_picture.side_effect = Exception("API Error")

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_capture_front"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should attempt to call take_picture even though it fails
    api_instance.take_picture.assert_called()


async def test_capture_rear_camera_button_api_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test rear camera button when take_picture raises exception."""
    await setup_integration(hass, mock_fmd_api)

    # Get the actual API instance and configure mock to fail
    api_instance = mock_fmd_api.create.return_value

    # Reset the mock call count before reconfiguring
    api_instance.take_picture.reset_mock()
    api_instance.take_picture.side_effect = Exception("API Error")

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_capture_rear"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should attempt to call take_picture even though it fails
    api_instance.take_picture.assert_called()


async def test_photo_download_button_get_pictures_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download button when get_picture_blobs raises exception (new API)."""
    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.get_picture_blobs.side_effect = Exception("API Error")

    await setup_integration(hass, mock_fmd_api)

    with pytest.raises(Exception, match="API Error"):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )
        await hass.async_block_till_done()

    device_mock.get_picture_blobs.assert_called()


async def test_photo_download_button_media_dir_missing(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download button with missing media directory (new API)."""
    await setup_integration(hass, mock_fmd_api)

    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.get_picture_blobs.return_value = [b"encrypted_blob"]
    from unittest.mock import MagicMock

    photo_result = MagicMock()
    photo_result.data = b"fake_photo_data"
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = None
    photo_result.raw = {}
    device_mock.decode_picture.return_value = photo_result

    # Mock Path operations to simulate directory creation
    with patch("pathlib.Path.mkdir"):
        with patch("pathlib.Path.exists", return_value=False):
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_photo_download"},
                blocking=True,
            )
            await hass.async_block_till_done()

    device_mock.get_picture_blobs.assert_called()


async def test_wipe_button_api_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe button when device.wipe raises an API error (new API)."""
    await setup_integration(hass, mock_fmd_api)

    # Set PIN required for wipe
    await hass.services.async_call(
        "text",
        "set_value",
        {"entity_id": "text.fmd_test_user_wipe_pin", "value": "Pin123"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Enable safety switch first
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Configure device.wipe to raise OperationError
    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.wipe.side_effect = OperationError("API Error")

    # Expect HomeAssistantError wrapping the failure
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_wipe_execute"},
            blocking=True,
        )
        await hass.async_block_till_done()

    device_mock.wipe.assert_called_once_with(pin="Pin123", confirm=True)
