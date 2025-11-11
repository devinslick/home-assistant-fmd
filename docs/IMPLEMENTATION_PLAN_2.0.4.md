# Implementation Plan: fmd_api 2.0.4 Integration

Date: 2025-11-09
Target: Adopt all new features and improvements from fmd_api 2.0.4

## Overview

This document outlines the comprehensive plan to integrate all improvements from fmd_api 2.0.4 into the Home Assistant FMD integration.

## Priority Order

1. **Authentication artifacts** (most impactful for security)
2. **Picture API migration** (required to avoid deprecation warnings)
3. **Error handling improvements** (better UX)
4. **Wipe PIN validation** (safety)
5. **Lock message support** (new feature)
6. **Documentation updates** (user-facing)
7. **Test updates** (ensure quality)

## Detailed Implementation Tasks

### 1. Password-Free Authentication with Artifacts (HIGHEST PRIORITY)

**Security Benefit:** Eliminates raw password storage, uses secure auth artifacts instead.

**Config Flow Changes (`config_flow.py`):**
- [x] Update initial setup flow:
  - Use `FmdClient.create(..., drop_password=True)` instead of retaining password
  - Immediately call `artifacts = await client.export_auth_artifacts()`
  - Persist artifacts in `config_entry.data` (mark as sensitive)
  - Remove raw password from storage after artifact export

- [x] Update reauthentication flow:
  - On successful reauth, export and persist new artifacts
  - Replace password with artifacts in config entry

- [x] Add migration logic:
  - Detect existing entries with raw password (check for 'password' key)
  - On next successful auth, convert to artifacts
  - Remove old password field from storage

**Runtime Changes (`__init__.py`):**
- [x] Update `async_setup_entry()`:
  - Check if `artifacts` exists in `config_entry.data`
  - Use `FmdClient.from_auth_artifacts(artifacts)` for startup
  - Fall back to password-based auth if migrating (temporary)

- [x] Handle 401 token expiry:
  - If artifacts include `password_hash`, client auto-reauths (no action needed)
  - If artifacts missing password_hash, trigger reauth flow

- [x] Cleanup on unload:
  - Ensure `await client.close()` is called

**Storage Contract:**

Required artifact fields to persist:
```python
{
    "base_url": str,
    "fmd_id": str,
    "access_token": str,
    "private_key": str,  # PEM format
    "password_hash": str,  # Optional but recommended
    "session_duration": int,
    "token_issued_at": float
}
```

Mark as sensitive: `private_key`, `password_hash`, `access_token`

**Files to Update:**
- `config_flow.py` - Initial setup and reauth flows
- `__init__.py` - Client initialization
- `const.py` - Add new storage keys if needed

---

### 2. Picture API Migration (REQUIRED)

**Breaking Change:** Deprecated methods emit warnings and will be removed in future versions.

**Update Photo Download (`button.py`):**

Replace:
```python
pictures = await tracker.api.get_pictures(num_to_get=max_photos)
decrypted = await self._async_decrypt_data_blob(tracker.api, blob)
```

With:
```python
blobs = await device.get_picture_blobs(max_photos)
for blob in blobs:
    photo_result = await device.decode_picture(blob)
    # photo_result.data = bytes
    # photo_result.mime_type = str (e.g., "image/jpeg")
    # photo_result.timestamp = datetime | None
    # photo_result.raw = dict (raw server response)
```

**Changes Required:**
- Remove calls to deprecated methods:
  - `device.get_pictures()`
  - `device.fetch_pictures()`
  - `device.download_photo()`
  - `device.get_picture()`

- Update EXIF extraction logic to work with `PhotoResult` structure
- Ensure MIME type detection works with new `mime_type` field
- Use `photo_result.timestamp` if available (fallback to EXIF extraction)

**Files to Update:**
- `button.py` - Photo download button implementation

---

### 3. Wipe PIN Validation (SAFETY)

**Safety Feature:** Ensures wipe command has proper PIN validation.

**Update Wipe Command (`button.py` or `switch.py`):**

Add PIN validation:
```python
def validate_wipe_pin(pin: str) -> bool:
    """Validate wipe PIN meets requirements."""
    if not pin:
        return False
    if not pin.isalnum():  # Alphanumeric only
        return False
    if ' ' in pin:  # No spaces
        return False
    # Don't enforce 16+ yet, but warn users
    return True
```

**Service Schema Updates:**
- Require `pin` parameter
- Add validation with clear error messages
- Always pass `confirm=True` to `device.wipe(pin, confirm=True)`
- Add warning note that future server versions may require 16+ characters

**UI/UX Improvements:**
- Clear error message: "PIN must be alphanumeric (letters and numbers only) with no spaces"
- Warning message: "Some FMD servers may require PINs of 16+ characters in the future"
- Document PIN requirements in README

**Files to Update:**
- `button.py` - Wipe button implementation
- `services.yaml` - Service schema (if applicable)

---

### 4. Lock Message Support (NEW FEATURE)

**New Feature:** Allow optional message when locking device.

**Update Lock Command (`button.py`):**

Add optional `message` parameter:
```python
async def async_press(self) -> None:
    """Handle lock button press."""
    message = self._attr_extra_state_attributes.get("message", "")
    await device.lock(message=message if message else None)
```

**Service Schema:**
- Add optional `message` field (string, max length handled by client)
- Document that client sanitizes dangerous characters automatically
- Provide automation examples

**Files to Update:**
- `button.py` - Lock button implementation
- `services.yaml` - Add message parameter schema
- `README.md` - Document lock message feature

---

### 5. Error Handling Improvements

**Better UX:** Clearer error messages, proper retry behavior.

**Platform Updates:**

**Retry Strategy:**
- Rely on client's automatic retry/backoff for GET/PUT operations
- **Never retry** unsafe POST commands (ring, lock, wipe, camera)
- Let client handle 429 (Retry-After) and 5xx backoff

**Error Messages:**
- Handle empty lists from `get_locations()` gracefully (don't error)
- Handle empty lists from `get_picture_blobs()` gracefully
- Surface user-friendly messages for common errors
- Only trigger reauth if artifacts are invalid/missing (401 with no password_hash)

**Exception Handling:**
```python
from fmd_api import FmdError, FmdAuthError, FmdConnectionError

try:
    result = await device.some_operation()
except FmdAuthError:
    # Trigger reauth flow
    raise ConfigEntryAuthFailed()
except FmdConnectionError as e:
    # Temporary network issue
    _LOGGER.warning("Connection error: %s", e)
    raise UpdateFailed(f"Cannot connect to FMD server: {e}")
except FmdError as e:
    # General API error
    _LOGGER.error("FMD API error: %s", e)
    raise HomeAssistantError(f"FMD operation failed: {e}")
```

**Files to Update:**
- `__init__.py` - Client initialization errors
- `device_tracker.py` - Location fetch errors
- `button.py` - Command errors
- All platform files - Consistent error handling

---

### 6. Documentation Updates

**Update User-Facing Documentation:**

**README.md:**
- Add section on password-free authentication (security improvement)
- Update picture API references (if mentioned)
- Document wipe PIN requirements
- Add lock message feature with examples
- Update version history for 2.0.4 adoption

**CREDITS.md:**
- Update fmd_api version reference to 2.0.4

**Release Notes:**
- Create/update release notes explaining breaking changes
- Migration guide for existing users
- Security improvements highlight

**Files to Update:**
- `README.md`
- `CREDITS.md`
- `RELEASE_NOTES_*.md`

---

### 7. Test Updates

**Update All Tests for New API:**

**Authentication Tests (`tests/test_config_flow.py`):**
- Mock `export_auth_artifacts()` return value
- Mock `from_auth_artifacts()` for resume
- Test migration from password to artifacts
- Test reauth with artifacts

**Picture Tests (`tests/test_button.py`):**
- Mock `get_picture_blobs()` return value (list of base64 strings)
- Mock `decode_picture()` return value (PhotoResult)
- Update EXIF extraction tests
- Test empty picture list handling

**Init Tests (`tests/test_init.py`):**
- Test artifact-based client creation
- Test fallback to password (during migration)
- Test 401 handling with/without password_hash

**Fixture Updates (`tests/conftest.py`):**
- Update `mock_fmd_api` fixture to include new methods
- Add `export_auth_artifacts` mock
- Add `from_auth_artifacts` mock
- Update `get_picture_blobs` and `decode_picture` mocks

**Files to Update:**
- `tests/conftest.py` - Update mocks
- `tests/test_config_flow.py` - Auth artifact tests
- `tests/test_init.py` - Client initialization tests
- `tests/test_button.py` - Picture API tests
- All test files - Update to use new API patterns

---

## Implementation Checklist

### Phase 1: Authentication Artifacts (IN PROGRESS)
- [ ] Update `config_flow.py` initial setup to use `drop_password=True`
- [ ] Update `config_flow.py` to export and persist artifacts
- [ ] Update `__init__.py` to use `from_auth_artifacts()` on startup
- [ ] Add migration logic for existing password-based entries
- [ ] Update reauth flow to use artifacts
- [ ] Test artifact-based authentication end-to-end

### Phase 2: Picture API Migration
- [ ] Replace `get_pictures()` with `get_picture_blobs()`
- [ ] Replace decrypt logic with `decode_picture()`
- [ ] Update EXIF handling for PhotoResult
- [ ] Test photo download with new API
- [ ] Ensure backward compatibility during transition

### Phase 3: Error Handling
- [ ] Review all platform error handling
- [ ] Add proper exception types from fmd_api
- [ ] Remove unsafe command retries
- [ ] Add user-friendly error messages
- [ ] Test error scenarios

### Phase 4: Safety Features
- [ ] Add wipe PIN validation
- [ ] Update wipe service schema
- [ ] Add lock message support
- [ ] Test both features

### Phase 5: Testing
- [ ] Update all test fixtures
- [ ] Update config flow tests
- [ ] Update picture tests
- [ ] Update init tests
- [ ] Verify 96%+ coverage maintained

### Phase 6: Documentation
- [ ] Update README.md
- [ ] Update CREDITS.md
- [ ] Create migration guide
- [ ] Add automation examples
- [ ] Update version history

---

## Success Criteria

- [ ] All tests passing with 96%+ coverage
- [ ] No deprecation warnings from fmd_api
- [ ] Existing users can migrate seamlessly
- [ ] New users never see raw password in storage
- [ ] Photo download works with new API
- [ ] Wipe command has proper PIN validation
- [ ] Lock command supports optional message
- [ ] Error messages are clear and actionable
- [ ] Documentation is complete and accurate

---

## Notes

- **Backward Compatibility:** Migration logic ensures existing users transition smoothly
- **Security:** Artifacts are more secure than raw passwords but still sensitive
- **Testing:** Comprehensive test updates ensure no regressions
- **Documentation:** Clear migration guide helps users understand changes
