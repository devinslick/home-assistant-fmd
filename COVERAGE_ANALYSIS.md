# Test Coverage Analysis & Improvement Plan

**Current Coverage**: 84% (1066 statements, 171 missing)
**Target Coverage**: 90%
**Gap**: 6% (~60 statements)
**Status**: ⚠️ Close but needs final push

---

## Quick Summary

| File | Coverage | Missing | Priority | Effort |
|------|----------|---------|----------|--------|
| button.py | 77% | 79 lines | ⭐⭐⭐ | High |
| device_tracker.py | 82% | 39 lines | ⭐⭐⭐ | High |
| switch.py | 86% | 22 lines | ⭐⭐ | Medium |
| select.py | 84% | 23 lines | ⭐⭐ | Medium |
| config_flow.py | 89% | 3 lines | ⭐ | Low |
| number.py | 98% | 2 lines | ⭐ | Low |
| sensor.py | 95% | 3 lines | ⭐ | Low |
| **const.py** | **100%** | **0** | — | — |
| **__init__.py** | **100%** | **0** | — | — |

---

## Coverage Improvement Strategy

### Phase 1: Quick Wins (30 min) → +2-3%
**Focus**: Low-hanging fruit that's easy to test

1. **config_flow.py** (89% → 100%)
   - Add test for `authenticate_and_get_locations()` error case
   - Test timeout/API error scenarios

2. **number.py** (98% → 100%)
   - Add test for when tracker not found in `hass.data`
   - 2 lines: turn_on/turn_off error handling

3. **sensor.py** (95% → 100%)
   - Add test for media folder not found
   - Add test for permission errors reading directory

### Phase 2: Medium Effort (1-2 hours) → +3-4%
**Focus**: Error paths and edge cases

1. **select.py** (84% → 90%)
   - Command execution errors
   - Bluetooth/DND/Ringer mode command failures
   - Reset delay handling

2. **switch.py** (86% → 92%)
   - Turn on/off with tracker not found
   - High-frequency mode with errors
   - Auto-disable timeout completion

### Phase 3: Major Effort (2-4 hours) → +2-3% (to 90%+)
**Focus**: Comprehensive error path coverage

1. **button.py** (77% → 88%)
   - Location update errors
   - Photo download errors (decrypt, media creation, file I/O)
   - Wipe device errors and safety checks
   - Command execution errors for all buttons

2. **device_tracker.py** (82% → 90%)
   - State attributes (altitude, speed, heading)
   - Extra attributes assembly
   - Location fetch errors
   - Polling/high-frequency mode edge cases

---

## Missing Lines by Category

### Error Paths (High Impact - Cover These!)
- Button command failures (API errors, tracker not found)
- Photo processing errors (decrypt, EXIF, file I/O)
- Switch state transition errors
- Select command execution errors
- Device tracker update failures

### State/Attribute Tests (Medium Impact)
- Device tracker extra attributes assembly
- Sensor icon property
- Switch auto-timeout completion
- Number entity value setting

### Defensive Programming (Low Impact - May Skip)
- Type checks that shouldn't fail
- Docstrings (already covered by import)
- Constants validation

---

## Recommended Test Additions

### Minimum to Reach 90% (~30 tests)

**button.py** (8-10 tests):
```python
test_location_update_button_tracker_not_found()
test_location_update_button_api_error()
test_ring_button_api_error()
test_lock_button_api_error()
test_download_photos_media_error()
test_download_photos_exif_error()
test_download_photos_no_photos()
test_wipe_device_api_error()
```

**device_tracker.py** (4-5 tests):
```python
test_device_tracker_extra_attributes()
test_device_tracker_altitude_speed_heading()
test_device_tracker_initial_location_error()
test_device_tracker_polling_update()
```

**switch.py** (4-5 tests):
```python
test_high_frequency_switch_turn_on_error()
test_allow_inaccurate_switch_turn_on_error()
test_wipe_safety_auto_disable()
test_photo_cleanup_switch_basic()
```

**select.py** (3-4 tests):
```python
test_bluetooth_command_error()
test_dnd_command_error()
test_ringer_mode_command_error()
```

**config_flow.py** (1-2 tests):
```python
test_authenticate_api_error()
```

**number.py** (1 test):
```python
test_number_entity_tracker_error()
```

**sensor.py** (1 test):
```python
test_photo_sensor_media_error()
```

---

## Implementation Checklist

- [ ] **Phase 1** (30 min)
  - [ ] Add config_flow error tests
  - [ ] Add number error tests
  - [ ] Add sensor error tests
  - [ ] Run: `pytest --cov` → Target: 86-87%

- [ ] **Phase 2** (1-2 hours)
  - [ ] Add select error tests
  - [ ] Add switch error tests
  - [ ] Run: `pytest --cov` → Target: 88-89%

- [ ] **Phase 3** (2-4 hours)
  - [ ] Add button comprehensive tests
  - [ ] Add device_tracker attribute tests
  - [ ] Run: `pytest --cov` → Target: 90%+

- [ ] **Final Verification**
  - [ ] All tests passing
  - [ ] Coverage ≥90%
  - [ ] Pre-commit hooks passing
  - [ ] Ready for submission

---

## Commands to Use

```bash
# Run coverage for specific file
pytest tests/test_button.py --cov=custom_components.fmd.button --cov-report=term-missing

# Run coverage for all with report
pytest --cov=custom_components.fmd --cov-report=term-missing --cov-report=html

# Check specific coverage percentage
pytest --cov=custom_components.fmd --cov-report=term --cov-fail-under=90

# View HTML report
open htmlcov/index.html
```

---

## Estimated Final Result

After implementing all recommended tests:
- **button.py**: 77% → 90% ✅
- **device_tracker.py**: 82% → 92% ✅
- **switch.py**: 86% → 93% ✅
- **select.py**: 84% → 91% ✅
- **config_flow.py**: 89% → 98% ✅
- **number.py**: 98% → 100% ✅
- **sensor.py**: 95% → 100% ✅

**Total Coverage**: 84% → **91-93%** ✅ **MEETS 90% REQUIREMENT**

---

**Priority**: 🔴 HIGH - Must complete before Home Assistant Core submission
**Time Estimate**: 3-6 hours
**Difficulty**: Medium (mostly straightforward error cases)
**Return on Investment**: Massive (unlocks HA Core submission)
