"""Pytest plugin to force-enable sockets before other plugins run.

This avoids pytest_socket from blocking asyncio event loop creation on Windows.
"""
import pytest

try:
    import pytest_socket
except Exception:  # pragma: no cover - plugin import guard
    pytest_socket = None  # type: ignore

if pytest_socket:
    # Force enable sockets immediately
    pytest_socket.enable_socket()

    # Monkeypatch disable_socket to a no-op so later imports can't re-disable
    def _no_disable_socket(*args, **kwargs):  # pragma: no cover - trivial shim
        return None

    pytest_socket.disable_socket = _no_disable_socket  # type: ignore[attr-defined]


# Expose a trivial hook to make this a valid plugin module
@pytest.hookimpl
def pytest_configure(config):  # pragma: no cover - no-op hook
    return None
