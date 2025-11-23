"""Tests for photo download error branches and duplicate handling."""
from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from conftest import setup_integration
from homeassistant.core import HomeAssistant

from custom_components.fmd.button import FmdDownloadPhotosButton
from custom_components.fmd.const import DOMAIN


async def test_download_photos_no_photos_found(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog
) -> None:
    """When no pictures are found, warn and return."""
    await setup_integration(hass, mock_fmd_api)

    btn = FmdDownloadPhotosButton(
        hass, hass.config_entries.async_entries(domain=DOMAIN)[0]
    )

    mock_device = mock_fmd_api.create.return_value.device.return_value
    mock_device.get_picture_blobs.return_value = []

    await btn.async_press()

    assert any("No photos found on server" in rec.message for rec in caplog.records)


async def test_download_photos_mkdir_failure_logs_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog, tmp_path: Path
) -> None:
    """If media directory cannot be created, log an error and stop."""
    await setup_integration(hass, mock_fmd_api)

    btn = FmdDownloadPhotosButton(
        hass, hass.config_entries.async_entries(domain=DOMAIN)[0]
    )

    mock_device = mock_fmd_api.create.return_value.device.return_value
    mock_device.get_picture_blobs.return_value = [b"blob1"]

    # Patch Path.mkdir to raise an exception
    with patch("pathlib.Path.mkdir", side_effect=Exception("fail mkdir")):
        await btn.async_press()

    assert any(
        "Failed to create media directory" in rec.message for rec in caplog.records
    )


async def test_download_photos_exif_extraction_failure_logs_warning(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog: MagicMock
) -> None:
    """If EXIF extraction fails, log a warning and continue."""
    await setup_integration(hass, mock_fmd_api)

    # Ensure media dir exists
    media_dir = (
        Path(hass.config.path("media"))
        / "fmd"
        / hass.data[DOMAIN][list(hass.data[DOMAIN].keys())[0]]["device_info"][
            "name"
        ].split()[1]
    )
    media_dir.mkdir(parents=True, exist_ok=True)
    # Ensure isolation: remove any leftover photo files from previous tests
    for existing in media_dir.glob("*.jpg"):
        existing.unlink()

    btn = FmdDownloadPhotosButton(
        hass, hass.config_entries.async_entries(domain=DOMAIN)[0]
    )

    mock_device = mock_fmd_api.create.return_value.device.return_value
    mock_device.get_picture_blobs.return_value = [b"blob1"]

    # Make decode_picture return a result with no timestamp
    photo_result = MagicMock()
    photo_bytes = b"imagedata"
    photo_result.data = photo_bytes
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = None
    mock_device.decode_picture.return_value = photo_result

    # Make Image.open to raise when used which should trigger EXIF warning
    with patch("PIL.Image.open", side_effect=Exception("exif fail")):
        await btn.async_press()

    assert any(
        "Could not extract EXIF timestamp" in rec.getMessage()
        or "Could not extract EXIF timestamp" in rec.message
        for rec in caplog.records
    )


async def test_download_photos_duplicate_skips_save(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, tmp_path: Path, caplog
) -> None:
    """Duplicate photo (existing file with same hash) should be skipped."""
    await setup_integration(hass, mock_fmd_api)

    entry_id = list(hass.data[DOMAIN].keys())[0]
    btn = FmdDownloadPhotosButton(
        hass, hass.config_entries.async_entries(domain=DOMAIN)[0]
    )

    mock_device = mock_fmd_api.create.return_value.device.return_value
    mock_device.get_picture_blobs.return_value = [b"blob1"]

    # Mock photo result with no timestamp so filename is hash-based
    photo_result = MagicMock()
    photo_bytes = b"duplicate bytes"
    photo_result.data = photo_bytes
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = None
    mock_device.decode_picture.return_value = photo_result

    # Pre-create a file with the hash-based filename
    content_hash = hashlib.sha256(photo_bytes).hexdigest()[:8]
    media_dir = (
        Path(hass.config.path("media"))
        / "fmd"
        / hass.data[DOMAIN][entry_id]["device_info"]["name"].split()[1]
    )
    media_dir.mkdir(parents=True, exist_ok=True)
    # Ensure isolation: clean any pre-existing files
    for existing in media_dir.glob("*.jpg"):
        existing.unlink()
    existing_file = media_dir / f"photo_{content_hash}.jpg"
    existing_file.write_bytes(b"existing")

    await btn.async_press()

    assert any("Skipping duplicate" in rec.message for rec in caplog.records)


async def test_download_photos_write_raises_logs_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog
) -> None:
    """If writing a photo file fails, log an error and continue."""
    await setup_integration(hass, mock_fmd_api)

    btn = FmdDownloadPhotosButton(
        hass, hass.config_entries.async_entries(domain=DOMAIN)[0]
    )

    mock_device = mock_fmd_api.create.return_value.device.return_value
    mock_device.get_picture_blobs.return_value = [b"blob1"]

    # Make decode_picture return a result
    photo_result = MagicMock()
    photo_bytes = b"imagedata2"
    photo_result.data = photo_bytes
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = None
    mock_device.decode_picture.return_value = photo_result

    # Patch Path.write_bytes to raise
    with patch("pathlib.Path.write_bytes", side_effect=Exception("write fail")):
        await btn.async_press()

    assert any("Failed to decrypt/save photo" in rec.message for rec in caplog.records)
