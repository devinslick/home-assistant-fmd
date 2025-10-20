# FMD Server Python Client Scripts

This directory contains Python scripts for interacting with an FMD (Find My Device) server, including authentication, key retrieval, and location data decryption.
For more information on this open source alternative to Google's Find My Device service, read the Credits section at the bottom of this README.

## Prerequisites
- Python 3.7+
- Install dependencies:
  ```
  pip install requests argon2-cffi cryptography
  ```

## Scripts Overview

### Main Client

#### `fmd_client.py`
**The primary tool for bulk data export.** Downloads locations and/or pictures, saving them to a directory or ZIP archive.

**Usage:**
```bash
python fmd_client.py --url <server_url> --id <fmd_id> --password <password> --output <path> [--locations [N]] [--pictures [N]]
```

**Options:**
- `--locations [N]`: Export all locations, or specify N for the most recent N locations
- `--pictures [N]`: Export all pictures, or specify N for the most recent N pictures
- `--output`: Output directory or `.zip` file path
- `--session`: Session duration in seconds (default: 3600)

**Examples:**
```bash
# Export all locations to CSV
python fmd_client.py --url https://fmd.example.com --id alice --password secret --output data --locations

# Export last 10 locations and 5 pictures to ZIP
python fmd_client.py --url https://fmd.example.com --id alice --password secret --output export.zip --locations 10 --pictures 5
```

### Debugging Scripts

Located in `debugging/`, these scripts help test individual workflows and troubleshoot issues.

#### `fmd_get_location.py`
**End-to-end test:** Authenticates, retrieves, and decrypts the latest location in one step.

**Usage:**
```bash
cd debugging
python fmd_get_location.py --url <server_url> --id <fmd_id> --password <password>
```

#### `fmd_export_data.py`
**Test native export:** Downloads the server's pre-packaged export ZIP (if available).

**Usage:**
```bash
cd debugging
python fmd_export_data.py --url <server_url> --id <fmd_id> --password <password> --output export.zip
```

#### `request_location_example.py`
**Request new location:** Triggers a device to capture and upload a new location update.

**Usage:**
```bash
cd debugging
python request_location_example.py --url <server_url> --id <fmd_id> --password <password> [--provider all|gps|cell|last] [--wait SECONDS]
```

**Options:**
- `--provider`: Location provider to use (default: all)
  - `all`: Use all available providers (GPS, network, fused)
  - `gps`: GPS only (most accurate, slower)
  - `cell`: Cellular network (faster, less accurate)
  - `last`: Don't request new location, just get last known
- `--wait`: Seconds to wait for location update (default: 30)

**Example:**
```bash
# Request GPS location and wait 45 seconds
python request_location_example.py --url https://fmd.example.com --id alice --password secret --provider gps --wait 45

# Quick cellular network location
python request_location_example.py --url https://fmd.example.com --id alice --password secret --provider cell --wait 20
```

#### `diagnose_blob.py`
**Diagnostic tool:** Analyzes encrypted blob structure to troubleshoot decryption issues.

**Usage:**
```bash
cd debugging
python diagnose_blob.py --url <server_url> --id <fmd_id> --password <password>
```

Shows:
- Private key size and type
- Actual blob size vs. expected structure
- Analysis of RSA session key packet layout
- First/last bytes in hex for inspection

## Core Library

### `fmd_api.py`
The foundational API library providing the `FmdApi` class. Handles:
- Authentication (salt retrieval, Argon2id password hashing, token management)
- Encrypted private key retrieval and decryption
- Data blob decryption (RSA-OAEP + AES-GCM)
- Location and picture retrieval
- Command sending (request location updates, ring, lock, camera)
  - Commands are cryptographically signed using RSA-PSS to prove authenticity

**For application developers:** See [LOCATION_FIELDS.md](LOCATION_FIELDS.md) for detailed documentation on extracting and using accuracy, altitude, speed, and heading fields.

**Quick example:**
```python
import asyncio
import json
from fmd_api import FmdApi

async def main():
    # Authenticate (automatically retrieves and decrypts private key)
    api = await FmdApi.create("https://fmd.example.com", "alice", "secret")

    # Request a new location update
    await api.request_location('gps')  # or 'all', 'cell', 'last'
    await asyncio.sleep(30)  # Wait for device to respond

    # Get locations
    locations = await api.get_all_locations(num_to_get=10)  # Last 10, or -1 for all

    # Decrypt a location blob
    decrypted_data = api.decrypt_data_blob(locations[0])
    location = json.loads(decrypted_data)
    
    # Access fields (use .get() for optional fields)
    lat = location['lat']
    lon = location['lon']
    speed = location.get('speed')      # Optional, only when moving
    heading = location.get('heading')  # Optional, only when moving
    
    # Send commands (see Available Commands section below)
    await api.send_command('ring')           # Make device ring
    await api.send_command('bluetooth on')   # Enable Bluetooth
    await api.send_command('camera front')   # Take picture with front camera

asyncio.run(main())
```

### Available Commands

The FMD Android app supports a comprehensive set of commands. You can send them using `api.send_command(command)` or use the convenience methods and constants:

#### Location Requests
```python
# Using convenience method
await api.request_location('gps')    # GPS only
await api.request_location('all')    # All providers (default)
await api.request_location('cell')   # Cellular network only

# Using send_command directly
await api.send_command('locate gps')
await api.send_command('locate')
await api.send_command('locate cell')
await api.send_command('locate last')  # Last known, no new request

# Using constants
from fmd_api import FmdCommands
await api.send_command(FmdCommands.LOCATE_GPS)
```

#### Device Control
```python
# Ring device
await api.send_command('ring')
await api.send_command(FmdCommands.RING)

# Lock device screen
await api.send_command('lock')
await api.send_command(FmdCommands.LOCK)

# ⚠️ Delete/wipe device (DESTRUCTIVE - factory reset!)
await api.send_command('delete')
await api.send_command(FmdCommands.DELETE)
```

#### Camera
```python
# Using convenience method
await api.take_picture('back')   # Rear camera (default)
await api.take_picture('front')  # Front camera (selfie)

# Using send_command
await api.send_command('camera back')
await api.send_command('camera front')

# Using constants
await api.send_command(FmdCommands.CAMERA_BACK)
await api.send_command(FmdCommands.CAMERA_FRONT)
```

#### Bluetooth
```python
# Using convenience method
await api.toggle_bluetooth(True)   # Enable
await api.toggle_bluetooth(False)  # Disable

# Using send_command
await api.send_command('bluetooth on')
await api.send_command('bluetooth off')

# Using constants
await api.send_command(FmdCommands.BLUETOOTH_ON)
await api.send_command(FmdCommands.BLUETOOTH_OFF)
```

**Note:** Android 12+ requires BLUETOOTH_CONNECT permission.

#### Do Not Disturb Mode
```python
# Using convenience method
await api.toggle_do_not_disturb(True)   # Enable DND
await api.toggle_do_not_disturb(False)  # Disable DND

# Using send_command
await api.send_command('nodisturb on')
await api.send_command('nodisturb off')

# Using constants
await api.send_command(FmdCommands.NODISTURB_ON)
await api.send_command(FmdCommands.NODISTURB_OFF)
```

**Note:** Requires Do Not Disturb Access permission.

#### Ringer Mode
```python
# Using convenience method
await api.set_ringer_mode('normal')   # Sound + vibrate
await api.set_ringer_mode('vibrate')  # Vibrate only
await api.set_ringer_mode('silent')   # Silent (also enables DND)

# Using send_command
await api.send_command('ringermode normal')
await api.send_command('ringermode vibrate')
await api.send_command('ringermode silent')

# Using constants
await api.send_command(FmdCommands.RINGERMODE_NORMAL)
await api.send_command(FmdCommands.RINGERMODE_VIBRATE)
await api.send_command(FmdCommands.RINGERMODE_SILENT)
```

**Note:** Setting to "silent" also enables Do Not Disturb (Android behavior). Requires Do Not Disturb Access permission.

#### Device Information
```python
# Get network statistics (IP addresses, WiFi SSID/BSSID)
await api.get_device_stats()
await api.send_command('stats')
await api.send_command(FmdCommands.STATS)

# Get battery and GPS status
await api.send_command('gps')
await api.send_command(FmdCommands.GPS)
```

**Note:** `stats` command requires Location permission to access WiFi information.

#### Command Testing Script
Test any command easily:
```bash
cd debugging
python test_command.py <command> --url <server_url> --id <fmd_id> --password <password>

# Examples
python test_command.py "ring" --url https://fmd.example.com --id alice --password secret
python test_command.py "bluetooth on" --url https://fmd.example.com --id alice --password secret
python test_command.py "ringermode vibrate" --url https://fmd.example.com --id alice --password secret
```

## Troubleshooting

### Empty or Invalid Blobs
If you see warnings like `"Blob too small for decryption"`, the server returned empty/corrupted data. This can happen when:
- No location data was uploaded for that time period
- Data was deleted or corrupted server-side
- The server returns placeholder values for missing data

The client will skip these automatically and report the count at the end.

### Debugging Decryption Issues
Use `debugging/diagnose_blob.py` to analyze blob structure:
```bash
cd debugging
python diagnose_blob.py --url <server_url> --id <fmd_id> --password <password>
```

This shows the actual blob size, expected structure, and helps identify if the RSA key size or encryption format has changed.

## Notes
- All scripts use Argon2id password hashing and AES-GCM/RSA-OAEP encryption, matching the FMD web client
- Blobs must be at least 396 bytes (384 RSA session key + 12 IV + ciphertext) to be valid
- Base64 data from the server may be missing padding - use `_pad_base64()` helper when needed
- **Location data fields**:
  - Always present: `time`, `provider`, `bat` (battery %), `lat`, `lon`, `date` (Unix ms)
  - Optional (depending on provider): `accuracy` (meters), `altitude` (meters), `speed` (m/s), `heading` (degrees)
- Picture data is double-encoded: encrypted blob → base64 string → actual image bytes

## Credits

This project is a client for the open-source FMD (Find My Device) server. The FMD project provides a decentralized, self-hostable alternative to commercial device tracking services.

- **[fmd-foss.org](https://fmd-foss.org/)**: The official project website, offering general information, documentation, and news.
- **[fmd-foss on GitLab](https://gitlab.com/fmd-foss)**: The official GitLab group hosting the source code for the server, Android client, web UI, and other related projects.
- **[fmd.nulide.de](https://fmd.nulide.de/)**: A generously hosted public instance of the FMD server available for community use.