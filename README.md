# Home Assistant FMD Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

This is a Home Assistant integration for FMD (Find My Device). It allows you to track the location of your devices running the FMD Android app.

## Installation

### Manual Installation

1.  Copy the `custom_components/fmd` directory to your Home Assistant `custom_components` directory.
2.  Restart Home Assistant.

## Configuration

1.  Go to **Settings** -> **Devices & Services**.
2.  Click **Add Integration**.
3.  Search for "FMD" and select it.
4.  Enter your FMD server URL, ID, and password.
5.  Configure the polling interval (in minutes) and location accuracy filtering.
    - **Allow inaccurate locations** (default: disabled) - When unchecked, filters out low-accuracy location updates from providers like BeaconDB. Only Fused, GPS, and network locations will be accepted.
6.  Click **Submit**.

## Entities Created

The integration will create the following entities for each configured FMD device:

### Device Tracker
- **Device Tracker** - Displays the current location of your device on the map
  - Entity ID example: `device_tracker.fmd_test_user`
  - Updates automatically based on the configured polling interval
  - Shows latitude, longitude, and other location metadata
  - **Attributes:**
    - `battery_level` - Device battery percentage (0-100)
    - `provider` - Location provider used by the device (e.g., `gps`, `network`, `BeaconDB`)
    - `last_poll_time` - ISO timestamp when Home Assistant last polled the FMD server
    - `device_timestamp` - Human-readable timestamp when the device sent the location to FMD server
    - `device_timestamp_ms` - Unix timestamp (milliseconds) when the device sent the location to FMD server
    - `gps_accuracy` - GPS accuracy in meters (optional - only when available)
    - `altitude` - Altitude in meters (optional - only when available)
    - `speed` - Speed in meters per second (optional - only present when device is moving)
    - `heading` - Direction/bearing in degrees 0-360° (optional - only present when device is moving)

### Number Entities (Configuration)
- **Update Interval** - Set the standard polling interval (1-1440 minutes, default: 30)
  - Entity ID example: `number.fmd_test_user_update_interval`
  - Controls how frequently the integration checks for location updates in normal mode
  - ✅ **Changes take effect immediately** - No reload required!

- **High Frequency Interval** - Set the high-frequency polling interval (1-60 minutes, default: 5)
  - Entity ID example: `number.fmd_test_user_high_frequency_interval`
  - Controls the polling rate when High Frequency Mode is enabled
  - _Note: Not yet connected to polling logic (functionality pending)_

### Button Entities (Configuration)
- **Location Update** - Request a new location from the device
  - Entity ID example: `button.fmd_test_user_location_update`
  - Sends a command to the FMD device to capture a new location using all available providers (GPS, network)
  - Waits 10 seconds for the device to respond, then fetches the updated location from the server
  - ✅ **Fully implemented** - Triggers immediate location update on-demand

- **Ring** - Make the device ring at maximum volume
  - Entity ID example: `button.fmd_test_user_ring`
  - Sends a ring command to the device, making it play a loud sound
  - Useful for finding a lost device nearby
  - ✅ **Fully implemented** - Triggers ring command immediately

- **Lock** - Lock the device screen
  - Entity ID example: `button.fmd_test_user_lock`
  - Sends a lock command to secure the device
  - Useful if device is lost or stolen
  - ✅ **Fully implemented** - Triggers lock command immediately

### Switch Entities (Configuration)
- **High Frequency Mode** - Enable rapid location polling
  - Entity ID example: `switch.fmd_test_user_high_frequency_mode`
  - When enabled, switches to the high-frequency polling interval
  - Useful for tracking during active travel or emergencies
  - _Note: Currently toggles state but doesn't change polling rate (functionality pending)_

- **Allow Inaccurate Locations** - Toggle location filtering
  - Entity ID example: `switch.fmd_test_user_allow_inaccurate`
  - When **off** (default): Blocks location updates from low-accuracy providers (e.g., BeaconDB). Only accepts updates from accurate providers (Fused, GPS, and network).
  - When **on**: Accepts all location updates regardless of provider accuracy.
  - ✅ **Fully implemented** - Filtering is active and can be toggled at runtime.
  - _Note: You can also configure this during initial setup via the config flow._

**All entities are grouped together under a single FMD device** in Home Assistant (e.g., "FMD test-user").

### Example Entity IDs
For a user with FMD account ID `test-user`, the following entities will be created:

1. `device_tracker.fmd_test_user` - Device location tracker (with battery_level attribute)
2. `number.fmd_test_user_update_interval` - Standard polling interval setting
3. `number.fmd_test_user_high_frequency_interval` - High-frequency polling interval setting
4. `button.fmd_test_user_location_update` - Location update trigger
5. `button.fmd_test_user_ring` - Ring device trigger
6. `button.fmd_test_user_lock` - Lock device trigger
7. `switch.fmd_test_user_high_frequency_mode` - High-frequency mode toggle
8. `switch.fmd_test_user_allow_inaccurate` - Location accuracy filter toggle

_Note: Hyphens in your FMD account ID will be converted to underscores in entity IDs._

## Features
- [x] **Dynamic polling interval updates** - Changing the update interval number immediately updates the polling schedule
- [x] **Location accuracy filtering** - Implement logic to filter inaccurate location updates based on the "Allow Inaccurate" switch setting
- [x] **Location metadata sensors** - Add attributes to track gps_accuracy, altitude, speed, and heading

## Current Limitations & TODO

### Location tracking improvements
- [ ] **Manual update button functionality** - Button should trigger immediate location fetch from device
- [ ] **High-frequency mode switching** - Enable/disable switch should toggle between standard FMD server polling and high-frequency polling intervals
- [ ] **Historical location history** - Option to fetch and store location history from FMD in the home assistant device tracker entity
- [ ] **Timestamp configuration** - Option to use FMD timestamp for location updates instead of the polling time


### Photos
- [ ] **Browsing** -  View historical photos taken that are already stored on the FMD server
- [ ] **Capture** - Capture front/read camera photos

### Other
- [ ] **Alarm** - A button to trigger the alarm/ring the device
- [ ] **Lock** - A button to lock the device
- [ ] **Wipe** - A button to wipe all data from the device
- [ ] **Account Deletion*** - A button to delete your FMD account


## Troubleshooting

### Location not updating
- Check that your FMD server is accessible from Home Assistant
- Verify your credentials are correct in the integration configuration
- Check Home Assistant logs for errors (`custom_components.fmd`)
- Ensure your device is sending location updates to the FMD server

### Integration won't load
- Verify all required dependencies are installed (aiohttp, argon2-cffi, cryptography)
- Check for errors in Home Assistant logs during startup
- Try removing and re-adding the integration

## Contributions

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.

### Development
This integration uses:
- Async/await for all I/O operations
- aiohttp for HTTP communication
- RSA-3072 encryption for key exchange
- AES-GCM for data encryption
- Argon2id for password hashing

## License

This project is open source. See the repository for license details.
