"""Additional branch coverage for FMD button entities.

Targets remaining untested branches in `button.py`:
 - Photo download outer exception handlers (AuthenticationError, OperationError, FmdApiException, generic)
 - Media directory creation failure early-return path
 - Duplicate photo detection (skip second)
 - EXIF extraction failure (Image.open raises)
 - EXIF absence (getexif returns empty) and timestamp fallback
 - Missing photo count sensor warning path
 - Wipe device error branches (AuthenticationError, OperationError, FmdApiException, generic)
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from conftest import setup_integration
from fmd_api import AuthenticationError, FmdApiException, OperationError
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError


async def _prepare_photo_download_common(hass: HomeAssistant, mock_fmd_api: AsyncMock):
    """Helper to setup integration and return device mock for picture API."""
    await setup_integration(hass, mock_fmd_api)
    return mock_fmd_api.create.return_value.device.return_value


@pytest.mark.parametrize(
    "exc_cls, msg_contains",
    [
        (AuthenticationError, "Authentication failed"),
        (OperationError, "Photo download failed"),
        (FmdApiException, "Photo download failed"),
    ],
)
async def test_download_photos_outer_known_errors(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, exc_cls, msg_contains
) -> None:
    """device.get_picture_blobs raising specific exceptions maps to HomeAssistantError paths."""
    device_mock = await _prepare_photo_download_common(hass, mock_fmd_api)
    device_mock.get_picture_blobs.side_effect = exc_cls("boom")

    with pytest.raises(HomeAssistantError, match=msg_contains):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )


async def test_download_photos_outer_generic_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Generic unexpected exception path maps to HomeAssistantError."""
    device_mock = await _prepare_photo_download_common(hass, mock_fmd_api)
    device_mock.get_picture_blobs.side_effect = RuntimeError("unexpected")

    with pytest.raises(HomeAssistantError, match="Photo download failed"):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )


async def test_download_photos_media_dir_creation_failure(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Failure during media directory creation returns early (no decode calls)."""
    device_mock = await _prepare_photo_download_common(hass, mock_fmd_api)
    device_mock.get_picture_blobs.return_value = [b"blob1"]
    # Provide a valid PhotoResult so if directory creation passed we'd decode
    pr = MagicMock()
    pr.data = b"imgdata"
    pr.mime_type = "image/jpeg"
    pr.timestamp = None
    pr.raw = {}
    device_mock.decode_picture.return_value = pr

    with patch("pathlib.Path.is_dir", return_value=True), patch(
        "pathlib.Path.mkdir", side_effect=OSError("mkdir fail")
    ):
        # Sensor should still update with count when early returning? (code returns before sensor)
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )

    # decode_picture never called due to directory creation failure
    device_mock.decode_picture.assert_not_called()


async def test_download_photos_duplicate_detection(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Second identical photo is skipped as duplicate (exists())."""
    device_mock = await _prepare_photo_download_common(hass, mock_fmd_api)
    device_mock.get_picture_blobs.return_value = [b"blob1", b"blob2"]

    # Two PhotoResults with identical data -> same hash
    pr1 = MagicMock()
    pr1.data = b"IDENTICAL_DATA"
    pr1.mime_type = "image/jpeg"
    pr1.timestamp = None
    pr1.raw = {}
    pr2 = MagicMock()
    pr2.data = b"IDENTICAL_DATA"
    pr2.mime_type = "image/jpeg"
    pr2.timestamp = None
    pr2.raw = {}
    device_mock.decode_picture.side_effect = [pr1, pr2]

    # exists() should return False for first file creation, True for second (duplicate)
    first_call = {"done": False}

    def exists_side_effect(self):
        # Directories -> True, files containing photo_ -> first False then True
        if "photo_" not in str(self):
            return True
        if not first_call["done"]:
            first_call["done"] = True
            return False
        return True

    with patch("pathlib.Path.is_dir", return_value=True), patch(
        "pathlib.Path.mkdir"
    ), patch("pathlib.Path.exists", exists_side_effect), patch(
        "pathlib.Path.write_bytes"
    ) as mock_write:
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )

    # Only first photo written
    assert mock_write.call_count == 1


async def test_download_photos_exif_open_failure(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """EXIF extraction failure (Image.open raises) uses hash-only filename path."""
    device_mock = await _prepare_photo_download_common(hass, mock_fmd_api)
    device_mock.get_picture_blobs.return_value = [b"blob1"]
    pr = MagicMock()
    pr.data = b"NO_EXIF_IMAGE"
    pr.mime_type = "image/jpeg"
    pr.timestamp = None
    pr.raw = {}
    device_mock.decode_picture.return_value = pr

    with patch("PIL.Image.open", side_effect=RuntimeError("exif boom")), patch(
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

    # File written despite EXIF failure
    assert mock_write.call_count == 1


async def test_download_photos_exif_no_data(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Image has no EXIF (getexif returns empty) triggers warning path."""
    device_mock = await _prepare_photo_download_common(hass, mock_fmd_api)
    device_mock.get_picture_blobs.return_value = [b"blob1"]
    pr = MagicMock()
    pr.data = b"NO_EXIF"
    pr.mime_type = "image/jpeg"
    pr.timestamp = None
    pr.raw = {}
    device_mock.decode_picture.return_value = pr

    class DummyImg:
        def getexif(self):
            return {}

    with patch("PIL.Image.open", return_value=DummyImg()), patch(
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

    assert mock_write.call_count == 1


async def test_download_photos_missing_sensor(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Warn path when photo_count_sensor is missing from hass.data mapping."""
    device_mock = await _prepare_photo_download_common(hass, mock_fmd_api)
    device_mock.get_picture_blobs.return_value = [b"blob1"]
    pr = MagicMock()
    pr.data = b"IMG"
    pr.mime_type = "image/jpeg"
    pr.timestamp = None
    pr.raw = {}
    device_mock.decode_picture.return_value = pr

    # Remove photo_count_sensor from hass.data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id].pop("photo_count_sensor", None)

    with patch("pathlib.Path.is_dir", return_value=True), patch(
        "pathlib.Path.mkdir"
    ), patch("pathlib.Path.exists", return_value=False), patch(
        "pathlib.Path.write_bytes"
    ):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )


# Wipe device error branch coverage
@pytest.mark.parametrize(
    "exc_cls, msg_contains",
    [
        (AuthenticationError, "Authentication failed"),
        (OperationError, "Wipe command failed"),
        (FmdApiException, "Wipe command failed"),
    ],
)
async def test_wipe_device_known_errors(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, exc_cls, msg_contains
) -> None:
    """device.wipe raising mapped exceptions escalates to HomeAssistantError."""
    await setup_integration(hass, mock_fmd_api)

    # Enable safety and set PIN
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

    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.wipe.side_effect = exc_cls("boom")

    with pytest.raises(HomeAssistantError, match=msg_contains):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_wipe_execute"},
            blocking=True,
        )


async def test_wipe_device_generic_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Generic unexpected exception path for wipe button."""
    await setup_integration(hass, mock_fmd_api)
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.services.async_call(
        "text",
        "set_value",
        {"entity_id": "text.fmd_test_user_wipe_pin", "value": "AnotherPin456"},
        blocking=True,
    )
    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.wipe.side_effect = RuntimeError("explode")

    with pytest.raises(HomeAssistantError, match="Wipe command failed"):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_wipe_execute"},
            blocking=True,
        )
