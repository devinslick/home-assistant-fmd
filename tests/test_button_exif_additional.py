"""Additional EXIF timestamp tag coverage for button photo download."""
from __future__ import annotations

import pathlib
from unittest.mock import AsyncMock, MagicMock, patch

from conftest import setup_integration
from homeassistant.core import HomeAssistant


async def mock_executor_job(func, *args):
    """Mock executor job to run synchronously."""
    return func(*args)


def mock_path_constructor(*args, **kwargs):
    """Mock Path constructor to avoid /media on Windows/Test envs."""
    if args and (args[0] == "/media" or args[0] == "\\media"):
        m = MagicMock()
        m.exists.return_value = False
        return m
    return pathlib.Path(*args, **kwargs)


async def test_download_photos_uses_DateTimeDigitized_when_original_missing(
    hass: HomeAssistant, mock_fmd_api
) -> None:
    """If DateTimeOriginal absent but DateTimeDigitized present, use that timestamp."""
    device = mock_fmd_api.create.return_value.device.return_value
    device.get_picture_blobs = AsyncMock(return_value=[b"blob1"])

    photo_result = MagicMock()
    photo_result.data = b"image_bytes_digitized"
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = None
    photo_result.raw = {}

    device.decode_picture = AsyncMock(return_value=photo_result)

    await setup_integration(hass, mock_fmd_api)

    # Ensure clean media directory baseline
    media_dir = pathlib.Path(hass.config.path("media")) / "fmd" / "test_user"
    if media_dir.exists():
        for f in media_dir.glob("*.jpg"):
            try:
                f.unlink()
            except Exception:
                pass

    class DummyImg:
        def getexif(self):
            # 36868 = DateTimeDigitized
            return {36868: "2025:11:22 08:15:30"}

    with patch("PIL.Image.open", return_value=DummyImg()), patch.object(
        hass, "async_add_executor_job", side_effect=mock_executor_job
    ), patch("custom_components.fmd.button.Path", side_effect=mock_path_constructor):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )
        # Photo saved -> count should be 1
        assert hass.states.get("sensor.fmd_test_user_photo_count").state == "1"


async def test_download_photos_uses_DateTime_fallback(
    hass: HomeAssistant, mock_fmd_api
) -> None:
    """If neither Original nor Digitized tags present but DateTime (306) exists, use it."""
    device = mock_fmd_api.create.return_value.device.return_value
    device.get_picture_blobs = AsyncMock(return_value=[b"blob1"])

    photo_result = MagicMock()
    photo_result.data = b"image_bytes_datetime"
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = None
    photo_result.raw = {}

    device.decode_picture = AsyncMock(return_value=photo_result)

    await setup_integration(hass, mock_fmd_api)

    # Ensure clean media directory baseline
    media_dir = pathlib.Path(hass.config.path("media")) / "fmd" / "test_user"
    if media_dir.exists():
        for f in media_dir.glob("*.jpg"):
            try:
                f.unlink()
            except Exception:
                pass

    class DummyImg:
        def getexif(self):
            return {306: "2025:11:22 09:10:05"}

    with patch("PIL.Image.open", return_value=DummyImg()), patch.object(
        hass, "async_add_executor_job", side_effect=mock_executor_job
    ), patch("custom_components.fmd.button.Path", side_effect=mock_path_constructor):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )
        assert hass.states.get("sensor.fmd_test_user_photo_count").state == "1"
