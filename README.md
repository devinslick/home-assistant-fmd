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

- **Wipe Device** - ⚠️ **DANGEROUS**: Factory reset the device (erases ALL data)
  - Entity ID example: `button.fmd_test_user_wipe_device`
  - **Requires "Device Wipe Safety" switch to be enabled first**
  - Sends the "delete" command which performs a factory reset
  - ⚠️ **THIS CANNOT BE UNDONE** - All data on device will be permanently erased
  - Safety switch automatically disables after use to prevent accidental repeated presses
  - Icon: `mdi:delete-forever` to indicate destructive action
  - ✅ **Fully implemented** - Device wipe with safety mechanism

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

- **Device Wipe Safety** - Safety switch for device wipe command
  - Entity ID example: `switch.fmd_test_user_device_wipe_safety`
  - Must be enabled before the "Wipe Device" button will function
  - ⚠️ **Automatically disables after 60 seconds** for safety
  - ⚠️ **DANGEROUS**: Only enable if you intend to wipe the device
  - Icon: `mdi:alert-octagon` to indicate danger
  - ✅ **Fully implemented** - Prevents accidental device wipes

### Select Entities (Configuration)
- **Location Source** - Choose which location provider the Location Update button uses
  - Entity ID example: `select.fmd_test_user_location_source`
  - Options: "All Providers (Default)", "GPS Only (Accurate)", "Cell Only (Fast)", "Last Known (No Request)"
  - **All Providers**: Uses GPS, network, and fused location (most reliable)
  - **GPS Only**: Best accuracy but slower, requires clear sky view
  - **Cell Only**: Fast but less accurate, uses cellular towers
  - **Last Known**: Returns cached location without new GPS request (instant, no battery use)
  - Selection persists and is used by the Location Update button
  - ✅ **Fully implemented** - Configures location request behavior

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

**Button Entities (7):**
5. `button.fmd_test_user_location_update` - Location update trigger
6. `button.fmd_test_user_ring` - Ring device trigger
7. `button.fmd_test_user_lock` - Lock device trigger
8. `button.fmd_test_user_capture_front` - Capture front camera photo
9. `button.fmd_test_user_capture_rear` - Capture rear camera photo
10. `button.fmd_test_user_download_photos` - Download photos from server
11. `button.fmd_test_user_wipe_device` - ⚠️ Device wipe (factory reset)

**Switch Entities (3):**
12. `switch.fmd_test_user_high_frequency_mode` - High-frequency mode toggle
13. `switch.fmd_test_user_allow_inaccurate` - Location accuracy filter toggle
14. `switch.fmd_test_user_device_wipe_safety` - Safety switch for device wipe

**Select Entities (4):**
15. `select.fmd_test_user_location_source` - Location provider selection
16. `select.fmd_test_user_bluetooth_command` - Bluetooth enable/disable commands
17. `select.fmd_test_user_do_not_disturb_command` - DND enable/disable commands
18. `select.fmd_test_user_ringer_mode_command` - Ringer mode commands

**Sensor Entities (1):**
19. `sensor.fmd_test_user_photo_count` - Photo count sensor

**Total: 19 entities per device**

_Note: Hyphens in your FMD account ID will be converted to underscores in entity IDs._

## Features

### ✅ Implemented
- **Dynamic polling interval updates** - Changes take effect immediately without restart
- **High-frequency active-tracking mode** - Requests fresh device location at faster intervals (battery intensive)
- **Location update button** - Triggers immediate on-demand location update from device
- **Configurable location source** - Choose between All Providers, GPS Only, Cell Only, or Last Known location
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
- **EXIF timestamp extraction** - Photos named with capture date/time for chronological sorting
- **Bluetooth control** - Send enable/disable Bluetooth commands to device
- **Do Not Disturb control** - Send enable/disable DND commands to device
- **Ringer mode control** - Set device ringer to Normal, Vibrate, or Silent mode
- **Device wipe** - Factory reset device with safety switch protection (60-second timeout)

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

## Device Control

The integration provides remote control commands for your FMD device:

### Location Source Selection
Configure which location provider the Location Update button uses:
- **All Providers (Default)**: Uses GPS, network, and fused location for best reliability
- **GPS Only (Accurate)**: Most accurate but slower, requires clear sky view, uses more battery
- **Cell Only (Fast)**: Fast but less accurate, uses cellular tower triangulation
- **Last Known (No Request)**: Returns cached location without new GPS request (instant, no battery use)

Use the Location Source select entity to change the provider. The setting persists and will be used by the Location Update button.

**Example automation for battery-conscious tracking:**
```yaml
automation:
  - alias: "FMD: Use GPS when charging, Cell when on battery"
    trigger:
      - platform: state
        entity_id: binary_sensor.my_phone_is_charging
    action:
      - service: select.select_option
        target:
          entity_id: select.fmd_test_user_location_source
        data:
          option: >
            {% if trigger.to_state.state == 'on' %}
              GPS Only (Accurate)
            {% else %}
              Cell Only (Fast)
            {% endif %}
```

### Bluetooth Control
Use the Bluetooth command select entity to enable or disable Bluetooth:
- Select "Enable Bluetooth" to turn on Bluetooth
- Select "Disable Bluetooth" to turn off Bluetooth
- Requires Android 12+ BLUETOOTH_CONNECT permission
- Entity resets to "Send Command..." after sending

### Do Not Disturb Control
Use the DND command select entity to control Do Not Disturb mode:
- Select "Enable Do Not Disturb" to enable DND
- Select "Disable Do Not Disturb" to disable DND
- Requires Do Not Disturb Access permission
- Useful for bedtime automations or meeting mode

### Ringer Mode Control
Use the Ringer Mode command select entity to change device ringer:
- Select "Normal (Sound + Vibrate)" for full sound
- Select "Vibrate Only" for vibrate-only mode
- Select "Silent" for silent mode (also enables DND)
- Requires Do Not Disturb Access permission

### Device Wipe (Factory Reset)
⚠️ **DANGEROUS COMMAND** - Permanently erases all data on the device!

To protect against accidental wipes, this feature requires a two-step process:

1. **Enable Safety Switch:**
   - Turn on the "Device Wipe Safety" switch
   - This allows the wipe button to function
   - ⏰ **Automatically disables after 60 seconds**

2. **Press Wipe Button:**
   - While safety switch is enabled, press "Wipe Device" button
   - Device will be factory reset (all data erased)
   - Safety switch automatically disables after use

**Use Cases:**
- Device is lost/stolen and you want to protect your data
- Device needs to be decommissioned or sold
- Final resort for security/privacy protection

**Important Notes:**
- This command **CANNOT BE UNDONE**
- All apps, files, photos, accounts will be deleted
- Device will return to factory settings
- You'll need physical access to set up the device again

**Note:** Bluetooth, DND, and Ringer commands are fire-and-forget. Home Assistant doesn't track the actual device state, so the select entities always show "Send Command..." as a placeholder.

## TODO & Planned Features

### To Do
- [ ] **Account deletion** - Add account deletion endpoint to FMD API and integration button
- [ ] **Photo cleanup** - Automatic deletion of old photos after X days
- [ ] **Device stats** - Request network statistics (IP, WiFi SSID, etc.)
- [ ] **GPS status** - Request GPS and battery status information

### Completed (v0.8.0)
- [x] **Device wipe** - Factory reset with safety switch and 60-second timeout

### Completed (v0.7.0)
- [x] **Location variants** - Configurable location source (All/GPS/Cell/Last Known)

### Completed (v0.6.0)
- [x] **Do Not Disturb** - Send DND enable/disable commands
- [x] **Bluetooth** - Send Bluetooth enable/disable commands
- [x] **Ringer mode** - Set device ringer mode (Normal/Vibrate/Silent)

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
