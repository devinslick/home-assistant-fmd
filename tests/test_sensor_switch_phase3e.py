"""Phase 3e sensor and switch edge case tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from conftest import setup_integration
from homeassistant.core import HomeAssistant


async def test_sensor_photo_count_initial(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo count sensor has initial value."""
    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("sensor.fmd_test_user_photo_count")
    assert state is not None
    assert state.state == "0"


async def test_sensor_photo_count_is_integer(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo count sensor returns integer state."""
    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("sensor.fmd_test_user_photo_count")
    assert state is not None
    # Should be a valid integer string
    try:
        int(state.state)
        assert True
    except ValueError:
        assert False, "Photo count should be an integer"


async def test_sensor_photo_count_with_pictures(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test photo count sensor with returned pictures."""
    from datetime import datetime

    # Mock the new device API
    device_mock = mock_fmd_api.create.return_value.device.return_value
    device_mock.get_picture_blobs.return_value = [b"blob1", b"blob2", b"blob3"]

    # Create mock PhotoResult objects with unique data
    def create_photo_result(data: bytes):
        photo_result = MagicMock()
        photo_result.data = data
        photo_result.mime_type = "image/jpeg"
        photo_result.timestamp = datetime(2025, 1, 15, 10, 30, 0)
        photo_result.raw = {}
        return photo_result

    device_mock.decode_picture.side_effect = [
        create_photo_result(b"jpeg_data_1"),
        create_photo_result(b"jpeg_data_2"),
        create_photo_result(b"jpeg_data_3"),
    ]

    await setup_integration(hass, mock_fmd_api)

    # Download photos
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.fmd_test_user_photo_download"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify get_picture_blobs was called
    device_mock.get_picture_blobs.assert_called()


async def test_switch_wipe_safety_exists(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe safety switch entity exists."""
    await setup_integration(hass, mock_fmd_api)

    state = hass.states.get("switch.fmd_test_user_wipe_safety_switch")
    assert state is not None


async def test_switch_wipe_safety_toggle_on(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe safety switch can be toggled on."""
    await setup_integration(hass, mock_fmd_api)

    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("switch.fmd_test_user_wipe_safety_switch")
    assert state is not None
    assert state.state == "on"


async def test_switch_wipe_safety_toggle_off(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test wipe safety switch can be toggled off."""
    await setup_integration(hass, mock_fmd_api)

    # First turn on
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Then turn off
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("switch.fmd_test_user_wipe_safety_switch")
    assert state is not None
    assert state.state == "off"


async def test_switch_multiple_toggles(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test switch handles multiple rapid toggles."""
    await setup_integration(hass, mock_fmd_api)

    # Rapid toggles
    for _ in range(3):
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
            blocking=True,
        )
        await hass.async_block_till_done()

        await hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": "switch.fmd_test_user_wipe_safety_switch"},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Final state should be off
    state = hass.states.get("switch.fmd_test_user_wipe_safety_switch")
    assert state is not None
    assert state.state == "off"
