# Home Assistant FMD 1.1.5 — Windows Test Suite Fixes & Documentation

Developer-focused release improving the testing experience on Windows and updating documentation.

## Highlights

- 🪟 **Windows Test Support**: Fixed critical issues preventing the test suite from running on Windows (specifically `pytest-socket` conflicts with `ProactorEventLoop`).
- 📚 **Documentation**: Updated developer documentation for Windows testing workflows (`docs/TESTS_WINDOWS.md`).
- 🧪 **Test Refactoring**: Refactored `conftest.py` and test fixtures for better cross-platform stability.

## What’s Changed

- **Test Suite Fixes**: Resolved `pytest_socket.SocketBlockedError` on Windows by selectively enabling sockets in `conftest.py` when the platform is detected. This allows the default `ProactorEventLoop` to function correctly during tests.
- **Documentation**: Updated `docs/TESTS_WINDOWS.md` with a comprehensive troubleshooting guide, covering `sitecustomize.py` plugin autoloading issues and environment setup.
- **Refactoring**: Cleaned up `tests/conftest.py` to remove ineffective event loop policy overrides and replaced them with a robust socket-enabling strategy.
- **CI/CD**: Added new workflows for version validation and enhanced test coverage reporting via Codecov.
- **Coverage**: Maintained high test coverage (99%).

## Upgrade Notes

1. Update via HACS (or pull 1.1.5) and restart Home Assistant.
2. No configuration changes required.
3. **Developers**: If running tests on Windows, please review `docs/TESTS_WINDOWS.md` for the latest setup instructions.

## Compatibility
- Home Assistant: same as 1.1.0+
- Dependency: `fmd-api==2.0.7`
- No breaking changes were introduced by this release.

## Quality & Coverage
- All tests pass locally on Windows with `fmd-api==2.0.7`.
- Test coverage remains at ~99%.

---
Released: 2025-11-26
Dependency: `fmd-api==2.0.7`
