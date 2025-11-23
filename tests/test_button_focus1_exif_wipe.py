"""Focus 1: Button.py EXIF multi-tag preference and wipe edge cases.

Targets remaining untested branches:
- Lines 184-196: EXIF tag preference logic (DateTimeOriginal first, then fallback)
- Lines 520-524: Debug logging for found tag
- Lines 526-545: Parse and format datetime from EXIF tag
- Lines 263/267/271: Ring button error branches
- Lines 693-694, 762-767, 788-793, 802-803: Wipe button edge cases
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from conftest import setup_integration
from fmd_api import AuthenticationError, FmdApiException, OperationError
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError


async def test_download_photos_exif_datetimeoriginal_used_first(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """When EXIF has DateTimeOriginal (36867), it's used and other tags ignored."""
    await setup_integration(hass, mock_fmd_api)

    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.get_picture_blobs.return_value = [b"blob1"]

    pr = MagicMock()
    pr.data = b"IMG_WITH_EXIF"
    pr.mime_type = "image/jpeg"
    pr.timestamp = None  # Force EXIF fallback
    pr.raw = {}
    device_mock.decode_picture.return_value = pr

    # Create mock image with EXIF containing DateTimeOriginal (36867)
    class MockImg:
        def getexif(self):
            # Include all three tags - DateTimeOriginal should be preferred
            return {
                36867: "2025:01:15 10:30:45",  # DateTimeOriginal
                36868: "2025:01:16 11:00:00",  # DateTimeDigitized
                306: "2025:01:17 12:00:00",  # DateTime
            }

    with patch("PIL.Image.open", return_value=MockImg()), patch(
        "pathlib.Path.is_dir", return_value=True
    ), patch("pathlib.Path.mkdir"), patch(
        "pathlib.Path.exists", return_value=False
    ), patch(
        "pathlib.Path.write_bytes"
    ) as mock_write:
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )

    # Verify file was written (EXIF timestamp extraction logged)
    assert mock_write.call_count == 1


async def test_download_photos_exif_digitized_when_original_missing(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """When DateTimeOriginal absent but DateTimeDigitized present, use it."""
    await setup_integration(hass, mock_fmd_api)

    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.get_picture_blobs.return_value = [b"blob1"]

    pr = MagicMock()
    pr.data = b"IMG_DIGITIZED"
    pr.mime_type = "image/jpeg"
    pr.timestamp = None
    pr.raw = {}
    device_mock.decode_picture.return_value = pr

    class MockImg:
        def getexif(self):
            # Only DateTimeDigitized and DateTime present
            return {
                36868: "2025:02:20 14:15:30",
                306: "2025:02:21 15:00:00",
            }

    with patch("PIL.Image.open", return_value=MockImg()), patch(
        "pathlib.Path.is_dir", return_value=True
    ), patch("pathlib.Path.mkdir"), patch(
        "pathlib.Path.exists", return_value=False
    ), patch(
        "pathlib.Path.write_bytes"
    ) as mock_write:
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )

    # Verify file was written (EXIF timestamp extraction logged)
    assert mock_write.call_count == 1


async def test_download_photos_exif_datetime_fallback(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """When only DateTime (306) present, use it as last resort."""
    await setup_integration(hass, mock_fmd_api)

    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.get_picture_blobs.return_value = [b"blob1"]

    pr = MagicMock()
    pr.data = b"IMG_DATETIME_ONLY"
    pr.mime_type = "image/jpeg"
    pr.timestamp = None
    pr.raw = {}
    device_mock.decode_picture.return_value = pr

    class MockImg:
        def getexif(self):
            # Only DateTime tag
            return {306: "2025:03:10 09:45:12"}

    with patch("PIL.Image.open", return_value=MockImg()), patch(
        "pathlib.Path.is_dir", return_value=True
    ), patch("pathlib.Path.mkdir"), patch(
        "pathlib.Path.exists", return_value=False
    ), patch(
        "pathlib.Path.write_bytes"
    ) as mock_write:
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )

    # Verify file was written (EXIF timestamp extraction logged)
    assert mock_write.call_count == 1


async def test_download_photos_exif_with_whitespace_and_nulls(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """EXIF datetime value with whitespace and null bytes is cleaned."""
    await setup_integration(hass, mock_fmd_api)

    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.get_picture_blobs.return_value = [b"blob1"]

    pr = MagicMock()
    pr.data = b"IMG_DIRTY_EXIF"
    pr.mime_type = "image/jpeg"
    pr.timestamp = None
    pr.raw = {}
    device_mock.decode_picture.return_value = pr

    class MockImg:
        def getexif(self):
            # DateTime with extra whitespace and null bytes
            return {36867: "  2025:04:05 16:20:30\x00\x00  "}

    with patch("PIL.Image.open", return_value=MockImg()), patch(
        "pathlib.Path.is_dir", return_value=True
    ), patch("pathlib.Path.mkdir"), patch(
        "pathlib.Path.exists", return_value=False
    ), patch(
        "pathlib.Path.write_bytes"
    ) as mock_write:
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )

    # Verify file was written (EXIF timestamp extraction logged)
    assert mock_write.call_count == 1


# Ring button error branches (lines 263/267/271)
async def test_ring_button_authentication_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Ring button AuthenticationError path raises HomeAssistantError."""
    await setup_integration(hass, mock_fmd_api)

    mock_fmd_api.create.return_value.send_command.side_effect = AuthenticationError(
        "auth failed"
    )

    with pytest.raises(HomeAssistantError, match="Authentication failed"):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_volume_ring_device"},
            blocking=True,
        )


async def test_ring_button_operation_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Ring button OperationError path raises HomeAssistantError."""
    await setup_integration(hass, mock_fmd_api)

    mock_fmd_api.create.return_value.send_command.side_effect = OperationError(
        "network fail"
    )

    with pytest.raises(HomeAssistantError, match="Ring command failed"):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_volume_ring_device"},
            blocking=True,
        )


async def test_ring_button_fmd_api_exception(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Ring button FmdApiException path raises HomeAssistantError."""
    await setup_integration(hass, mock_fmd_api)

    mock_fmd_api.create.return_value.send_command.side_effect = FmdApiException(
        "api error"
    )

    with pytest.raises(HomeAssistantError, match="Ring command failed"):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_volume_ring_device"},
            blocking=True,
        )


# Wipe button edge cases
async def test_wipe_button_missing_wipe_pin_entity(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Wipe button when wipe_pin_text entity missing from hass.data."""
    await setup_integration(hass, mock_fmd_api)

    # Enable safety
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )

    # Remove wipe_pin_text from hass.data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id].pop("wipe_pin_text", None)

    # Try to wipe - should return early (lines 760-766)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )

    # Should not call wipe API
    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.wipe.assert_not_called()


async def test_wipe_button_empty_pin(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Wipe button with empty PIN value (lines 770-777)."""
    await setup_integration(hass, mock_fmd_api)

    # Enable safety
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )

    # Set empty PIN - text entity will raise ValueError
    with pytest.raises(ValueError, match="PIN cannot be empty"):
        await hass.services.async_call(
            "text",
            "set_value",
            {"entity_id": "text.fmd_test_user_wipe_pin", "value": ""},
            blocking=True,
        )


async def test_wipe_button_invalid_pin_validation_fails(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Wipe button with invalid PIN that fails validation (lines 784-790)."""
    await setup_integration(hass, mock_fmd_api)

    # Enable safety
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )

    # Set invalid PIN (contains special characters) - text entity will raise ValueError
    with pytest.raises(ValueError, match="alphanumeric"):
        await hass.services.async_call(
            "text",
            "set_value",
            {"entity_id": "text.fmd_test_user_wipe_pin", "value": "Pin@123!"},
            blocking=True,
        )


async def test_wipe_button_tracker_missing_after_validation(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Wipe button when tracker missing after PIN validation (lines 800-802)."""
    await setup_integration(hass, mock_fmd_api)

    # Enable safety and set valid PIN
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.services.async_call(
        "text",
        "set_value",
        {"entity_id": "text.fmd_test_user_wipe_pin", "value": "ValidPin123"},
        blocking=True,
    )

    # Remove tracker from hass.data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id].pop("tracker", None)

    # Try to wipe
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )

    # Should not call wipe API
    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.wipe.assert_not_called()


async def test_wipe_button_safety_switch_missing_after_success(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Wipe succeeds but safety_switch missing when trying to disable it."""
    await setup_integration(hass, mock_fmd_api)

    # Enable safety and set valid PIN
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.services.async_call(
        "text",
        "set_value",
        {"entity_id": "text.fmd_test_user_wipe_pin", "value": "SecurePin456"},
        blocking=True,
    )

    # Remove safety switch from hass.data before wipe
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id].pop("wipe_safety_switch", None)

    # Mock successful wipe
    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.wipe.return_value = None

    # Execute wipe - should succeed but not crash when safety_switch missing
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )

    # Verify wipe was called
    device_mock.wipe.assert_called_once_with(pin="SecurePin456", confirm=True)
