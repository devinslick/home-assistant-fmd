"""Phase 3d advanced button tests - complex image processing and EXIF paths."""
from __future__ import annotations

import base64
import io
from unittest.mock import AsyncMock, patch

from conftest import setup_integration
from homeassistant.core import HomeAssistant
from PIL import Image


async def test_photo_download_button_image_processing_success(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download with valid image and EXIF data."""
    # Create a fake JPEG image with EXIF data
    img = Image.new("RGB", (100, 100), color="red")

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    encrypted_photo = base64.b64encode(b"fake_encrypted_data")
    mock_fmd_api.create.return_value.get_pictures.return_value = [
        encrypted_photo.decode()
    ]
    mock_fmd_api.create.return_value.decrypt_data_blob.return_value = base64.b64encode(
        img_bytes.getvalue()
    ).decode()

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

    mock_fmd_api.create.return_value.get_pictures.assert_called()


async def test_photo_download_button_image_no_exif(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download with image that has no EXIF data."""
    # Create a simple image without EXIF
    img = Image.new("RGB", (100, 100), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    encrypted_photo = base64.b64encode(b"fake_encrypted_data")
    mock_fmd_api.create.return_value.get_pictures.return_value = [
        encrypted_photo.decode()
    ]
    mock_fmd_api.create.return_value.decrypt_data_blob.return_value = base64.b64encode(
        img_bytes.getvalue()
    ).decode()

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

    mock_fmd_api.create.return_value.get_pictures.assert_called()


async def test_photo_download_button_invalid_image_data(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download with invalid image data."""
    # Return corrupted image data
    encrypted_photo = base64.b64encode(b"fake_encrypted_data")
    mock_fmd_api.create.return_value.get_pictures.return_value = [
        encrypted_photo.decode()
    ]
    # Return invalid image data
    mock_fmd_api.create.return_value.decrypt_data_blob.return_value = base64.b64encode(
        b"not_a_real_image"
    ).decode()

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

    mock_fmd_api.create.return_value.get_pictures.assert_called()


async def test_photo_download_button_decrypt_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download when decryption fails."""
    encrypted_photo = base64.b64encode(b"fake_encrypted_data")
    mock_fmd_api.create.return_value.get_pictures.return_value = [
        encrypted_photo.decode()
    ]
    mock_fmd_api.create.return_value.decrypt_data_blob.side_effect = Exception(
        "Decryption failed"
    )

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

    # Should handle exception and continue
    mock_fmd_api.create.return_value.get_pictures.assert_called()


async def test_photo_download_max_photos_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download when max_photos_number entity not found."""
    await setup_integration(hass, mock_fmd_api)

    # Remove max_photos_number from hass data
    entry_id = list(hass.data["fmd"].keys())[0]
    hass.data["fmd"][entry_id]["max_photos_number"] = None

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_download"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should not call get_pictures without max_photos setting
    mock_fmd_api.create.return_value.get_pictures.assert_not_called()


async def test_photo_download_media_fallback_path(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download uses fallback media path when /media doesn't exist."""
    # Create a simple image
    img = Image.new("RGB", (100, 100), color="green")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    encrypted_photo = base64.b64encode(b"fake_encrypted_data")
    mock_fmd_api.create.return_value.get_pictures.return_value = [
        encrypted_photo.decode()
    ]
    mock_fmd_api.create.return_value.decrypt_data_blob.return_value = base64.b64encode(
        img_bytes.getvalue()
    ).decode()

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

    mock_fmd_api.create.return_value.get_pictures.assert_called()


async def test_photo_download_multiple_photos(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download with multiple photos."""
    # Create multiple fake images
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    encrypted_photos = [
        base64.b64encode(b"fake_encrypted_data_1").decode(),
        base64.b64encode(b"fake_encrypted_data_2").decode(),
        base64.b64encode(b"fake_encrypted_data_3").decode(),
    ]
    mock_fmd_api.create.return_value.get_pictures.return_value = encrypted_photos
    mock_fmd_api.create.return_value.decrypt_data_blob.return_value = base64.b64encode(
        img_bytes.getvalue()
    ).decode()

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

    mock_fmd_api.create.return_value.get_pictures.assert_called()
