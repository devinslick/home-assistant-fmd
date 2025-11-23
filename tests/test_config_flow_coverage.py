"""Test config flow coverage."""
from typing import Any

from custom_components.fmd.config_flow import _normalize_artifacts


def test_normalize_artifacts_with_mock_object():
    """Test _normalize_artifacts with an object that has .get() but is not a dict."""

    class MockArtifacts:
        def get(self, key: str, default: Any = None) -> Any:
            data = {
                "base_url": "http://test.url",
                "fmd_id": "test_id",
                "access_token": "token",
                "private_key": "key",
                "password_hash": "hash",
            }
            return data.get(key, default)

    mock_artifacts = MockArtifacts()

    # Ensure isinstance(mock_artifacts, dict) is False
    assert not isinstance(mock_artifacts, dict)

    # Call the function
    result = _normalize_artifacts(mock_artifacts)

    # Verify result is a dict with expected keys
    assert isinstance(result, dict)
    assert result["base_url"] == "http://test.url"
    assert result["fmd_id"] == "test_id"
    assert result["access_token"] == "token"


def test_normalize_artifacts_with_list_of_tuples() -> None:
    """Test _normalize_artifacts with a list of tuples (convertible to dict)."""
    artifacts = [("base_url", "http://example.com"), ("fmd_id", "123")]
    normalized = _normalize_artifacts(artifacts)
    assert normalized == {"base_url": "http://example.com", "fmd_id": "123"}
