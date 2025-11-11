"""Additional tests for FMD button entities to improve coverage."""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from conftest import setup_integration
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError


async def test_download_photos_exif_timestamp_used(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, tmp_path: Path
) -> None:
    """EXIF DateTimeOriginal should be used when PhotoResult has no timestamp."""
    device = mock_fmd_api.create.return_value.device.return_value
    device.get_picture_blobs.return_value = [b"blob1"]

    # PhotoResult has no timestamp so code falls back to EXIF
    photo_result = MagicMock()
    photo_result.data = b"image_bytes_for_exif"
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = None
    photo_result.raw = {}
    device.decode_picture.return_value = photo_result

    # Use hass.config.path fallback by making /media not a dir
    await setup_integration(hass, mock_fmd_api)

    with patch.object(hass.config, "path", return_value=str(tmp_path)):
        with patch("pathlib.Path.is_dir", return_value=False):
            # Provide EXIF with DateTimeOriginal and a trailing null
            class DummyImg:
                def getexif(self):
                    return {36867: "2025:10:19 15:00:34\x00"}

            with patch("PIL.Image.open", return_value=DummyImg()):
                # Let real filesystem write in tmp_path
                await hass.services.async_call(
                    "button",
                    "press",
                    {"entity_id": "button.fmd_test_user_photo_download"},
                    blocking=True,
                )

    media_dir = tmp_path / "fmd" / "test_user"
    files = list(media_dir.glob("*.jpg"))
    assert len(files) == 1
    assert files[0].name.startswith("photo_20251019_150034_")


async def test_download_photos_duplicate_skipped(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, tmp_path: Path
) -> None:
    """If a photo file already exists, it should be skipped (no write)."""
    device = mock_fmd_api.create.return_value.device.return_value
    device.get_picture_blobs.return_value = [b"blob1"]

    # Deterministic timestamp so we can pre-create duplicate
    photo_bytes = b"duplicate_test_bytes"
    photo_result = MagicMock()
    photo_result.data = photo_bytes
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = datetime(2025, 1, 1, 0, 0, 0)
    photo_result.raw = {}
    device.decode_picture.return_value = photo_result

    # Pre-create the expected filename
    content_hash = hashlib.sha256(photo_bytes).hexdigest()[:8]
    expected_filename = f"photo_20250101_000000_{content_hash}.jpg"

    await setup_integration(hass, mock_fmd_api)

    with patch.object(hass.config, "path", return_value=str(tmp_path)):
        with patch("pathlib.Path.is_dir", return_value=False):
            media_dir = tmp_path / "fmd" / "test_user"
            media_dir.mkdir(parents=True, exist_ok=True)
            (media_dir / expected_filename).write_bytes(b"already_here")

            with patch("pathlib.Path.write_bytes") as mock_write:
                await hass.services.async_call(
                    "button",
                    "press",
                    {"entity_id": "button.fmd_test_user_photo_download"},
                    blocking=True,
                )
                mock_write.assert_not_called()


@pytest.mark.parametrize(
    "exc_type",
    [
        pytest.param("auth", id="auth"),
        pytest.param("op", id="operation"),
        pytest.param("api", id="api"),
    ],
)
async def test_download_photos_raises_specific_errors(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, exc_type: str
) -> None:
    """Download path should raise HomeAssistantError on specific FMD errors."""
    from fmd_api import AuthenticationError, FmdApiException, OperationError

    device = mock_fmd_api.create.return_value.device.return_value

    if exc_type == "auth":
        device.get_picture_blobs.side_effect = AuthenticationError("nope")
    elif exc_type == "op":
        device.get_picture_blobs.side_effect = OperationError("bad conn")
    else:
        device.get_picture_blobs.side_effect = FmdApiException("server")

    await setup_integration(hass, mock_fmd_api)

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )


async def test_photo_cleanup_handles_unlink_errors(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Cleanup should continue deleting when one unlink fails."""
    device = mock_fmd_api.create.return_value.device.return_value
    device.get_picture_blobs.return_value = [b"blob1"]

    photo_result = MagicMock()
    photo_result.data = b"bytes_for_cleanup"
    photo_result.mime_type = "image/jpeg"
    photo_result.timestamp = datetime.now()
    photo_result.raw = {}
    device.decode_picture.return_value = photo_result

    await setup_integration(hass, mock_fmd_api)

    # Set retention to 1 so we'll delete all but newest
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.fmd_test_user_photo_max_to_retain", "value": 1},
        blocking=True,
    )

    # Enable auto-cleanup
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_photo_auto_cleanup"},
        blocking=True,
    )

    # Prepare three mock photos; the oldest will raise on unlink
    old1 = MagicMock()
    old2 = MagicMock()
    newest = MagicMock()

    now = datetime.now().timestamp()
    old1.stat.return_value.st_mtime = now - 300
    old2.stat.return_value.st_mtime = now - 200
    newest.stat.return_value.st_mtime = now - 100

    def exists_side_effect(self):
        return "photo_" not in str(self)

    old1.unlink.side_effect = OSError("perm")

    async def run_executor(func, *args):
        return func(*args)

    with patch("pathlib.Path.mkdir"), patch("pathlib.Path.write_bytes"), patch(
        "pathlib.Path.is_dir", return_value=True
    ), patch("pathlib.Path.exists", exists_side_effect), patch(
        "pathlib.Path.glob", return_value=[old1, old2, newest]
    ), patch.object(
        hass, "async_add_executor_job", side_effect=run_executor
    ):
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )

    # Even though the first unlink fails, the next should still be attempted
    assert old1.unlink.called
    assert old2.unlink.called


async def test_location_update_select_missing_defaults_to_all(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """If location source select is missing, provider should default to 'all'."""
    await setup_integration(hass, mock_fmd_api)

    # Remove the select entity state to simulate it being missing
    hass.states.async_remove("select.fmd_test_user_location_source")
    await hass.async_block_till_done()

    # Press the button; code should default to provider='all'
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_location_update"},
        blocking=True,
    )

    assert mock_fmd_api.create.return_value.request_location.called
    kwargs = mock_fmd_api.create.return_value.request_location.call_args.kwargs
    assert kwargs.get("provider") == "all"
