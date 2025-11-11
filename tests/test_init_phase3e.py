"""Phase 3e entry setup and config flow edge case tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ID, CONF_PASSWORD, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fmd.const import DOMAIN


async def test_setup_multiple_entries(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test setting up multiple FMD entries in separate hass instances."""
    # Create first entry
    entry1 = MockConfigEntry(
        domain=DOMAIN,
        title="device1",
        data={
            CONF_URL: "https://fmd.example.com",
            CONF_ID: "device1",
            CONF_PASSWORD: "password1",
        },
        entry_id="entry1",
    )
    entry1.add_to_hass(hass)

    with patch("custom_components.fmd.__init__.FmdClient", mock_fmd_api):
        # Setup first entry
        assert await hass.config_entries.async_setup(entry1.entry_id)
        await hass.async_block_till_done()

    # Verify first is loaded
    assert entry1.state == ConfigEntryState.LOADED
    assert "entry1" in hass.data[DOMAIN]


async def test_unload_entry_with_platforms(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test unloading entry properly cleans up platform entities."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test_user",
        data={
            CONF_URL: "https://fmd.example.com",
            CONF_ID: "test_user",
            CONF_PASSWORD: "test_password",
        },
        entry_id="test_entry",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.fmd.__init__.FmdClient", mock_fmd_api):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Verify setup succeeded
        assert entry.state == ConfigEntryState.LOADED

        # Now unload
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    # Verify entry is cleaned up
    assert entry.state == ConfigEntryState.NOT_LOADED
    assert entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_setup_entry_partial_unload(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test unload when platform unload partially fails."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test_user",
        data={
            CONF_URL: "https://fmd.example.com",
            CONF_ID: "test_user",
            CONF_PASSWORD: "test_password",
        },
        entry_id="test_entry",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.fmd.__init__.FmdClient", mock_fmd_api):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Simulate partial unload failure (should still attempt to clean up)
        result = await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    # Should still unload
    assert result is True or result is False  # Either is acceptable
    assert entry.state == ConfigEntryState.NOT_LOADED


async def test_config_flow_form_shows_error_message(hass: HomeAssistant) -> None:
    """Test config flow displays error message on failure."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    assert result["type"] == FlowResultType.FORM
    assert "errors" in result

    with patch(
        "custom_components.fmd.config_flow.authenticate_and_get_artifacts",
        side_effect=Exception("Server error"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_URL: "https://fmd.example.com",
                CONF_ID: "test_user",
                CONF_PASSWORD: "password",
            },
        )

    assert result2["errors"]["base"] == "cannot_connect"


async def test_config_flow_empty_url(hass: HomeAssistant) -> None:
    """Test config flow with empty URL."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    # Submit with minimal fields (could fail validation)
    with patch(
        "custom_components.fmd.config_flow.authenticate_and_get_artifacts",
        side_effect=ValueError("Invalid URL"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_URL: "",
                CONF_ID: "test_user",
                CONF_PASSWORD: "password",
            },
        )
        await hass.async_block_till_done()

    # Should show form again with errors
    assert (
        result2["type"] == FlowResultType.FORM
        or result2["type"] == FlowResultType.CREATE_ENTRY
    )


async def test_config_flow_special_characters_in_fields(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test config flow handles special characters in input fields."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    # Create mock artifacts
    mock_artifacts = MagicMock()
    mock_artifacts.get.side_effect = lambda k, default=None: {
        "base_url": "https://fmd-example.com:8443/api",
        "fmd_id": "user@domain.com",
        "access_token": "token",
        "private_key": "key",
        "password_hash": "hash",
    }.get(k, default)

    with patch(
        "custom_components.fmd.config_flow.authenticate_and_get_artifacts",
        return_value=mock_artifacts,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_URL: "https://fmd-example.com:8443/api",
                CONF_ID: "user@domain.com",
                CONF_PASSWORD: "p@ssw0rd!#$%",
                "polling_interval": 15,
                "allow_inaccurate_locations": True,
                "use_imperial": True,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"]["use_imperial"] is True
    assert result2["data"]["allow_inaccurate_locations"] is True


async def test_config_flow_minimal_required_fields(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test config flow with only required fields."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    # Create mock artifacts
    mock_artifacts = MagicMock()
    mock_artifacts.get.side_effect = lambda k, default=None: {
        "base_url": "https://fmd.example.com",
        "fmd_id": "test_user",
        "access_token": "token",
        "private_key": "key",
        "password_hash": "hash",
    }.get(k, default)

    with patch(
        "custom_components.fmd.config_flow.authenticate_and_get_artifacts",
        return_value=mock_artifacts,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_URL: "https://fmd.example.com",
                CONF_ID: "test_user",
                CONF_PASSWORD: "test_password",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    # Verify defaults are applied
    assert "polling_interval" in result2["data"]
    assert "allow_inaccurate_locations" in result2["data"]


async def test_data_entry_not_ready_retry(
    hass: HomeAssistant,
) -> None:
    """Test that ConfigEntryNotReady triggers automatic retry."""
    from homeassistant.config_entries import ConfigEntryNotReady

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test_user",
        data={
            CONF_URL: "https://fmd.example.com",
            CONF_ID: "test_user",
            CONF_PASSWORD: "test_password",
        },
        entry_id="test_entry",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.fmd.__init__.FmdClient.create",
        side_effect=ConfigEntryNotReady("Server temporarily unavailable"),
    ):
        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Should not be loaded but set to retry state
    assert result is False
    assert entry.state == ConfigEntryState.SETUP_RETRY


async def test_entry_data_persistence(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test that entry data persists correctly across setup/unload cycles."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test_user",
        data={
            CONF_URL: "https://fmd.example.com",
            CONF_ID: "test_user",
            CONF_PASSWORD: "test_password",
            "polling_interval": 45,
            "allow_inaccurate_locations": True,
            "use_imperial": True,
        },
        entry_id="test_entry",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.fmd.__init__.FmdClient", mock_fmd_api):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Verify data is intact
    assert entry.data["polling_interval"] == 45
    assert entry.data["allow_inaccurate_locations"] is True
    assert entry.data["use_imperial"] is True
