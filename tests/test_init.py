"""Test FMD integration setup."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_ID
from homeassistant.core import HomeAssistant

from custom_components.fmd.const import DOMAIN


async def test_setup_entry(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test setting up the integration."""
    config_entry = MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="test_user",
        data={
            CONF_URL: "https://fmd.example.com",
            CONF_ID: "test_user",
            CONF_PASSWORD: "test_password",
            "polling_interval": 30,
            "allow_inaccurate_locations": False,
            "use_imperial": False,
        },
        entry_id="test_entry_id",
        unique_id="test_user",
    )
    config_entry.add_to_hass(hass)

    with patch("custom_components.fmd.__init__.FmdApi", mock_fmd_api):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert config_entry.entry_id in hass.data[DOMAIN]
    assert "api" in hass.data[DOMAIN][config_entry.entry_id]
    assert "device_info" in hass.data[DOMAIN][config_entry.entry_id]


async def test_unload_entry(
    hass: HomeAssistant,
    mock_fmd_api: AsyncMock,
) -> None:
    """Test unloading the integration."""
    config_entry = MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="test_user",
        data={
            CONF_URL: "https://fmd.example.com",
            CONF_ID: "test_user",
            CONF_PASSWORD: "test_password",
            "polling_interval": 30,
        },
        entry_id="test_entry_id",
        unique_id="test_user",
    )
    config_entry.add_to_hass(hass)

    with patch("custom_components.fmd.__init__.FmdApi", mock_fmd_api):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.NOT_LOADED
    assert config_entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_setup_entry_api_failure(
    hass: HomeAssistant,
) -> None:
    """Test setup fails when API creation fails."""
    config_entry = MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="test_user",
        data={
            CONF_URL: "https://fmd.example.com",
            CONF_ID: "test_user",
            CONF_PASSWORD: "wrong_password",
            "polling_interval": 30,
        },
        entry_id="test_entry_id",
        unique_id="test_user",
    )
    config_entry.add_to_hass(hass)

    with patch(
        "custom_components.fmd.__init__.FmdApi.create",
        side_effect=Exception("Authentication failed"),
    ):
        assert not await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.SETUP_ERROR
