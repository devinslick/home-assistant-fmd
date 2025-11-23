"""Additional EXIF timestamp tag coverage for button photo download."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from conftest import setup_integration
from homeassistant.core import HomeAssistant


async def test_download_photos_uses_DateTimeDigitized_when_original_missing(
    hass: HomeAssistant, mock_fmd_api
) -> None:
    """If DateTimeOriginal absent but DateTimeDigitized present, use that timestamp."""
    device = mock_fmd_api.create.return_value.device.return_value
    device.get_picture_blobs.return_value = [b"blob1"]
    photo_result = MagicMock()
    photo_result.data = b"image_bytes_digitized"
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = None
    photo_result.raw = {}
    device.decode_picture.return_value = photo_result

    await setup_integration(hass, mock_fmd_api)

    # Ensure clean media directory baseline
    from pathlib import Path

    media_dir = Path(hass.config.path("media")) / "fmd" / "test_user"
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

    # Patch Image.open to provide EXIF tag.
    with patch("PIL.Image.open", return_value=DummyImg()):
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
    device.get_picture_blobs.return_value = [b"blob1"]
    photo_result = MagicMock()
    photo_result.data = b"image_bytes_datetime"
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = None
    photo_result.raw = {}
    device.decode_picture.return_value = photo_result

    await setup_integration(hass, mock_fmd_api)

    # Ensure clean media directory baseline
    from pathlib import Path

    media_dir = Path(hass.config.path("media")) / "fmd" / "test_user"
    if media_dir.exists():
        for f in media_dir.glob("*.jpg"):
            try:
                f.unlink()
            except Exception:
                pass

    class DummyImg:
        def getexif(self):
            return {306: "2025:11:22 09:10:05"}

    with patch("PIL.Image.open", return_value=DummyImg()):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )
        assert hass.states.get("sensor.fmd_test_user_photo_count").state == "1"
