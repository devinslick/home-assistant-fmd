"""Test FMD config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_ID, CONF_PASSWORD, CONF_URL
from homeassistant.core import HomeAssistant

from custom_components.fmd.const import DEFAULT_POLLING_INTERVAL, DOMAIN


async def test_form(hass: HomeAssistant, mock_fmd_api: AsyncMock) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "custom_components.fmd.config_flow.authenticate_and_get_locations",
        return_value=[{"lat": 37.7749, "lon": -122.4194}],
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_URL: "https://fmd.example.com",
                CONF_ID: "test_user",
                CONF_PASSWORD: "test_password",
                "polling_interval": 30,
                "allow_inaccurate_locations": False,
                "use_imperial": False,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "test_user"
    assert result2["data"] == {
        CONF_URL: "https://fmd.example.com",
        CONF_ID: "test_user",
        CONF_PASSWORD: "test_password",
        "polling_interval": 30,
        "allow_inaccurate_locations": False,
        "use_imperial": False,
    }


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.fmd.config_flow.authenticate_and_get_locations",
        side_effect=Exception("Authentication failed"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_URL: "https://fmd.example.com",
                CONF_ID: "test_user",
                CONF_PASSWORD: "wrong_password",
                "polling_interval": 30,
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.fmd.config_flow.authenticate_and_get_locations",
        side_effect=ConnectionError("Cannot reach server"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_URL: "https://invalid.example.com",
                CONF_ID: "test_user",
                CONF_PASSWORD: "test_password",
                "polling_interval": 30,
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_default_values(
    hass: HomeAssistant, mock_fmd_api: AsyncMock
) -> None:
    """Test default values are set correctly."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.fmd.config_flow.authenticate_and_get_locations",
        return_value=[{"lat": 37.7749, "lon": -122.4194}],
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

    assert result2["data"]["polling_interval"] == DEFAULT_POLLING_INTERVAL
    assert result2["data"]["allow_inaccurate_locations"] is False
    assert result2["data"]["use_imperial"] is False


async def test_authenticate_api_error(hass: HomeAssistant) -> None:
    """Test authenticate_and_get_locations with API error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.fmd.config_flow.authenticate_and_get_locations",
        side_effect=TimeoutError("API timeout"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_URL: "https://fmd.example.com",
                CONF_ID: "test_user",
                CONF_PASSWORD: "test_password",
                "polling_interval": 30,
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_authenticate_and_get_locations_success(mock_fmd_api: AsyncMock) -> None:
    """Test authenticate_and_get_locations function directly."""
    from custom_components.fmd.config_flow import authenticate_and_get_locations

    # Mock FmdApi.create to return our mock instance
    mock_fmd_api.get_all_locations.return_value = [
        {"lat": 37.7749, "lon": -122.4194, "time": "2025-10-24T13:20:00Z"}
    ]

    with patch(
        "custom_components.fmd.config_flow.FmdApi.create", return_value=mock_fmd_api
    ):
        locations = await authenticate_and_get_locations(
            "https://fmd.example.com", "test_user", "test_password"
        )

    assert len(locations) == 1
    assert locations[0]["lat"] == 37.7749
    mock_fmd_api.get_all_locations.assert_called_once_with(
        num_to_get=1, skip_empty=True
    )
