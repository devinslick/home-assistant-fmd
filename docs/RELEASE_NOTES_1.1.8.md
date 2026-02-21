# Home Assistant FMD 1.1.8 — Dependency Update

Maintenance release with updated fmd-api dependency.

## Highlights

- **fmd-api 2.0.9**: Upgraded to the latest fmd-api library version which now allows HTTP connections.  Updated documentation to reflect that HTTPS is no longer required.
- **homeassistant**: Updated homeassistant pip package to 2026.2.3 for testing

## What's Changed

- **Dependencies**: Upgraded `fmd-api` from 2.0.8 to 2.0.9.

## Upgrade Notes

1. Update via HACS (or pull 1.1.8) and restart Home Assistant.
2. No configuration changes required.

## Compatibility
- Home Assistant: Tested with 2026.2.3+ (Python 3.13)
- Dependency: `fmd-api==2.0.9`
