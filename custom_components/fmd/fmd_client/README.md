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

**Usage in your own scripts:**
```python
from fmd_api import FmdApi

# Authenticate (automatically retrieves and decrypts private key)
api = FmdApi("https://fmd.example.com", "alice", "secret")

# Get locations
locations = api.get_all_locations(num_to_get=10)  # Last 10, or -1 for all

# Decrypt a location blob
decrypted_data = api.decrypt_data_blob(locations[0])
location_json = json.loads(decrypted_data)
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
- Location data includes: `time`, `provider`, `bat` (battery %), `lon`, `lat`
- Picture data is double-encoded: encrypted blob → base64 string → actual image bytes

## Credits

This project is a client for the open-source FMD (Find My Device) server. The FMD project provides a decentralized, self-hostable alternative to commercial device tracking services.

- **[fmd-foss.org](https://fmd-foss.org/)**: The official project website, offering general information, documentation, and news.
- **[fmd-foss on GitLab](https://gitlab.com/fmd-foss)**: The official GitLab group hosting the source code for the server, Android client, web UI, and other related projects.
- **[fmd.nulide.de](https://fmd.nulide.de/)**: A generously hosted public instance of the FMD server available for community use.