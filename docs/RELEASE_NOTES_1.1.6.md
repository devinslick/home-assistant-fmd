# Home Assistant FMD 1.1.6 — Python 3.13 Support & PIN Updates

Maintenance release adding Python 3.13 support and updating PIN requirements.

## Highlights

- 🐍 **Python 3.13 Support**: Test suite and CI updated to target Python 3.13, ensuring compatibility with future Home Assistant versions.
- 🔐 **Wipe PIN Update**: Relaxed the recommended Wipe PIN length from 16 to 8 characters, matching updated upstream FMD server recommendations.

## What’s Changed

- **CI/CD**: Updated GitHub Actions `tests.yml` to run exclusively on Python 3.13, dropping 3.11 and 3.12 from the test matrix to align with Home Assistant 2026.x requirements.
- **Documentation**: Updated `README.md` and inline comments to reflect the new 8+ character PIN recommendation.
- **Logic**: Updated PIN validation warning in `text.py` to trigger only when PIN is shorter than 8 characters (previously 16).

## Upgrade Notes

1. Update via HACS (or pull 1.1.6) and restart Home Assistant.
2. No configuration changes required.

## Compatibility
- Home Assistant: Tested with 2026.1.1+ (Python 3.13)
- Dependency: `fmd-api==2.0.7`

## Quality
- Tests updated to pass on Python 3.13.
