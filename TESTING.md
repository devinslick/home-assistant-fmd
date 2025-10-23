# Testing Guide

## Running Tests

### Linux / macOS / WSL
```bash
pytest --cov=custom_components.fmd --cov-report=html --cov-report=term-missing
```

### Windows
**Known Issue**: pytest-homeassistant-custom-component includes pytest-socket which is incompatible with Windows asyncio event loops. Tests cannot be run directly on Windows.

**Workarounds**:
1. Use Windows Subsystem for Linux (WSL)
2. Use Docker with Linux container
3. Run tests in GitHub Actions (automatic on push)
4. Use a Linux VM

The integration code itself works fine on Windows - this is only a testing limitation.

## Test Coverage
Tests are located in the `tests/` directory and cover:
- Component initialization and setup (`test_init.py`)
- Configuration flow (`test_config_flow.py`)  
- Device tracker platform (`test_device_tracker.py`)
- Button platform (`test_button.py`)
- Switch platform (`test_switch.py`)
- Select platform (`test_select.py`)
- Number platform (`test_number.py`)
- Sensor platform (`test_sensor.py`)

## GitHub Actions
Tests run automatically on every push via `.github/workflows/tests.yml`. The workflow tests against Python 3.11 and 3.12 on Ubuntu Linux.

## Coverage Goals
- Target: 90%+ code coverage for Home Assistant Core submission
- View coverage report: `htmlcov/index.html` after running tests
