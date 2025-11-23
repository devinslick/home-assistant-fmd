# Copilot Instructions for Home Assistant FMD Integration

## Project Overview
- This is a Home Assistant custom integration for the FMD (Find My Device) ecosystem, enabling device tracking and remote control of Android devices via a self-hosted FMD server.
- The integration is structured as a Home Assistant component in `custom_components/fmd/` and exposes 20 entities per device (trackers, buttons, switches, selects, numbers, sensors).
- The integration communicates with the FMD server using the `fmd_api` PyPI package (see requirements).

## Key Architectural Patterns
- **Entity-Driven:** Each device is represented by a set of Home Assistant entities (see README for full list and entity ID conventions).
- **Async/Await:** All I/O and Home Assistant API calls are async; use `async def` and `await` for all entity methods and setup.
- **API Abstraction:** All FMD server communication is abstracted via the `FmdClient` class (mocked in tests).
- **Config Flow:** User configuration is handled via Home Assistant's config flow system (`config_flow.py`).
- **Media Handling:** Photos are downloaded, decrypted, and stored in `/media/fmd/<device-id>/` or `/config/media/fmd/<device-id>/` with EXIF timestamp extraction.
- **Safety Mechanisms:** Destructive actions (e.g., device wipe) require a safety switch and are logged with CRITICAL severity.

## Developer Workflows
- **Testing:**
  - Use `pytest` and `pytest-homeassistant-custom-component` for all tests.
  - Run all tests: `pytest`
  - Run with coverage: `pytest --cov=custom_components.fmd --cov-report=html --cov-report=term-missing`
  - Test fixtures and helpers are in `tests/conftest.py`.
  - All FMD API calls are mocked; see `mock_fmd_api` fixture for details.
- **Linting/Formatting:**
  - Pre-commit hooks run `black`, `flake8`, and `isort`.
  - Run `black .` and `flake8 .` before committing.
- **CI:**
  - GitHub Actions run tests and coverage on push/PR.
  - Python 3.11+ is required.

## Project-Specific Conventions
- **Entity IDs:** All entities are prefixed with `fmd_<device_id>`; hyphens in device IDs are converted to underscores.
- **Select Entities:** Use a placeholder option (e.g., "Send Command...") and reset to it after sending a command.
- **Photo Filenames:** Use EXIF `DateTimeOriginal` if available, else fallback to content hash.
- **Wipe Command:** Requires safety switch; disables itself after use or timeout.
- **No State Feedback:** Most command entities (Bluetooth, DND, Ringer) are fire-and-forget; state is not tracked.
- **Error Handling:** All API/network errors are logged; platform-level failures do not raise `ConfigEntryNotReady` (integration-level only).

## Key Files & Directories
- `custom_components/fmd/` — Main integration code (entities, config flow, constants)
- `tests/` — All tests, fixtures, and coverage extensions
- `requirements_test.txt` — Test dependencies (pytest, pytest-homeassistant-custom-component, etc.)
- `README.md` — Full documentation, entity list, and developer notes

## External Dependencies
- `fmd_api` (PyPI) — All FMD server communication
- `pytest-homeassistant-custom-component` — For integration testing
- `Pillow` — For EXIF/photo handling

## Examples
- To add a new entity, subclass the appropriate Home Assistant entity class and register in `async_setup_entry`.
- To test a new API command, add a method to the `FmdClient` mock in `conftest.py` and write a test in `tests/`.
- To update photo handling, adjust EXIF logic in `button.py` and update tests to patch `Image.open`.
- All code changes should have test coverage; aim for 95%+ overall coverage.

---

For more details, see `README.md` and `tests/conftest.py`.
