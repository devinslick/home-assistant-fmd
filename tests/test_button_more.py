"""Additional button tests for photo cleanup."""
from __future__ import annotations

import os
import time
from pathlib import Path
from unittest.mock import AsyncMock

from conftest import setup_integration
from homeassistant.core import HomeAssistant

from custom_components.fmd.button import FmdDownloadPhotosButton
from custom_components.fmd.const import DOMAIN


async def test_cleanup_old_photos_deletes_oldest(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, tmp_path: Path
) -> None:
    """Cleanup should delete oldest photos when count exceeds the limit."""
    await setup_integration(hass, mock_fmd_api)

    # Prepare a fake media directory under hass config path
    entry_id = list(hass.data[DOMAIN].keys())[0]
    # device_id removed as unused

    # Use hass.config.path('media') base and create fmd subdir
    media_dir = (
        Path(hass.config.path("media"))
        / "fmd"
        / hass.data[DOMAIN][entry_id]["device_info"]["name"].split()[1]
    )
    media_dir.mkdir(parents=True, exist_ok=True)

    # Clean up any existing jpg files that may have been created by other tests
    for existing in media_dir.glob("*.jpg"):
        existing.unlink()

    # Create 4 dummy photo files with increasing modification times
    files = []
    for i in range(4):
        f = media_dir / f"photo_old_{i}.jpg"
        f.write_bytes(b"testdata%d" % i)
        # Set mtime progressively older
        ts = time.time() - (100 * (4 - i))
        os.utime(f, (ts, ts))
        files.append(f)

    # Create a button instance to call cleanup directly
    # Construct a fake entry object to pass to button
    mock_entry = hass.config_entries.async_entries(domain=DOMAIN)[0]
    button = FmdDownloadPhotosButton(hass, mock_entry)

    # Now call the cleanup to retain only 2 files
    await button._cleanup_old_photos(media_dir, 2)

    # Only 2 files should remain
    remaining = sorted(p.name for p in media_dir.glob("*.jpg"))
    assert len(remaining) == 2

    # Ensure the two newest remain (highest indices in our create loop)
    assert "photo_old_3.jpg" in remaining
    assert "photo_old_2.jpg" in remaining
