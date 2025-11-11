# Home Assistant FMD 1.1.0 — Security and API Upgrade (fmd_api 2.0.4)

A security-focused release that adopts `fmd_api` 2.0.4, switches to password-free authentication, and hardens photo handling, device control, and config flow reliability. Also adds HACS/Hassfest workflows and improves test coverage and resilience.

## Highlights

- 🔐 Password-free authentication (secure artifacts, no raw password storage)
- 📸 Updated photo pipeline (`get_picture_blobs()` + `decode_picture()`)
- 🧷 Device wipe now requires validated PIN + safety switch (auto-disable)
- 💬 Lock command supports optional lock-screen message
- 🧪 Test coverage improved to ~95% with new edge-case tests
- 🛠 Added HACS + Hassfest GitHub Actions workflows and repository metadata
- 🪪 Better error mapping and resilience in config flow and command buttons

## What’s New

### Authentication Model
- Stores exported authentication artifacts (token, private key, password hash, issued timestamp) instead of raw password.
- Automatic migration of existing config entries on startup.
- Reauth flow continues seamlessly using artifacts.

### Photo Handling
- Uses modern API (`device.get_picture_blobs()` + `device.decode_picture()`).
- Filenames include EXIF `DateTimeOriginal` timestamp when available; falls back to content hash.
- Duplicate prevention via SHA-256 content hash (skip existing files).
- Auto-cleanup deletes oldest photos beyond retention limit.

### Device Control Enhancements
- Lock supports optional message via `text.fmd_<id>_lock_message` (sanitized by client).
- Wipe command requires `text.fmd_<id>_wipe_pin` (alphanumeric, no spaces) and always passes `confirm=True`.
- Safety switch auto-disables after successful wipe to prevent repeat execution.

### Location Update Logic
- Location provider derived from select entity; defaults to `all` if select state missing.
- High-frequency mode requests fresh location each poll; interval changes apply immediately.

### Repository & CI
- Added `hacs.yml` and `hassfest.yml` workflows.
- Added `hacs.json`; normalized `manifest.json` ordering to satisfy hassfest.
- README expanded/validated for HACS structure (installation, security, attribution, FAQ).

## Improvements

- Robust EXIF parsing (multiple tag fallback; null-byte stripping).
- Safe media directory resolution (`/media` fallback to `config/media`).
- Cleanup routine continues after individual unlink failures.
- Better exception specificity in photo download, ring, lock, wipe flows.
- Artifact normalization prevents MagicMock serialization errors in config flow tests.
- Reduced test flakiness by avoiding illegal await patterns in sync HA helpers.

## Fixes

- Phase 3e config flow failures resolved (artifact dict normalization).
- Removed improper `await` usage on sync HA helpers in new tests.
- Duplicate photo skip branch covered; cleanup error branch covered.
- Lint cleanup (unused imports) across new test files.
- Manifest key ordering adjusted to pass hassfest.

## Breaking Changes

- Device wipe now requires a validated PIN (safety improvement).
- Internal photo API updated to `fmd_api` 2.0.4 (legacy picture methods deprecated). User-facing behavior unchanged; existing automations continue to work.

## Migration & Upgrade Steps

1. Update integration (HACS or manual) and restart Home Assistant.
2. Authentication automatically migrates to artifact-based storage (no input required).
3. Set the wipe PIN in `text.fmd_<id>_wipe_pin` before using the wipe button.
4. (Optional) Set a lock message in `text.fmd_<id>_lock_message` if desired.
5. Validate that photo download and location update buttons operate normally.

## New / Updated Entities

| Entity | Purpose | Notes |
|--------|---------|-------|
| `text.fmd_<id>_wipe_pin` | Required PIN for device wipe | Alphanumeric, no spaces |
| `text.fmd_<id>_lock_message` | Optional lock-screen message | Sanitized by client |

Total entity count remains 22 per device after additions.

## Developer Notes

- Test suite extended (photo EXIF parsing, duplicate skip, cleanup resilience, provider default logic, auth/operation error mapping).
- Coverage ~95%; remaining uncovered lines are predominantly defensive logging branches.
- Config flow artifact normalization prevents cross-platform serialization issues.
- HACS workflow may require manual GitHub repo Topics (set via repository settings) for full green status.

## Known Post-Upgrade Considerations

| Area | Note | Action |
|------|------|--------|
| Wipe Command | Requires PIN + safety switch | Set PIN first |
| Photo Downloads | EXIF may be absent on some camera models | Hash-only filename fallback |
| HACS Validation | "Repository topics" warning until topics added | Add topics in GitHub settings |

## Security Enhancements Recap

- Raw password eliminated from storage (artifacts only).
- PIN validation for destructive wipe commands.
- Critical log messages around wipe operations for audit visibility.
- Graceful degradation on lock/wipe failures without crashing integration startup.

## Attribution

FMD ecosystem by the FMD-FOSS team (Nulide, Thore, and contributors). This release builds upon their secure design and extends client-side safety controls.

## Next Possible Steps

- Add device stats (network/GPS state) surfaces when API exposes them.
- Improve media management (opt-in auto-delete on server side if API permits).
- Additional localization for new security prompts and artifact migration messages.

---
Released: 2025-11-09
Dependency: `fmd-api==2.0.4`
