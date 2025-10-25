"""Phase 3c comprehensive button tests - targeting edge cases and error paths."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from conftest import setup_integration
from homeassistant.core import HomeAssistant


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
    mock_fmd_api.create.return_value.send_command.side_effect = Exception("API Error")

    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_volume_ring_device"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should handle exception gracefully
    mock_fmd_api.create.return_value.send_command.assert_called_once_with("ring")


async def test_ring_button_command_fails(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ring button when send_command returns false."""
    mock_fmd_api.create.return_value.send_command.return_value = False

    await setup_integration(hass, mock_fmd_api)

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
    """Test lock button when send_command raises exception."""
    await setup_integration(hass, mock_fmd_api)

    # Get the actual API instance and configure mock to fail
    api_instance = mock_fmd_api.create.return_value

    # Reset the mock call count before reconfiguring
    api_instance.send_command.reset_mock()
    api_instance.send_command.side_effect = Exception("API Error")

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_lock_device"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should attempt to call send_command even though it fails
    api_instance.send_command.assert_called()


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
    """Test photo download button when get_pictures raises exception."""
    mock_fmd_api.create.return_value.get_pictures.side_effect = Exception("API Error")

    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_download"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should attempt to get pictures even if it fails
    mock_fmd_api.create.return_value.get_pictures.assert_called()


async def test_photo_download_button_media_dir_missing(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download button with missing media directory."""
    mock_fmd_api.create.return_value.get_pictures.return_value = [b"fake_photo_data"]

    await setup_integration(hass, mock_fmd_api)

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

    mock_fmd_api.create.return_value.get_pictures.assert_called()


async def test_wipe_button_api_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe button when send_command raises exception."""
    mock_fmd_api.create.return_value.send_command.side_effect = Exception("API Error")

    await setup_integration(hass, mock_fmd_api)

    # Enable safety switch first
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should attempt delete command even if it fails
    mock_fmd_api.create.return_value.send_command.assert_called_with("delete")
