# Home Assistant FMD 1.1.4 — Dependency Bump to `fmd-api==2.0.7`

Maintenance release updating FMD API client dependency and ensuring compatibility and stability with the latest client.

## Highlights

- 📦 **Dependency update**: Bumped `fmd-api` to **2.0.7**.
- 🧪 **Compatibility**: Verified current test suite against `fmd-api==2.0.7`; all tests passed.
- 🛠️ **Maintenance**: Minor internal improvements and maintenance updates to align with new API behavior.

## What’s Changed

- Dependency updated to `fmd-api==2.0.7` in `custom_components/fmd/manifest.json` and `requirements_test.txt`.
- No functional user-facing changes in this release; it's a dependency upgrade and compatibility maintenance release.
- Improved code test coverage from 94% to 100%!

## Upgrade Notes

1. Update via HACS (or pull 1.1.4) and restart Home Assistant.
2. No configuration changes required.

## Compatibility
- Home Assistant: same as 1.1.0+
- Dependency: `fmd-api==2.0.7`
- No breaking changes were introduced by this release.

## Quality & Coverage
- All tests pass locally with `fmd-api==2.0.7`.

---
Released: 2025-11-22
Dependency: `fmd-api==2.0.7`
