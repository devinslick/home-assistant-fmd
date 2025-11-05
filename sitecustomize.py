"""Test harness bootstrap tweaks.

We disable pytest's auto plugin loading to avoid third-party plugins (like
pytest-socket) interfering with Home Assistant's asyncio event loop on Windows.
Required plugins are loaded explicitly via tests/conftest.py.
"""
import os

os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
