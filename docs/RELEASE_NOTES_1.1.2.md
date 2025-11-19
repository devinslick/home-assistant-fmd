# Home Assistant FMD 1.1.2 — Polling Reliability & Maintenance

A maintenance release focused on improving location tracking reliability and updating core dependencies.

## Highlights

- 🔄 **Improved Polling Logic**: Device tracker now actively requests fresh location data from the device during every poll.
- 🛡️ **Schedule Reliability**: Added protection against overlapping updates to prevent task pile-ups.
- 📦 **Dependency Update**: Updated to `fmd-api==2.0.5`.

## What’s Changed

### Active Location Polling
- Previously, the normal polling interval (default 30 min) only fetched the *cached* location from the FMD server.
- **Now**, every poll triggers a `request_location` command to the device first, waits for it to report, and *then* fetches the updated location.
- This ensures the location data in Home Assistant is current, rather than potentially stale server cache.

### Polling Overlap Protection
- Added a guard mechanism to prevent a new polling cycle from starting if the previous one is still in progress.
- This resolves issues where the schedule could become unreliable or stop working if the FMD server or device was slow to respond.

### Dependency Updates
- Updated `fmd-api` from `2.0.4` to `2.0.5`.

## Upgrade Notes

1. Update via HACS (or pull the 1.1.2 release) and restart Home Assistant.
2. No configuration changes required.
3. **Note on Battery**: Because the integration now actively requests location from the device on every poll (instead of just reading server cache), this may have a slightly higher battery impact on the Android device if you have a very frequent polling interval set. The default of 30 minutes is still recommended.

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
