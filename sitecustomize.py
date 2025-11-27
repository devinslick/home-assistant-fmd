"""Test harness bootstrap tweaks.

Historically we disabled pytest's auto plugin loading globally to avoid
third-party plugins (like pytest-socket) interfering with Windows event loop
creation. That suppression also prevented required plugins (e.g.
pytest-homeassistant-custom-component) from auto-loading on Linux CI, leading
to missing fixtures (hass, enable_custom_integrations).

We now scope the disabling to Windows only. On Linux runners we allow normal
plugin auto-discovery so Home Assistant fixtures are available without manual
"-p" flags.
"""
import sys

if sys.platform.startswith("win"):
    # Only disable auto plugin loading on Windows to avoid pytest-socket issues.
    # os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    pass
