# Home Assistant FMD 1.1.1 — Button Reliability Hotfix

A small maintenance release that fixes button actions introduced by the 1.1.0 / fmd_api 2.0.4 upgrade and adds Windows test documentation. No configuration changes required.

## Highlights

- ✅ Restores functionality of affected buttons:
  - Lock device
  - Photo: Download
  - Wipe: Execute (safety switch + PIN still required)
- 🧪 Test suite updates to match new `Device(...)` usage and verify lock message handling
- 📄 New Windows test execution guide: `docs/TESTS_WINDOWS.md`

## What’s Fixed

### Device Construction (fmd_api 2.0.4)
- Corrects the integration to construct the device as `Device(client, device_id)` instead of calling a non-existent `client.device()` method.
- Affected entities now work as expected:
  - Lock device button
  - Photo: Download button
  - Wipe: Execute button

### Lock Message Handling
- Confirms `lock(message=...)` is passed as a keyword argument and adds explicit test coverage.
- Note: If you were already on 1.1.0, this may not change behavior; the primary runtime fix in 1.1.1 is the `Device(...)` construction for the affected buttons.

### Tests & Tooling
- Tests patched to mock `custom_components.fmd.button.Device` so the same `mock_device` is returned on constructor calls.
- Added `docs/TESTS_WINDOWS.md` with recurring Windows-specific pytest troubleshooting steps (plugin autoload vs `sitecustomize.py`, PYTHONPATH, invocation examples).

## Upgrade Notes

1. Update via HACS (or pull the 1.1.1 release) and restart Home Assistant.
2. No configuration changes required.
3. Optional: If you use a lock-screen message, verify the `text.fmd_<id>_lock_message` entity and press the Lock button to confirm behavior.

## Compatibility
- Home Assistant: same as 1.1.0
- Dependency: `fmd-api==2.0.4` (unchanged)
- No breaking changes.

## Quality & Coverage
- All tests pass locally (253/253) with coverage ~95%.
- Button flows specifically exercised (success, error handling, message argument, wipe safety).

## Acknowledgements
Thanks to users who reported the button regressions and helped validate the hotfix quickly.

---
Released: 2025-11-11
Dependency: `fmd-api==2.0.4`
