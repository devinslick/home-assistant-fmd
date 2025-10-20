# Home Assistant FMD Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

This is a Home Assistant integration for FMD (Find My Device). It allows you to track the location of your devices running the FMD Android app.

## Installation

### HACS Installation (Recommended)

1.  Open HACS in Home Assistant
2.  Click on "Integrations"
3.  Click the "+" button
4.  Search for "FMD" or "Find My Device"
5.  Click "Download"
6.  Restart Home Assistant

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
    - `provider` - Location provider used by the device (e.g., `fused`, `gps`, `network`, `BeaconDB`)
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
  - ✅ **Changes take effect immediately** - If high-frequency mode is active, the new interval is applied right away

- **Max Photos to Download** - Set how many recent photos to download (1-50, default: 10)
  - Entity ID example: `number.fmd_test_user_max_photos`
  - Controls how many of the most recent photos are fetched when pressing the "Download Photos" button
  - Larger values = more photos but larger download size (~2-3 MB per photo)
  - ✅ **Fully implemented** - Configure before downloading photos

### Button Entities (Configuration)
- **Location Update** - Request a new location from the device
  - Entity ID example: `button.fmd_test_user_location_update`
  - Sends a command to the FMD device to capture a new location using all available providers (Fused, GPS, network, cell)
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

- **Capture Front Camera** - Take a photo with the front-facing camera
  - Entity ID example: `button.fmd_test_user_capture_front`
  - Sends a "camera front" command to the device
  - Device captures photo and uploads to FMD server (~15-30 seconds)
  - Press "Download Photos" button afterwards to retrieve the photo
  - ✅ **Fully implemented** - Triggers front camera photo capture

- **Capture Rear Camera** - Take a photo with the rear-facing camera
  - Entity ID example: `button.fmd_test_user_capture_rear`
  - Sends a "camera back" command to the device
  - Device captures photo and uploads to FMD server (~15-30 seconds)
  - Press "Download Photos" button afterwards to retrieve the photo
  - ✅ **Fully implemented** - Triggers rear camera photo capture

- **Download Photos** - Download photos from server to media folder
  - Entity ID example: `button.fmd_test_user_download_photos`
  - Fetches the N most recent photos from server (N = "Max Photos to Download" setting)
  - Decrypts and saves photos to `/config/media/fmd/` folder
  - Photos automatically appear in Home Assistant's Media Browser
  - Updates the "Photo Count" sensor
  - ✅ **Fully implemented** - Downloads photos to media browser

### Switch Entities (Configuration)
- **High Frequency Mode** - Enable active tracking with device location requests
  - Entity ID example: `switch.fmd_test_user_high_frequency_mode`
  - When enabled:
    - Immediately requests a new location from the device
    - Switches to high-frequency polling interval
    - Each poll requests fresh location data from the device (impacts battery life)
  - When disabled, returns to normal polling interval
  - ⚠️ **Battery impact**: Active tracking drains device battery faster
  - Useful for tracking during active travel, emergencies, or finding lost devices
  - ✅ **Fully implemented** - True active tracking mode

- **Allow Inaccurate Locations** - Toggle location filtering
  - Entity ID example: `switch.fmd_test_user_allow_inaccurate`
  - When **off** (default): Blocks location updates from low-accuracy providers (e.g., BeaconDB). Only accepts updates from accurate providers (Fused, GPS, and network).
  - When **on**: Accepts all location updates regardless of provider accuracy.
  - ✅ **Fully implemented** - Filtering is active and can be toggled at runtime.
  - _Note: You can also configure this during initial setup via the config flow._

### Select Entities (Configuration)
- **Bluetooth Command** - Send Bluetooth enable/disable commands
  - Entity ID example: `select.fmd_test_user_bluetooth_command`
  - Options: "Send Command...", "Enable Bluetooth", "Disable Bluetooth"
  - Sends command to device, then resets to "Send Command..." placeholder
  - ⚠️ **Requires Android 12+ BLUETOOTH_CONNECT permission**
  - ✅ **Fully implemented** - Commands sent immediately, no state tracking

- **Do Not Disturb Command** - Send DND enable/disable commands
  - Entity ID example: `select.fmd_test_user_do_not_disturb_command`
  - Options: "Send Command...", "Enable Do Not Disturb", "Disable Do Not Disturb"
  - Sends command to device, then resets to placeholder
  - ⚠️ **Requires Do Not Disturb Access permission**
  - ✅ **Fully implemented** - Commands sent immediately, no state tracking

- **Ringer Mode Command** - Set device ringer mode
  - Entity ID example: `select.fmd_test_user_ringer_mode_command`
  - Options: "Send Command...", "Normal (Sound + Vibrate)", "Vibrate Only", "Silent"
  - Sends command to device, then resets to placeholder
  - ⚠️ **Requires Do Not Disturb Access permission**
  - ⚠️ **Note**: Silent mode also enables Do Not Disturb (Android behavior)
  - ✅ **Fully implemented** - Commands sent immediately, no state tracking

### Sensor Entities
- **Photo Count** - Number of photos available on the server
  - Entity ID example: `sensor.fmd_test_user_photo_count`
  - Shows how many photos were retrieved in the last download
  - **Attributes:**
    - `last_download_time` - ISO timestamp of the last photo download
    - `photos_in_media_folder` - Count of `.jpg` files in `/config/media/fmd/`
  - ✅ **Fully implemented** - Updates automatically when photos are downloaded

**All entities are grouped together under a single FMD device** in Home Assistant (e.g., "FMD test-user").

### Example Entity IDs
For a user with FMD account ID `test-user`, the following entities will be created:

**Device Tracker:**
1. `device_tracker.fmd_test_user` - Device location tracker

**Number Entities (3):**
2. `number.fmd_test_user_update_interval` - Standard polling interval setting
3. `number.fmd_test_user_high_frequency_interval` - High-frequency polling interval setting
4. `number.fmd_test_user_max_photos` - Max photos to download setting

**Button Entities (6):**
5. `button.fmd_test_user_location_update` - Location update trigger
6. `button.fmd_test_user_ring` - Ring device trigger
7. `button.fmd_test_user_lock` - Lock device trigger
8. `button.fmd_test_user_capture_front` - Capture front camera photo
9. `button.fmd_test_user_capture_rear` - Capture rear camera photo
10. `button.fmd_test_user_download_photos` - Download photos from server

**Switch Entities (2):**
11. `switch.fmd_test_user_high_frequency_mode` - High-frequency mode toggle
12. `switch.fmd_test_user_allow_inaccurate` - Location accuracy filter toggle

**Select Entities (3):**
13. `select.fmd_test_user_bluetooth_command` - Bluetooth enable/disable commands
14. `select.fmd_test_user_do_not_disturb_command` - DND enable/disable commands
15. `select.fmd_test_user_ringer_mode_command` - Ringer mode commands

**Sensor Entities (1):**
16. `sensor.fmd_test_user_photo_count` - Photo count sensor

**Total: 16 entities per device**

_Note: Hyphens in your FMD account ID will be converted to underscores in entity IDs._

## Features

### ✅ Implemented
- **Dynamic polling interval updates** - Changes take effect immediately without restart
- **High-frequency active-tracking mode** - Requests fresh device location at faster intervals (battery intensive)
- **Location update button** - Triggers immediate on-demand location update from device
- **Location accuracy filtering** - Filters inaccurate providers (BeaconDB) while accepting accurate ones (Fused, GPS, network)
- **Location metadata attributes** - Tracks GPS accuracy, altitude, speed, and heading
- **Ring button** - Makes device play loud sound at maximum volume
- **Lock button** - Remotely locks the device screen
- **Multiple location provider support** - Fused (Android's best), GPS, network, and cell tower
- **Smart location selection** - Checks up to 5 recent locations to find most recent accurate one
- **Photo capture** - Remote front and rear camera photo capture
- **Photo download** - Download and decrypt photos from FMD server
- **Media browser integration** - Photos automatically appear in Home Assistant's media browser
- **Configurable photo downloads** - Set how many recent photos to download (1-50)

## Photo Workflow

The integration provides complete photo management functionality:

1. **Capture a Photo:**
   - Press "Capture Front Camera" or "Capture Rear Camera" button
   - Wait 15-30 seconds for device to capture and upload to server

2. **Download Photos:**
   - Set "Max Photos to Download" to desired number (default: 10)
   - Press "Download Photos" button
   - Photos are fetched, decrypted, and saved to `/config/media/fmd/<device-id>/` or `/media/fmd/<device-id>/`

3. **View Photos:**
   - Navigate to **Media** → **FMD** in Home Assistant
   - Click on your device folder (e.g., `test-user`)
   - Browse photos in grid view
   - Click to view full size
   - Use photos in automations or notifications

**Photo Storage:**
- Location: `/media/fmd/<device-id>/` (Docker/Core/K8s) or `/config/media/fmd/<device-id>/` (HAOS)
- Format: `photo_YYYYMMDD_HHMMSS_<hash>.jpg` (timestamp from EXIF data + content hash)
  - Example: `photo_20251019_150034_705a8c9f.jpg`
  - Timestamp extracted from EXIF `DateTimeOriginal` tag (when photo was captured)
  - Falls back to `photo_<hash>.jpg` if EXIF data is missing
- Size: ~2-3 MB per photo
- Organization: Each device has its own subdirectory
- Chronological sorting: Photos appear in capture order thanks to timestamp prefix
- Duplicate prevention: Content hash suffix prevents re-downloading identical photos
- No automatic polling - photos are downloaded only when requested

## TODO & Planned Features

### To Do
- [ ] **Device wipe** - Add wipe command support to FMD API and integration
- [ ] **Account deletion** - Add account deletion endpoint to FMD API and integration button
- [ ] **Photo cleanup** - Automatic deletion of old photos after X days
- [ ] **Change ringer** - Change device volume ring mode
- [ ] **Do Not Disturb** - Switch device Do Not Disturb state
- [ ] **Bluetooth** - Enable/Disable bluetooth
- [ ] **GPS**  - Enable/Disable GPS

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
