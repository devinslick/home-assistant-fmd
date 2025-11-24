"""Test FMD sensor and text coverage."""
from unittest.mock import AsyncMock, patch

import pytest
from conftest import setup_integration
from homeassistant.core import HomeAssistant

from custom_components.fmd.const import DOMAIN


async def test_sensor_init_invalid_date(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test sensor initialization with invalid date string."""
    # Setup integration first to get the entry
    await setup_integration(hass, mock_fmd_api)

    # Get the entry
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    # Modify entry data to have invalid date
    new_data = dict(entry.data)
    new_data["photo_count_last_download_time"] = "invalid-date-string"
    hass.config_entries.async_update_entry(entry, data=new_data)

    # Reload the integration to trigger __init__ again
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    # Check that the sensor initialized with None for last_download_time
    sensor = hass.states.get("sensor.fmd_test_user_photo_count")
    assert sensor is not None
    assert sensor.attributes["last_download_time"] is None


async def test_sensor_update_media_folder_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test sensor handles errors when counting media files."""
    await setup_integration(hass, mock_fmd_api)

    # Patch Path to raise exception
    with patch("custom_components.fmd.sensor.Path") as mock_path_cls:
        mock_path = mock_path_cls.return_value
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True
        # Raise exception when accessing glob
        mock_path.__truediv__.return_value.glob.side_effect = Exception("Disk error")

        # Trigger update
        sensor_entity = hass.data[DOMAIN]["test_entry_id"]["photo_count_sensor"]
        sensor_entity.update_photo_count(5)

        # Verify count is 0 on error
        assert sensor_entity.native_value == 0


async def test_wipe_pin_validation_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Test wipe PIN validation errors."""
    await setup_integration(hass, mock_fmd_api)

    # Get the entity instance
    entity = hass.data[DOMAIN]["test_entry_id"]["wipe_pin_text"]

    # Test non-alphanumeric
    with pytest.raises(ValueError) as excinfo:
        await entity.async_set_value("1234!")
    assert "alphanumeric" in str(excinfo.value)

    # Test non-ASCII
    with pytest.raises(ValueError) as excinfo:
        await entity.async_set_value("café")
    assert "ASCII" in str(excinfo.value)


async def test_wipe_pin_short_warning(
    hass: HomeAssistant, mock_fmd_api: AsyncMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Test warning for short wipe PIN."""
    await setup_integration(hass, mock_fmd_api)

    # Set short PIN
    await hass.services.async_call(
        "text",
        "set_value",
        {"entity_id": "text.fmd_test_user_wipe_pin", "value": "12345"},
        blocking=True,
    )

    # Check for warning
    assert "Wipe PIN is less than 16 characters" in caplog.text


async def test_lock_message_update(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test lock message update."""
    await setup_integration(hass, mock_fmd_api)

    # Get the entity instance
    entity = hass.data[DOMAIN]["test_entry_id"]["lock_message_text"]

    # Update value
    await entity.async_set_value("Return to owner")

    # Verify state
    state = hass.states.get("text.fmd_test_user_lock_message")
    assert state is not None
    assert state.state == "Return to owner"

    # Verify config entry updated
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.data["lock_message_native_value"] == "Return to owner"


async def test_wipe_pin_empty_error(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test wipe PIN empty error."""
    await setup_integration(hass, mock_fmd_api)

    # Get the entity instance
    entity = hass.data[DOMAIN]["test_entry_id"]["wipe_pin_text"]

    # Test empty PIN
    with pytest.raises(ValueError) as excinfo:
        await entity.async_set_value("")
    assert "PIN cannot be empty" in str(excinfo.value)
