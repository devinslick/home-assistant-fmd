# Windows Test Execution Guide for Home Assistant FMD Integration

This document captures the recurring troubleshooting steps needed to get the test suite running reliably on Windows. Follow these steps whenever tests unexpectedly fail to start (e.g. missing fixtures like `enable_custom_integrations`).

## 1. Python Environment
- Use a clean Python 3.12 or 3.11 environment (Conda or venv both work).
- Install test dependencies:

```powershell
pip install --upgrade pip setuptools wheel
pip install -r requirements_test.txt
```

Verify key packages:
```powershell
python -c "import pytest, pytest_homeassistant_custom_component; print(pytest.__version__)"
```

## 2. Plugin Autoload vs `sitecustomize.py`
On Windows the repository's `sitecustomize.py` sets:
```python
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
```
This disables auto-loading of ALL pytest plugins, including `pytest-homeassistant-custom-component`, which provides critical fixtures (`hass`, `enable_custom_integrations`).

### Symptoms When Disabled
- Errors like: `fixture 'enable_custom_integrations' not found`
- All tests error during collection/setup.

### Workaround Options
1. Temporarily rename or remove `sitecustomize.py` before running tests:
   ```powershell
   Rename-Item .\sitecustomize.py sitecustomize.py.bak
   ```
2. Or override the env var in the shell:
   ```powershell
   $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=""
   ```

Option 1 (rename) is more reliable because plugin discovery happens very early.

After tests finish, restore the file:
```powershell
Rename-Item .\sitecustomize.py.bak sitecustomize.py
```

## 3. PYTHONPATH
Ensure the repository root is on `PYTHONPATH` so custom integrations and the test support helpers resolve:
```powershell
$env:PYTHONPATH = "$(Get-Location)"
```
(If invoking from the repo root, this is usually not required, but explicitly setting it avoids edge cases.)

## 4. Running Tests
Minimal invocation (after handling plugin autoload):
```powershell
python -m pytest -v
```
Target a single test for faster iteration:
```powershell
python -m pytest tests\test_button.py::test_lock_button_with_message -xvs
```
Generate coverage (matches CI configuration):
```powershell
python -m pytest --cov=custom_components.fmd --cov-report=term-missing
```

## 5. Common Issues & Fixes
| Issue | Cause | Resolution |
|-------|-------|------------|
| `fixture 'enable_custom_integrations' not found` | Plugin autoload disabled | Rename `sitecustomize.py` or clear env var |
| All Home Assistant fixtures missing | Same as above | Same fix |
| Import errors for `test_support.enable_sockets_plugin` | PYTHONPATH not set, plugin not loaded | Set `$env:PYTHONPATH` and ensure plugin autoload works |
| Device-related button tests failing after API change | `Device` class instantiation change (`tracker.api.device` vs `Device(...)`) | Ensure tests' `conftest.py` patches `custom_components.fmd.button.Device` |

## 6. Device Class Mocking (Post fmd_api 2.0.4)
The integration now directly instantiates `Device(tracker.api, id)`. Tests must patch the class at the import location:
```python
patch("custom_components.fmd.button.Device", MagicMock(side_effect=lambda *a, **k: mock_device))
```
Make sure both:
- `api_instance.device = MagicMock(return_value=mock_device)` (backwards compatibility)
- The class patch returns the same `mock_device`

## 7. Quick Diagnostic Checklist
Run these when things break unexpectedly:
```powershell
# 1. Confirm plugin autoload disabled state
Get-Content .\sitecustomize.py | Select-String PYTEST_DISABLE_PLUGIN_AUTOLOAD

# 2. Temporarily disable it
Rename-Item .\sitecustomize.py sitecustomize.py.bak

# 3. Verify plugin imports
python - <<'PY'
import importlib
for mod in ["pytest_homeassistant_custom_component", "pytest"]:
    try:
        m = importlib.import_module(mod)
        print(f"Loaded {mod}: {m}")
    except Exception as e:
        print(f"FAILED {mod}: {e}")
PY

# 4. Run a single test
python -m pytest tests\test_button.py::test_location_update_button -xvs

# 5. Restore sitecustomize
Rename-Item .\sitecustomize.py.bak sitecustomize.py
```

## 8. CI vs Windows Local Differences
CI (Ubuntu) does NOT disable plugin autoload. If a test fails locally only because fixtures are missing, suspect Windows autoload suppression first.

## 9. Recommended Script (Optional)
Create `scripts\run-tests-win.ps1` for convenience:
```powershell
# Rename if present
if (Test-Path .\sitecustomize.py) { Rename-Item .\sitecustomize.py sitecustomize.py.bak }
$env:PYTHONPATH = "$(Get-Location)"
python -m pytest --cov=custom_components.fmd --cov-report=term-missing @Args
if (Test-Path .\sitecustomize.py.bak) { Rename-Item .\sitecustomize.py.bak sitecustomize.py }
```
Run:
```powershell
pwsh .\scripts\run-tests-win.ps1
```

## 10. Summary
- Windows `sitecustomize.py` disables plugin autoload → hides Home Assistant fixtures.
- Rename or neutralize it before test runs.
- Patch `Device` class after fmd_api 2.0.4 upgrade.
- Always ensure `PYTHONPATH` includes repo root for `test_support` and custom component discovery.

Keeping these steps documented should eliminate repetitive troubleshooting cycles.
