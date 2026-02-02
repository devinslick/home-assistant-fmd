# Home Assistant FMD 1.1.7 — Dependency Updates & Translation Fix

Maintenance release with updated dependencies and a translation validation fix.

## Highlights

- **fmd-api 2.0.8**: Upgraded to the latest fmd-api library version.
- **Translation Fix**: Fixed hassfest validation error by removing URL from translation string.

## What's Changed

- **Dependencies**: Upgraded `fmd-api` from 2.0.7 to 2.0.8.
- **CI/CD**: Bumped homeassistant pip package from 2026.1.2 to 2026.1.3.
- **Translations**: Fixed hassfest validation by removing example URL from the server URL description field in `translations/en.json`.

## Upgrade Notes

1. Update via HACS (or pull 1.1.7) and restart Home Assistant.
2. No configuration changes required.

## Compatibility
- Home Assistant: Tested with 2026.1.3+ (Python 3.13)
- Dependency: `fmd-api==2.0.8`
