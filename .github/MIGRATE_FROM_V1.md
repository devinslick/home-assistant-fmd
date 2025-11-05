# Migrating from fmd_api v1 to v2

# Migrating from fmd_api v1 (module style) to v2 (FmdClient + Device)

## Overview

This short guide shows common v1 usages (from fmd_api.py) and how to perform the

**fmd_api v2.0** introduces a major architectural change from the monolithic `FmdApi` class to a device-oriented design with `FmdClient` and `Device` classes. This guide helps you migrate your code from v1 (0.1.x) to v2 (2.0.x).equivalent actions using the new FmdClient and Device classes.



### Key ChangesAuthenticate

v1:

1. **Device-Oriented Architecture**: V2 introduces a `Device` class that wraps common device operations```python

2. **Method Renaming**: `toggle_*` methods renamed to `set_*` for clarityapi = await FmdApi.create("https://fmd.example.com", "alice", "secret")
3. **Import Changes**: `FmdApi` → `FmdClient`, new `Device` class available
4. **Method Deprecations**: Some v1 methods like `get_all_locations()` renamed to `get_locations()`
5. **Constants Removed**: `FmdCommands` constants removed (use string commands directly)

---

## Quick Start: Before and After

### Authentication

**V1:**
```python
from fmd_api import FmdApi

api = await FmdApi.create("https://fmd.example.com", "alice", "secret")
```

**V2:**
```python
from fmd_api import FmdClient

client = await FmdClient.create("https://fmd.example.com", "alice", "secret")
```

---

## Complete Migration Table

### Authentication & Setup

| V1 | V2 | Notes |
|----|----|-------|
| `from fmd_api import FmdApi` | `from fmd_api import FmdClient, Device` | Import names changed |
| `api = await FmdApi.create(url, id, pw)` | `client = await FmdClient.create(url, id, pw)` | Class renamed |
| `await api.close()` | `await client.close()` | Same method |

### Location Methods

| V1 | V2 | Notes |
|----|----|-------|
| `await api.get_all_locations(10)` | `await client.get_locations(10)` | Method renamed |
| `api.decrypt_data_blob(blob)` | `client.decrypt_data_blob(blob)` | Same method |
| `await api.request_location('gps')` | `await client.request_location('gps')` | Same method |

### Device Commands

| V1 | V2 (FmdClient) | V2 (Device) | Notes |
|----|----------------|-------------|-------|
| `await api.send_command('ring')` | `await client.send_command('ring')` | `await device.play_sound()` | Device method preferred |
| `await api.send_command('lock')` | `await client.send_command('lock')` | `await device.lock()` | Device method preferred |
| `await api.send_command('delete')` | `await client.send_command('delete')` | `await device.wipe(confirm=True)` | **REQUIRES confirm flag** |

### Camera Commands

| V1 | V2 (FmdClient) | V2 (Device) | Notes |
|----|----------------|-------------|-------|
| `await api.take_picture('back')` | `await client.take_picture('back')` | `await device.take_rear_photo()` | Device method preferred |
| `await api.take_picture('front')` | `await client.take_picture('front')` | `await device.take_front_photo()` | Device method preferred |

### Bluetooth & Audio Settings

| V1 | V2 | Notes |
|----|----|-------|
| `await api.toggle_bluetooth(True)` | `await client.set_bluetooth(True)` | Method renamed |
| `await api.toggle_bluetooth(False)` | `await client.set_bluetooth(False)` | Method renamed |
| `await api.toggle_do_not_disturb(True)` | `await client.set_do_not_disturb(True)` | Method renamed |
| `await api.toggle_do_not_disturb(False)` | `await client.set_do_not_disturb(False)` | Method renamed |
| `await api.set_ringer_mode('normal')` | `await client.set_ringer_mode('normal')` | Same method |

### Pictures

| V1 | V2 (FmdClient) | V2 (Device) | Notes |
|----|----------------|-------------|-------|
| `await api.get_pictures(10)` | `await client.get_pictures(10)` | `await device.fetch_pictures(10)` | Both available |
| N/A | N/A | `await device.download_photo(blob)` | New helper method |

### Device Stats

| V1 | V2 | Notes |
|----|----|-------|
| `await api.get_device_stats()` | `await client.get_device_stats()` | Same method |

### Export Data

| V1 | V2 | Notes |
|----|----|-------|
| `await api.export_data_zip('output.zip')` | `await client.export_data_zip('output.zip')` | Same method |

### Constants (Removed)

| V1 | V2 | Notes |
|----|----|-------|
| `FmdCommands.RING` | `'ring'` | Use string directly |
| `FmdCommands.LOCATE_GPS` | `'locate gps'` | Use string directly |
| `FmdCommands.BLUETOOTH_ON` | `'bluetooth on'` | Use string directly |
| `FmdCommands.NODISTURB_ON` | `'nodisturb on'` | Use string directly |
| `FmdCommands.RINGERMODE_VIBRATE` | `'ringermode vibrate'` | Use string directly |

---

## New Device-Oriented API

V2 introduces the `Device` class for cleaner device-specific operations:

### Creating a Device Instance

```python
from fmd_api import FmdClient, Device

# Authenticate with client
client = await FmdClient.create("https://fmd.example.com", "alice", "secret")

# Create device instance
device = Device(client, "alice")

# Now use device methods
await device.refresh()
location = await device.get_location()
print(f"Lat: {location.lat}, Lon: {location.lon}")
```

### Device Methods

```python
# Get current location (with caching)
location = await device.get_location()
location = await device.get_location(force=True)  # Force refresh

# Get location history as async iterator
async for location in device.get_history(limit=10):
    print(f"Location at {location.date}: {location.lat}, {location.lon}")

# Device commands
await device.play_sound()                    # Ring device
await device.take_rear_photo()               # Rear camera
await device.take_front_photo()              # Front camera
await device.lock(message="Lost device")     # Lock with message
await device.wipe(confirm=True)              # Factory reset (DESTRUCTIVE)

# Pictures
pictures = await device.fetch_pictures(10)
photo_result = await device.download_photo(pictures[0])
```

---

## Complete Migration Examples

### Example 1: Get Latest Location

**V1:**
```python
import asyncio
import json
from fmd_api import FmdApi

async def main():
    api = await FmdApi.create("https://fmd.example.com", "alice", "secret")

    # Request new location
    await api.request_location('gps')
    await asyncio.sleep(30)

    # Get locations
    blobs = await api.get_all_locations(1)
    location_json = api.decrypt_data_blob(blobs[0])
    location = json.loads(location_json)

    print(f"Lat: {location['lat']}, Lon: {location['lon']}")
    await api.close()

asyncio.run(main())
```

**V2 (Client-based):**
```python
import asyncio
import json
from fmd_api import FmdClient

async def main():
    client = await FmdClient.create("https://fmd.example.com", "alice", "secret")

    # Request new location
    await client.request_location('gps')
    await asyncio.sleep(30)

    # Get locations
    blobs = await client.get_locations(1)
    location_json = client.decrypt_data_blob(blobs[0])
    location = json.loads(location_json)

    print(f"Lat: {location['lat']}, Lon: {location['lon']}")
    await client.close()

asyncio.run(main())
```

**V2 (Device-oriented, RECOMMENDED):**
```python
import asyncio
from fmd_api import FmdClient, Device

async def main():
    client = await FmdClient.create("https://fmd.example.com", "alice", "secret")
    device = Device(client, "alice")

    # Request and get location (simplified)
    await client.request_location('gps')
    await asyncio.sleep(30)

    location = await device.get_location(force=True)
    print(f"Lat: {location.lat}, Lon: {location.lon}")

    await client.close()

asyncio.run(main())
```

### Example 2: Send Commands

**V1:**
```python
from fmd_api import FmdApi, FmdCommands

async def control_device():
    api = await FmdApi.create("https://fmd.example.com", "alice", "secret")

    # Using constants
    await api.send_command(FmdCommands.RING)
    await api.send_command(FmdCommands.BLUETOOTH_ON)

    # Using convenience methods
    await api.toggle_bluetooth(True)
    await api.toggle_do_not_disturb(True)
    await api.set_ringer_mode('vibrate')

    await api.close()
```

**V2 (Client-based):**
```python
from fmd_api import FmdClient

async def control_device():
    client = await FmdClient.create("https://fmd.example.com", "alice", "secret")

    # Use strings directly (constants removed)
    await client.send_command('ring')
    await client.send_command('bluetooth on')

    # Using convenience methods (renamed from toggle_* to set_*)
    await client.set_bluetooth(True)
    await client.set_do_not_disturb(True)
    await client.set_ringer_mode('vibrate')

    await client.close()
```

**V2 (Device-oriented, RECOMMENDED):**
```python
from fmd_api import FmdClient, Device

async def control_device():
    client = await FmdClient.create("https://fmd.example.com", "alice", "secret")
    device = Device(client, "alice")

    # Use device methods for cleaner API
    await device.play_sound()

    # Settings still use client
    await client.set_bluetooth(True)
    await client.set_do_not_disturb(True)
    await client.set_ringer_mode('vibrate')

    await client.close()
```

### Example 3: Get Location History

**V1:**
```python
import json
from fmd_api import FmdApi

async def get_history():
    api = await FmdApi.create("https://fmd.example.com", "alice", "secret")

    blobs = await api.get_all_locations(10)
    for blob in blobs:
        location_json = api.decrypt_data_blob(blob)
        location = json.loads(location_json)
        print(f"Date: {location['date']}, Lat: {location['lat']}, Lon: {location['lon']}")

    await api.close()
```

**V2 (Device-oriented, RECOMMENDED):**
```python
from fmd_api import FmdClient, Device

async def get_history():
    client = await FmdClient.create("https://fmd.example.com", "alice", "secret")
    device = Device(client, "alice")

    # Async iterator with automatic decryption
    async for location in device.get_history(limit=10):
        print(f"Date: {location.date}, Lat: {location.lat}, Lon: {location.lon}")

    await client.close()
```

---

## Breaking Changes Summary

### Required Changes

1. **Import statements**: Replace `FmdApi` with `FmdClient`
2. **Method renames**:
   - `get_all_locations()` → `get_locations()`
   - `toggle_bluetooth()` → `set_bluetooth()`
   - `toggle_do_not_disturb()` → `set_do_not_disturb()`
3. **Constants removed**: Replace `FmdCommands.*` with string literals
4. **Wipe command**: Now requires `confirm=True` when using Device class

### Optional But Recommended

1. **Use Device class** for device-specific operations
2. **Use async iteration** for location history: `async for location in device.get_history()`
3. **Use Location objects** instead of raw JSON dictionaries

---

## Compatibility Notes

- **Python 3.8+** required (same as v1)
- **Dependencies**: Same dependencies (aiohttp, argon2-cffi, cryptography)
- **Server compatibility**: V2 works with the same FMD server as V1
- **Data format**: Location and picture data formats unchanged

---

## Migration Checklist

- [ ] Update imports: `FmdApi` → `FmdClient`
- [ ] Rename `get_all_locations()` → `get_locations()`
- [ ] Rename `toggle_bluetooth()` → `set_bluetooth()`
- [ ] Rename `toggle_do_not_disturb()` → `set_do_not_disturb()`
- [ ] Replace `FmdCommands` constants with strings
- [ ] Consider using `Device` class for cleaner code
- [ ] Update `wipe()` calls to include `confirm=True`
- [ ] Test all functionality with your FMD server

---

## Getting Help

- **Issues**: https://github.com/devinslick/fmd_api/issues
- **Documentation**: https://github.com/devinslick/fmd_api#readme
- **Version**: Check `fmd_api.__version__`

For additional examples, see the `tests/functional/` directory in the repository.
