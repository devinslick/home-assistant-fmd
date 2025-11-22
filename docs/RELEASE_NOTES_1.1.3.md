# Home Assistant FMD 1.1.3 — Polling Fixes & Code Quality

A release focused on fixing polling interval persistence and improving code quality with strict typing.

## Highlights

- 🐛 **Fix: Polling Interval Persistence**: Custom polling intervals (e.g., 1 minute) now correctly persist across restarts.
- 🧹 **Strict Typing**: Comprehensive type hinting added to `device_tracker.py` for better code stability.
- 🛡️ **Robust Configuration**: Enhanced type safety when reading configuration values during startup.

## What’s Changed

### Fix: Polling Interval Persistence
- Fixed a bug where custom polling intervals (Normal and High Frequency) would revert to defaults (30m / 5m) after a Home Assistant restart.
- The integration now correctly prioritizes the saved values from the number entities (`update_interval_native_value`, `high_frequency_interval_native_value`) during startup.

### Strict Typing Improvements
- Updated `device_tracker.py` to use strict type hints (e.g., `dict[str, Any]` instead of bare `dict`).
- Added type annotations for all class attributes and method returns.
- Resolved linting warnings related to protected member access and implicit types.

### Configuration Safety
- `async_setup_entry` now explicitly casts configuration values (polling intervals, booleans) to their correct types.
- This adds an extra layer of safety against malformed configuration data.

### Refactoring
- Refactored `async_update` to use safer local variable handling for location data.
- Improved `extra_state_attributes` to safely handle cases where location data might be missing.

## Upgrade Notes

1. Update via HACS (or pull the 1.1.3 release) and restart Home Assistant.
2. No configuration changes required.

## Compatibility
- Home Assistant: same as 1.1.0+
- Dependency: `fmd-api==2.0.5`
- No breaking changes.

## Quality & Coverage
- All tests pass locally.
- Verified fix for interval persistence.

---
Released: 2025-11-19
Dependency: `fmd-api==2.0.5`
