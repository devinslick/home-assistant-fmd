"""Additional tests for __init__ error branches and artifact export."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fmd_api import FmdApiException
from homeassistant.const import CONF_ID, CONF_URL
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fmd.const import DOMAIN


async def test_setup_entry_artifact_export_success(
    hass, mock_fmd_api: AsyncMock
) -> None:
    """When create succeeds and export_auth_artifacts returns artifacts, entry is updated."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="FMD test_user",
        data={
            CONF_URL: "https://fmd.example.com",
            CONF_ID: "test_user",
            "password": "test_password",
            "id": "test_user",
        },
        source="user",
        unique_id="test_user",
    )
    entry.add_to_hass(hass)

    # Ensure create returns an API where export_auth_artifacts returns a dict
    api = AsyncMock()
    api.export_auth_artifacts = AsyncMock(return_value={"a": "b"})
    api.get_locations = AsyncMock(return_value=[{}])

    create_mock = AsyncMock(return_value=api)

    with patch("custom_components.fmd.FmdClient.create", create_mock):
        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert result is True
    # Entry data should now include artifacts and not contain password
    new_entry = hass.config_entries.async_get_entry(entry.entry_id)
    assert "artifacts" in new_entry.data
    assert "password" not in new_entry.data


async def test_setup_entry_from_artifacts_raises_fmdapi_exception(
    hass, mock_fmd_api: AsyncMock
) -> None:
    """If from_auth_artifacts raises FmdApiException, setup should retry (ConfigEntryNotReady)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="FMD test_user",
        data={
            "artifacts": {"mock": "data"},
            "id": "test_user",
        },
        source="user",
        unique_id="test_user",
    )
    entry.add_to_hass(hass)

    # Make from_auth_artifacts raise a FmdApiException
    with patch(
        "custom_components.fmd.FmdClient.from_auth_artifacts",
        side_effect=FmdApiException("server error"),
    ):
        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Setup should not succeed and entry should indicate retry
    assert not result
    assert entry.state is not None


async def test_unload_entry_close_api_exception_logged(
    hass, mock_fmd_api: AsyncMock, caplog
) -> None:
    """If api.close raises, the unload should still succeed but log a warning."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="FMD test_user",
        data={
            CONF_URL: "https://fmd.example.com",
            CONF_ID: "test_user",
            CONF_URL: "https://fmd.example.com",
            "password": "test_password",
        },
        entry_id="test_entry_id",
        unique_id="test_user",
    )
    entry.add_to_hass(hass)

    # Use the existing mock but patch its close to raise
    mock_api = mock_fmd_api.create.return_value

    async def close_raises():
        raise Exception("close failed")

    mock_api.close.side_effect = close_raises

    with patch("custom_components.fmd.FmdClient", mock_fmd_api):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Unload should succeed and log warning
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    assert any("Error closing FMD API client" in r.message for r in caplog.records)
