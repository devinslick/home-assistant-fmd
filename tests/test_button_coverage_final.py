"""Final coverage tests for button entities."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from conftest import setup_integration
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError


def get_button_entity(hass: HomeAssistant, entity_id: str):
    """Get a button entity instance by its entity ID."""
    component = hass.data.get("entity_components", {}).get("button")
    if component:
        for entity in component.entities:
            if entity.entity_id == entity_id:
                return entity
    raise ValueError(f"Entity {entity_id} not found")


async def test_ring_button_homeassistant_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test ring button re-raises HomeAssistantError."""
    await setup_integration(hass, mock_fmd_api)

    # Get the button instance
    button = get_button_entity(hass, "button.fmd_test_user_volume_ring_device")

    # Mock send_command to raise HomeAssistantError
    # We need to patch the api instance on the tracker
    entry_id = list(hass.data["fmd"].keys())[0]
    tracker = hass.data["fmd"][entry_id]["tracker"]
    tracker.api.send_command.side_effect = HomeAssistantError("Test error")

    # Press the button and expect HomeAssistantError
    with pytest.raises(HomeAssistantError, match="Test error"):
        await button.async_press()


async def test_cleanup_old_photos_no_cleanup_needed(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, tmp_path: Any
) -> None:
    """Test cleanup skips when photo count is within limit."""
    await setup_integration(hass, mock_fmd_api)

    # Get the button instance
    button = get_button_entity(hass, "button.fmd_test_user_photo_download")

    # Enable auto cleanup switch
    entry_id = list(hass.data["fmd"].keys())[0]
    cleanup_switch = hass.data["fmd"][entry_id]["photo_auto_cleanup_switch"]
    await cleanup_switch.async_turn_on()

    # Set max photos to 10
    max_photos_entity = hass.data["fmd"][entry_id]["max_photos_number"]
    await max_photos_entity.async_set_native_value(10)

    # Mock Device class to return 1 photo
    with patch("custom_components.fmd.button.Device") as mock_device_cls:
        mock_device = mock_device_cls.return_value
        mock_device.get_picture_blobs = AsyncMock(return_value=["blob1"])

        # Mock decode_picture
        from datetime import datetime

        mock_photo_result = MagicMock()
        mock_photo_result.data = b"fake_image_data"
        mock_photo_result.mime_type = "image/jpeg"
        mock_photo_result.timestamp = datetime.now()
        mock_device.decode_picture = AsyncMock(return_value=mock_photo_result)

        # Patch hass.config.path to return tmp_path
        with patch.object(hass.config, "path", return_value=str(tmp_path)):
            # Patch _LOGGER to verify the debug message
            with patch("custom_components.fmd.button._LOGGER") as mock_logger:
                await button.async_press()

                # Verify debug message was logged
                # We need to check if any call matches the pattern because there are many debug logs
                found = False
                for call in mock_logger.debug.call_args_list:
                    args = call.args
                    if args and "no cleanup needed" in args[0]:
                        found = True
                        break

                assert found, "Cleanup debug message not found"


async def test_cleanup_old_photos_exception(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, tmp_path: Any
) -> None:
    """Test exception handling in _cleanup_old_photos."""
    await setup_integration(hass, mock_fmd_api)

    # Get the button instance
    button = get_button_entity(hass, "button.fmd_test_user_photo_download")

    # Enable auto cleanup switch
    entry_id = list(hass.data["fmd"].keys())[0]
    cleanup_switch = hass.data["fmd"][entry_id]["photo_auto_cleanup_switch"]
    await cleanup_switch.async_turn_on()

    # Mock Device class to return 1 photo
    with patch("custom_components.fmd.button.Device") as mock_device_cls:
        mock_device = mock_device_cls.return_value
        mock_device.get_picture_blobs = AsyncMock(return_value=["blob1"])

        # Mock decode_picture
        from datetime import datetime

        mock_photo_result = MagicMock()
        mock_photo_result.data = b"fake_image_data"
        mock_photo_result.mime_type = "image/jpeg"
        mock_photo_result.timestamp = datetime.now()
        mock_device.decode_picture = AsyncMock(return_value=mock_photo_result)

        # Patch hass.config.path to return tmp_path
        with patch.object(hass.config, "path", return_value=str(tmp_path)):
            # Mock media_dir.glob to raise an exception
            # We need to patch Path.glob, but since we don't know the exact Path object,
            # we can patch the method on the class or use a side_effect on the mock if we could inject it.
            # However, _cleanup_old_photos is called internally.
            # Let's patch pathlib.Path.glob
            with patch("pathlib.Path.glob", side_effect=Exception("Filesystem error")):
                with patch("custom_components.fmd.button._LOGGER") as mock_logger:
                    await button.async_press()

                    # Verify error was logged
                    found = False
                    for call in mock_logger.error.call_args_list:
                        if "Error during photo cleanup" in call[0][0]:
                            found = True
                            break
                    assert found


async def test_wipe_button_empty_pin(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test wipe button blocks when PIN is empty."""
    await setup_integration(hass, mock_fmd_api)

    # Get the button instance
    button = get_button_entity(hass, "button.fmd_test_user_wipe_execute")

    # Enable safety switch
    entry_id = list(hass.data["fmd"].keys())[0]
    safety_switch = hass.data["fmd"][entry_id]["wipe_safety_switch"]
    await safety_switch.async_turn_on()

    # Ensure PIN is empty (it should be by default)
    pin_entity = hass.data["fmd"][entry_id]["wipe_pin_text"]
    assert pin_entity.native_value == ""

    # Press the button
    with patch("custom_components.fmd.button._LOGGER") as mock_logger:
        await button.async_press()

        # Verify error logs
        assert mock_logger.error.call_count >= 3
        mock_logger.error.assert_any_call("⚠️ Wipe PIN is not set")


async def test_wipe_button_missing_pin_entity(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test wipe button blocks when PIN entity is missing."""
    await setup_integration(hass, mock_fmd_api)

    # Get the button instance
    button = get_button_entity(hass, "button.fmd_test_user_wipe_execute")

    # Enable safety switch
    entry_id = list(hass.data["fmd"].keys())[0]
    safety_switch = hass.data["fmd"][entry_id]["wipe_safety_switch"]
    await safety_switch.async_turn_on()

    # Remove the PIN entity from hass.data
    del hass.data["fmd"][entry_id]["wipe_pin_text"]

    # Press the button
    with patch("custom_components.fmd.button._LOGGER") as mock_logger:
        await button.async_press()

        # Verify error logs
        assert mock_logger.error.call_count >= 3
        mock_logger.error.assert_any_call("⚠️ Wipe PIN entity not found")


async def test_wipe_button_invalid_pin(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test wipe button with invalid PIN format."""
    await setup_integration(hass, mock_fmd_api)

    # Get the button instance
    button = get_button_entity(hass, "button.fmd_test_user_wipe_execute")

    # Enable safety switch
    entry_id = list(hass.data["fmd"].keys())[0]
    safety_switch = hass.data["fmd"][entry_id]["wipe_safety_switch"]
    await safety_switch.async_turn_on()

    # Set invalid PIN
    pin_entity = hass.data["fmd"][entry_id]["wipe_pin_text"]
    # We need to bypass the validation in async_set_value to test the button's validation
    # So we set the internal attribute directly
    pin_entity._attr_native_value = "invalid pin with spaces"
    pin_entity.async_write_ha_state()

    # Press the button
    with patch("custom_components.fmd.button._LOGGER") as mock_logger:
        await button.async_press()

        # Verify error logs
        found = False
        for call in mock_logger.error.call_args_list:
            if "Invalid wipe PIN" in call[0][0]:
                found = True
                break
        assert found
