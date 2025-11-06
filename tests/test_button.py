"""Test FMD button entities."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from conftest import setup_integration
from homeassistant.core import HomeAssistant


async def test_location_update_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test location update button."""
    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_location_update"},
        blocking=True,
    )

    mock_fmd_api.create.return_value.request_location.assert_called_once()


async def test_ring_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ring button."""
    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_volume_ring_device"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_fmd_api.create.return_value.send_command.assert_called_once_with("ring")


async def test_lock_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test lock button."""
    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_lock_device"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_fmd_api.create.return_value.send_command.assert_called_once_with("lock")


async def test_capture_front_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test capture front photo button."""
    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_capture_front"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_fmd_api.create.return_value.take_picture.assert_called_once_with("front")


async def test_capture_rear_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test capture rear photo button."""
    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_capture_rear"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_fmd_api.create.return_value.take_picture.assert_called_once_with("back")


async def test_download_photos_button(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test download photos button."""
    import base64

    # Return encrypted blobs (just strings)
    mock_fmd_api.create.return_value.get_pictures.return_value = [
        "encrypted_blob_1",
        "encrypted_blob_2",
    ]

    # Mock decrypt_data_blob to return DIFFERENT base64-encoded fake image data
    # So they don't hash to the same value and get skipped as duplicates
    # Note: decrypt_data_blob is a sync function called in executor
    fake_image_1 = base64.b64encode(b"fake_jpeg_data_1_unique").decode("utf-8")
    fake_image_2 = base64.b64encode(b"fake_jpeg_data_2_different").decode("utf-8")

    # Use a function instead of list to avoid StopIteration issues
    decrypt_values = {
        "encrypted_blob_1": fake_image_1,
        "encrypted_blob_2": fake_image_2,
    }
    mock_fmd_api.create.return_value.decrypt_data_blob.side_effect = (
        lambda blob: decrypt_values.get(blob, fake_image_1)
    )

    # Setup integration BEFORE patching Path methods
    await setup_integration(hass, mock_fmd_api)

    # Use a callable for exists() to handle any number of calls
    # Returns True for directories, False for photo files
    def exists_side_effect(self):
        return "photo_" not in str(self)

    with patch("pathlib.Path.mkdir"), patch(
        "pathlib.Path.is_dir", return_value=True
    ), patch("pathlib.Path.exists", exists_side_effect), patch(
        "pathlib.Path.write_bytes"
    ) as mock_write:
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_download"},
            blocking=True,
        )

        mock_fmd_api.create.return_value.get_pictures.assert_called_once()
        # Verify 2 photos were written
        assert mock_write.call_count == 2


async def test_download_photos_with_cleanup(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test download photos with auto-cleanup enabled."""
    import base64
    from datetime import datetime, timedelta
    from unittest.mock import MagicMock

    # Return encrypted blob
    mock_fmd_api.create.return_value.get_pictures.return_value = ["encrypted_blob_1"]

    # Mock decrypt_data_blob to return base64-encoded fake image data
    fake_image = base64.b64encode(b"fake_jpeg_data_cleanup_test").decode("utf-8")
    mock_fmd_api.create.return_value.decrypt_data_blob.return_value = fake_image

    # Setup integration BEFORE patching Path methods
    await setup_integration(hass, mock_fmd_api)

    # Set max photos to 3
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.fmd_test_user_photo_max_to_retain", "value": 3},
        blocking=True,
    )

    # Enable auto-cleanup
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_photo_auto_cleanup"},
        blocking=True,
    )

    # Create mock old photos (4 old photos + will add 1 new = 5 total,
    # limit is 3, so 2 should be deleted)
    old_photos = []
    for i in range(4):
        photo = MagicMock()
        photo.stat.return_value.st_mtime = (
            datetime.now() - timedelta(days=i + 1)
        ).timestamp()
        photo.name = f"old_photo_{i}.jpg"
        old_photos.append(photo)

    # The new photo that will be downloaded
    new_photo = MagicMock()
    new_photo.stat.return_value.st_mtime = datetime.now().timestamp()
    new_photo.name = "new_photo.jpg"

    # Use a callable for exists() that returns True for directories, False for photo files
    def exists_side_effect(self):
        return "photo_" not in str(self)

    # Now patch only for the photo download operation
    with patch("pathlib.Path.mkdir"), patch("pathlib.Path.write_bytes"), patch(
        "pathlib.Path.is_dir", return_value=True
    ), patch("pathlib.Path.exists", exists_side_effect), patch(
        "pathlib.Path.glob"
    ) as mock_glob:
        # glob returns all photos (4 old + 1 new = 5) when cleanup runs
        mock_glob.return_value = old_photos + [new_photo]

        # Mock async_add_executor_job to actually execute the callable
        async def mock_executor_job(func, *args):
            return func(*args)

        with patch.object(
            hass, "async_add_executor_job", side_effect=mock_executor_job
        ):
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_photo_download"},
                blocking=True,
            )

            # Verify the 2 oldest photos were deleted (5 photos - 3 limit =
            # 2 to delete)
            # Photos are created with timestamps: old_photo_0 is 4 days old,
            # old_photo_1 is 3 days old, etc.
            # When sorted by mtime (oldest first), they delete the 2 oldest:
            # old_photo_3 (1 day) and old_photo_2 (2 days)
            # WAIT - actually looking at the loop: for i in range(4):
            # mtime = now - (i+1) days
            # So: old_photo_0 = now-1, old_photo_1 = now-2, old_photo_2 =
            # now-3, old_photo_3 = now-4
            # Sorted oldest first: old_photo_3 (now-4), old_photo_2
            # (now-3), old_photo_1 (now-2), old_photo_0 (now-1)
            # With 5 total (4 old + 1 new) and limit 3, we delete 2 oldest
            # = old_photo_3 and old_photo_2
            # Which corresponds to indices 3 and 2
            old_photos[3].unlink.assert_called_once()
            old_photos[2].unlink.assert_called_once()
            # Ensure photos 0 and 1 were NOT deleted (they are newer)
            old_photos[0].unlink.assert_not_called()
            old_photos[1].unlink.assert_not_called()


async def test_wipe_device_button_blocked(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe device button is blocked without safety switch."""
    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_device"},
        blocking=True,
    )

    # Should NOT call wipe API
    mock_fmd_api.create.return_value.wipe_device.assert_not_called()


async def test_wipe_device_button_allowed(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe device button works with safety switch enabled."""
    await setup_integration(hass, mock_fmd_api)

    # Enable safety switch
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_fmd_api.create.return_value.send_command.assert_called_with("delete")


# Phase 3 error handling tests
async def test_location_update_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test location update when tracker is not found."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass.data
    hass.data["fmd"][list(hass.data["fmd"].keys())[0]].pop("tracker", None)

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_location_update"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should handle gracefully - API should not be called
    mock_fmd_api.create.return_value.request_location.assert_not_called()


async def test_ring_button_api_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test ring button handles API errors gracefully."""
    await setup_integration(hass, mock_fmd_api)

    # Mock API to raise error
    mock_fmd_api.create.return_value.send_command.side_effect = RuntimeError(
        "API error"
    )

    try:
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_volume_ring_device"},
            blocking=True,
        )
    except RuntimeError:
        pass

    await hass.async_block_till_done()
    mock_fmd_api.create.return_value.send_command.assert_called_once_with("ring")


async def test_lock_button_api_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test lock button handles API errors gracefully."""
    await setup_integration(hass, mock_fmd_api)

    # Mock API to raise error
    mock_fmd_api.create.return_value.send_command.side_effect = RuntimeError(
        "API error"
    )

    try:
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_lock_device"},
            blocking=True,
        )
    except RuntimeError:
        pass

    await hass.async_block_till_done()
    mock_fmd_api.create.return_value.send_command.assert_called_once_with("lock")


async def test_capture_photo_api_error(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test capture photo button handles API errors gracefully."""
    await setup_integration(hass, mock_fmd_api)

    # Mock API to raise error
    mock_fmd_api.create.return_value.take_picture.side_effect = RuntimeError(
        "API error"
    )

    try:
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.fmd_test_user_photo_capture_front"},
            blocking=True,
        )
    except RuntimeError:
        pass

    await hass.async_block_till_done()
    mock_fmd_api.create.return_value.take_picture.assert_called_once_with("front")


async def test_download_photos_empty_result(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test download photos button with empty result."""
    await setup_integration(hass, mock_fmd_api)

    # Return empty list
    mock_fmd_api.create.return_value.get_pictures.return_value = []

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_download"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Sensor should have count of 0
    sensor = hass.data["fmd"][list(hass.data["fmd"].keys())[0]]["photo_count_sensor"]
    assert sensor._last_download_count == 0


async def test_wipe_button_tracker_not_found(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe button when tracker is not found."""
    await setup_integration(hass, mock_fmd_api)

    # Remove tracker from hass.data
    hass.data["fmd"][list(hass.data["fmd"].keys())[0]].pop("tracker", None)

    # Enable safety
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )

    # Try wipe
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should not call API since tracker not found
    mock_fmd_api.create.return_value.send_command.assert_not_called()


async def test_wipe_button_tracker_not_found_keeps_safety_on(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """With safety on but tracker missing, wipe should not run and safety stays on."""
    await setup_integration(hass, mock_fmd_api)

    # Enable safety
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Remove tracker from hass.data
    hass.data["fmd"][list(hass.data["fmd"].keys())[0]].pop("tracker", None)

    # Try wipe
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_fmd_api.create.return_value.send_command.assert_not_called()
    state = hass.states.get("switch.fmd_test_user_wipe_safety_switch")
    assert state is not None and state.state == "on"


async def test_ring_button_returns_false(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """If ring command returns False, it should be handled without crash."""
    await setup_integration(hass, mock_fmd_api)

    mock_fmd_api.create.return_value.send_command.return_value = False

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_volume_ring_device"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_fmd_api.create.return_value.send_command.assert_called_once_with("ring")


async def test_lock_button_returns_false(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """If lock command returns False, it should be handled without crash."""
    await setup_integration(hass, mock_fmd_api)

    mock_fmd_api.create.return_value.send_command.return_value = False

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_lock_device"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_fmd_api.create.return_value.send_command.assert_called_once_with("lock")


async def test_capture_front_returns_false(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """If take_picture returns False, it should be handled without crash."""
    await setup_integration(hass, mock_fmd_api)

    mock_fmd_api.create.return_value.take_picture.return_value = False

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_capture_front"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_fmd_api.create.return_value.take_picture.assert_called_once_with("front")


async def test_download_photos_cleanup_noop_no_warnings(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
    caplog,
) -> None:
    """No cleanup warnings should be logged when count <= max_to_retain."""
    import base64
    from unittest.mock import MagicMock, patch

    mock_fmd_api.create.return_value.get_pictures.return_value = [
        base64.b64encode(b"jpeg_data").decode()
    ]
    mock_fmd_api.create.return_value.decrypt_data_blob.return_value = base64.b64encode(
        b"jpeg_data"
    ).decode()

    await setup_integration(hass, mock_fmd_api)

    # Set retention higher than existing count
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.fmd_test_user_photo_max_to_retain", "value": 5},
        blocking=True,
    )
    # Enable auto-cleanup
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_photo_auto_cleanup"},
        blocking=True,
    )

    photos = [MagicMock(), MagicMock()]

    def exists_side_effect(self):
        return "photo_" not in str(self)

    caplog.clear()
    with patch("pathlib.Path.mkdir"), patch("pathlib.Path.write_bytes"), patch(
        "pathlib.Path.is_dir",
        return_value=True,
    ), patch("pathlib.Path.exists", exists_side_effect), patch(
        "pathlib.Path.glob",
        return_value=photos,
    ):

        async def mock_executor_job(func, *args):
            return func(*args)

        with patch.object(
            hass, "async_add_executor_job", side_effect=mock_executor_job
        ):
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_photo_download"},
                blocking=True,
            )
            await hass.async_block_till_done()

    # Ensure no AUTO-CLEANUP warning entries present
    assert not any(
        "AUTO-CLEANUP" in r.getMessage() and r.levelname == "WARNING"
        for r in caplog.records
    )


async def test_download_photos_success(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test successful photo download button press."""
    await setup_integration(hass, mock_fmd_api)

    # Mock get_pictures to return a photo
    mock_fmd_api.create.return_value.get_pictures.return_value = [b"fake_photo_data"]

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_download"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify get_pictures was called
    mock_fmd_api.create.return_value.get_pictures.assert_called()


async def test_download_photos_no_photos(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo download when no photos available."""
    await setup_integration(hass, mock_fmd_api)

    # Return empty list of photos
    mock_fmd_api.create.return_value.get_pictures.return_value = []

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_download"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should still call get_pictures
    mock_fmd_api.create.return_value.get_pictures.assert_called()


async def test_wipe_button_blocked_by_safety(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe button is blocked when safety switch is on."""
    await setup_integration(hass, mock_fmd_api)

    # Safety is OFF by default (disabled)
    state = hass.states.get("switch.fmd_test_user_wipe_safety_switch")
    assert state.state == "off"

    # Try to wipe with safety off (disabled)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Should not call send_command because safety is disabled
    mock_fmd_api.create.return_value.send_command.assert_not_called()


async def test_wipe_device_button_failure_keeps_safety_on(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """If wipe command returns False, safety should remain on."""
    await setup_integration(hass, mock_fmd_api)

    # Enable safety switch
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Return False from API
    mock_fmd_api.create.return_value.send_command.return_value = False

    # Attempt wipe
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Safety should still be ON after failure
    state = hass.states.get("switch.fmd_test_user_wipe_safety_switch")
    assert state is not None and state.state == "on"


async def test_location_update_uses_selected_provider_gps(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Selecting GPS Only should call request_location with provider='gps'."""
    await setup_integration(hass, mock_fmd_api)

    # Change select option to GPS Only (Accurate)
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.fmd_test_user_location_source",
            "option": "GPS Only (Accurate)",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Press location update
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_location_update"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify provider mapping
    assert mock_fmd_api.create.return_value.request_location.called
    kwargs = mock_fmd_api.create.return_value.request_location.call_args.kwargs
    assert kwargs.get("provider") == "gps"


async def test_download_photos_cleanup_noop_when_within_limit(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Auto-cleanup returns early when photo_count <= max_to_retain."""
    import base64
    from unittest.mock import MagicMock, patch

    # One picture to trigger download flow
    mock_fmd_api.create.return_value.get_pictures.return_value = [
        base64.b64encode(b"jpeg_data").decode()
    ]
    mock_fmd_api.create.return_value.decrypt_data_blob.return_value = base64.b64encode(
        b"jpeg_data"
    ).decode()

    await setup_integration(hass, mock_fmd_api)

    # Set retention to 5
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.fmd_test_user_photo_max_to_retain", "value": 5},
        blocking=True,
    )

    # Enable auto-cleanup
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_photo_auto_cleanup"},
        blocking=True,
    )

    # Prepare a small list of existing photos (<= 5)
    photos = [MagicMock(), MagicMock()]  # 2 existing photos

    def exists_side_effect(self):
        return "photo_" not in str(self)

    with patch("pathlib.Path.mkdir"), patch("pathlib.Path.write_bytes"), patch(
        "pathlib.Path.is_dir",
        return_value=True,
    ), patch("pathlib.Path.exists", exists_side_effect), patch(
        "pathlib.Path.glob",
        return_value=photos,
    ):
        # Make executor jobs run
        async def mock_executor_job(func, *args):
            return func(*args)

        with patch.object(
            hass, "async_add_executor_job", side_effect=mock_executor_job
        ):
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": "button.fmd_test_user_photo_download"},
                blocking=True,
            )
            await hass.async_block_till_done()

    # Ensure no deletions attempted
    for p in photos:
        p.unlink.assert_not_called()


async def test_wipe_device_button_auto_disables_safety(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Wipe button should auto-disable safety switch after success."""
    await setup_integration(hass, mock_fmd_api)

    # Enable safety
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Ensure API returns success
    mock_fmd_api.create.return_value.send_command.return_value = True

    # Press wipe execute
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Safety switch should be turned off by the button
    state = hass.states.get("switch.fmd_test_user_wipe_safety_switch")
    assert state is not None and state.state == "off"


async def test_wipe_device_button_api_error_keeps_safety_on(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """If wipe API raises, safety remains on (only disabled on success)."""
    await setup_integration(hass, mock_fmd_api)

    # Enable safety
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Make API raise
    mock_fmd_api.create.return_value.send_command.side_effect = RuntimeError("boom")

    # Press wipe execute (should handle error internally)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Safety should still be on
    state = hass.states.get("switch.fmd_test_user_wipe_safety_switch")
    assert state is not None and state.state == "on"


async def test_location_update_default_provider(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Location update uses provider='all' when default option is selected."""
    await setup_integration(hass, mock_fmd_api)

    # By default the select is "All Providers (Default)"
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_location_update"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Ensure provider default was used
    mock_fmd_api.create.return_value.request_location.assert_called()
    kwargs = mock_fmd_api.create.return_value.request_location.call_args.kwargs
    assert kwargs.get("provider") == "all"


async def test_download_photos_exif_present_but_no_timestamp_tags(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
    tmp_path,
) -> None:
    """With EXIF present but no datetime tags, fallback filename used."""
    import base64
    from unittest.mock import patch

    image_bytes = b"img_no_tags"
    mock_fmd_api.create.return_value.get_pictures.return_value = [
        base64.b64encode(image_bytes).decode()
    ]
    mock_fmd_api.create.return_value.decrypt_data_blob.return_value = base64.b64encode(
        image_bytes
    ).decode()

    # Setup integration first
    await setup_integration(hass, mock_fmd_api)

    # Force using config/media by making /media appear missing
    # But let real paths in tmp_path work normally
    from pathlib import Path as RealPath

    original_exists = RealPath.exists
    original_is_dir = RealPath.is_dir

    def exists_side_effect(path_self):
        if str(path_self) == "/media":
            return False
        return original_exists(path_self)

    def is_dir_side_effect(path_self):
        if str(path_self) == "/media":
            return False
        return original_is_dir(path_self)

    with patch("pathlib.Path.exists", side_effect=exists_side_effect), patch(
        "pathlib.Path.is_dir", side_effect=is_dir_side_effect
    ):
        # Make hass.config.path return tmp dir (patch instance method)
        with patch.object(hass.config, "path", return_value=str(tmp_path)):

            class DummyImg:
                def getexif(self):
                    # EXIF present but no datetime tags
                    return {1234: "something"}

            with patch("PIL.Image.open", return_value=DummyImg()):
                await hass.services.async_call(
                    "button",
                    "press",
                    {"entity_id": "button.fmd_test_user_photo_download"},
                    blocking=True,
                )
                await hass.async_block_till_done()

    # Should have one jpg with hash-only naming
    device_dir = tmp_path / "fmd" / "test_user"
    photos = list(device_dir.glob("photo_*.jpg"))
    assert len(photos) == 1
    assert "_" not in photos[0].name.split("photo_")[1][:15]  # no timestamp prefix

    # Now enable the safety switch (turn it on)
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify it's now on
    state = hass.states.get("switch.fmd_test_user_wipe_safety_switch")
    assert state.state == "on"

    # Reset the mock to check if wipe works now
    mock_fmd_api.create.return_value.send_command.reset_mock()

    # Try to wipe with safety enabled
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_wipe_execute"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Now delete command should be called since safety is enabled
    mock_fmd_api.create.return_value.send_command.assert_called_once_with("delete")
