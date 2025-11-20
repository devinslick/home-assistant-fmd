# Home Assistant FMD 1.1.2 — Polling Reliability & Maintenance

A maintenance release focused on improving location tracking reliability and updating core dependencies.

## Highlights

- 🎯 **Smarter High Frequency Tracking**: High Frequency Mode now respects your "Location Source" selection (e.g., Cell Only, GPS Only) instead of always forcing "All Providers".
- 🛡️ **Schedule Reliability**: Added protection against overlapping updates to prevent task pile-ups.
- 🔄 **Improved Polling Logic**: Ensures polling tasks are managed correctly, preventing stalls if the server or device is slow to respond.
- 📦 **Dependency Update**: Updated to `fmd-api==2.0.5`.

## What’s Changed

### Smarter High Frequency Tracking
- **High Frequency Mode** now uses the provider selected in the **Location Source** entity.
- Previously, High Frequency Mode always requested "All Providers" (GPS + Network + Fused).
- Now you can select "Cell Only" to save battery during active tracking, or "GPS Only" for maximum precision.
- If the selection is unavailable, it safely defaults back to "All Providers".

### Polling Overlap Protection
- Added a guard mechanism to prevent a new polling cycle from starting if the previous one is still in progress.
- This resolves issues where the schedule could become unreliable or stop working if the FMD server or device was slow to respond.
- This ensures that the integration respects the configured polling interval more reliably.

### Fix: Interval Persistence
- Fixed an issue where custom polling intervals (e.g., 1 minute) would revert to defaults (30m normal / 5m high-freq) after a Home Assistant restart.
- The integration now correctly restores your configured intervals immediately upon startup.

### Dependency Updates
- Updated `fmd-api` from `2.0.4` to `2.0.5`.

## Upgrade Notes

1. Update via HACS (or pull the 1.1.2 release) and restart Home Assistant.
2. No configuration changes required.

## Compatibility
- Home Assistant: same as 1.1.0+
- Dependency: `fmd-api==2.0.5`
- No breaking changes.

## Quality & Coverage
- All tests pass locally.
- New tests added for polling logic and overlap protection.

---
Released: 2025-11-18
Dependency: `fmd-api==2.0.5`
