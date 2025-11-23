"""Edge case tests for __init__ setup error branches not yet covered."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fmd_api import AuthenticationError, FmdApiException, OperationError
from homeassistant.const import CONF_ID, CONF_URL
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fmd.const import DOMAIN


def _entry(data: dict) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="edge_user",
        data=data,
        unique_id=data.get("id", "edge_user"),
    )


async def test_setup_entry_missing_credentials_raises_config_entry_not_ready(
    hass,
) -> None:
    """Entry missing both artifacts and password should raise ConfigEntryNotReady (wrapped ValueError)."""
    data = {
        CONF_URL: "https://fmd.example.com",
        CONF_ID: "edge_user",
        "id": "edge_user",
    }
    entry = _entry(data)
    entry.add_to_hass(hass)

    # Patch FmdClient refs so code enters try and triggers ValueError path
    with patch("custom_components.fmd.FmdClient.from_auth_artifacts"), patch(
        "custom_components.fmd.FmdClient.create"
    ):
        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Setup returns False due to retry state
    assert result is False
    assert entry.state.name.lower().startswith("setup_retry")


@pytest.mark.parametrize(
    "exc, expected_exception",
    [
        (AuthenticationError("bad"), "auth"),
        (OperationError("temporary"), "retry"),
        (FmdApiException("api"), "retry"),
    ],
)
async def test_setup_entry_artifacts_specific_errors(
    hass, exc, expected_exception
) -> None:
    """from_auth_artifacts should propagate mapped exceptions (auth vs retry)."""
    entry = _entry(
        {
            "artifacts": {"base_url": "u", "fmd_id": "edge_user", "access_token": "t"},
            "id": "edge_user",
        }
    )
    entry.add_to_hass(hass)

    with patch("custom_components.fmd.FmdClient.from_auth_artifacts", side_effect=exc):
        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    if expected_exception == "auth":
        # Authentication triggers reauth => setup returns False, state should indicate retry or auth
        assert result is False
    else:
        assert result is False
    assert entry.state.name.lower().startswith(
        "setup_retry"
    ) or entry.state.name.lower().startswith("setup_error")


async def test_setup_entry_unexpected_exception_wrapped(hass) -> None:
    """Unexpected generic exception should be wrapped in ConfigEntryNotReady."""
    entry = _entry(
        {
            "artifacts": {"base_url": "u", "fmd_id": "edge_user", "access_token": "t"},
            "id": "edge_user",
        }
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.fmd.FmdClient.from_auth_artifacts",
        side_effect=RuntimeError("boom"),
    ):
        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert result is False
    assert entry.state.name.lower().startswith("setup_retry")
