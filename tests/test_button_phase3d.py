"""Phase 3d advanced button tests - complex image processing and EXIF/PhotoResult paths.

Updated for fmd_api 2.0.4+ picture API:
 - Uses device.get_picture_blobs(max_photos)
 - Each blob decoded via device.decode_picture(blob) returning PhotoResult
 - PhotoResult.timestamp preferred; when None falls back to EXIF extraction
"""
from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch

from conftest import setup_integration
from homeassistant.core import HomeAssistant
from PIL import Image


async def test_photo_download_button_image_processing_success(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download with valid image and fallback to EXIF (timestamp None)."""
    # Create a fake JPEG image (EXIF path will be attempted because timestamp=None)
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    raw_bytes = img_bytes.getvalue()

    device = mock_fmd_api.create.return_value.device.return_value
    device.get_picture_blobs.return_value = [b"blob1"]

    # Return PhotoResult-like object with timestamp=None to force EXIF path
    photo_result = MagicMock()
    photo_result.data = raw_bytes
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = None  # Force EXIF extraction code path
    photo_result.raw = {}
    device.decode_picture.return_value = photo_result

    await setup_integration(hass, mock_fmd_api)

    with patch("pathlib.Path.mkdir"):
        with patch("pathlib.Path.exists", return_value=True):
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_photo_download"},
                blocking=True,
            )
            await hass.async_block_till_done()

    device.get_picture_blobs.assert_called()


async def test_photo_download_button_image_no_exif(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download with image that has no EXIF data (still saved)."""
    img = Image.new("RGB", (100, 100), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    raw_bytes = img_bytes.getvalue()

    device = mock_fmd_api.create.return_value.device.return_value
    device.get_picture_blobs.return_value = [b"blob1"]

    photo_result = MagicMock()
    photo_result.data = raw_bytes
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = None  # triggers EXIF attempt -> none found
    photo_result.raw = {}
    device.decode_picture.return_value = photo_result

    await setup_integration(hass, mock_fmd_api)

    with patch("pathlib.Path.mkdir"):
        with patch("pathlib.Path.exists", return_value=True):
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_photo_download"},
                blocking=True,
            )
            await hass.async_block_till_done()

    device.get_picture_blobs.assert_called()


async def test_photo_download_button_invalid_image_data(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download with invalid image data (decode succeeds, EXIF fails)."""
    device = mock_fmd_api.create.return_value.device.return_value
    device.get_picture_blobs.return_value = [b"blob1"]

    # Corrupted bytes that PIL cannot parse as JPEG
    photo_result = MagicMock()
    photo_result.data = b"not_a_real_image"
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = None
    photo_result.raw = {}
    device.decode_picture.return_value = photo_result

    await setup_integration(hass, mock_fmd_api)

    with patch("pathlib.Path.mkdir"):
        with patch("pathlib.Path.exists", return_value=True):
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_photo_download"},
                blocking=True,
            )
            await hass.async_block_till_done()

    device.get_picture_blobs.assert_called()


async def test_photo_download_button_decode_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download when decode_picture fails for a blob."""
    device = mock_fmd_api.create.return_value.device.return_value
    device.get_picture_blobs.return_value = [b"blob1"]
    device.decode_picture.side_effect = Exception("Decode failed")

    await setup_integration(hass, mock_fmd_api)

    with patch("pathlib.Path.mkdir"):
        with patch("pathlib.Path.exists", return_value=True):
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_photo_download"},
                blocking=True,
            )
            await hass.async_block_till_done()

    device.get_picture_blobs.assert_called()


async def test_photo_download_max_photos_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download when max_photos_number entity not found (no API call)."""
    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id]["max_photos_number"] = None

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_download"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_fmd_api.create.return_value.device.return_value.get_picture_blobs.assert_not_called()


async def test_photo_download_media_fallback_path(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download uses fallback media path when /media doesn't exist."""
    img = Image.new("RGB", (100, 100), color="green")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    raw_bytes = img_bytes.getvalue()

    device = mock_fmd_api.create.return_value.device.return_value
    device.get_picture_blobs.return_value = [b"blob1"]
    photo_result = MagicMock()
    photo_result.data = raw_bytes
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = None
    photo_result.raw = {}
    device.decode_picture.return_value = photo_result

    await setup_integration(hass, mock_fmd_api)

    with patch("pathlib.Path.mkdir"):
        with patch("pathlib.Path.exists", return_value=False):
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_photo_download"},
                blocking=True,
            )
            await hass.async_block_till_done()

    device.get_picture_blobs.assert_called()


async def test_photo_download_multiple_photos(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download with multiple blobs decoded sequentially."""
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    raw_bytes = img_bytes.getvalue()

    device = mock_fmd_api.create.return_value.device.return_value
    device.get_picture_blobs.return_value = [b"blob1", b"blob2", b"blob3"]

    # Use side_effect to return a new PhotoResult for each blob
    def mk_photo_result():
        pr = MagicMock()
        pr.data = raw_bytes
        pr.mime_type = "image/jpeg"
        pr.timestamp = None  # exercise EXIF path each time
        pr.raw = {}
        return pr

    device.decode_picture.side_effect = [
        mk_photo_result(),
        mk_photo_result(),
        mk_photo_result(),
    ]

    await setup_integration(hass, mock_fmd_api)

    with patch("pathlib.Path.mkdir"):
        with patch("pathlib.Path.exists", return_value=True):
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_photo_download"},
                blocking=True,
            )
            await hass.async_block_till_done()

    device.get_picture_blobs.assert_called()
