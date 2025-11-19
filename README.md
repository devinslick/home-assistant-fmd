# Home Assistant FMD Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![Tests](https://github.com/devinslick/home-assistant-fmd/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/devinslick/home-assistant-fmd/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/devinslick/home-assistant-fmd/branch/main/graph/badge.svg?token=W04KEUVQ8W)](https://codecov.io/gh/devinslick/home-assistant-fmd)

A Home Assistant custom integration for [FMD (Find My Device)](https://fmd-foss.org) that allows you to track and control Android devices running the FMD app through your self-hosted FMD server.

## About FMD

**FMD (Find My Device)** is a free and open source device tracking solution created by [Nulide](http://nulide.de) and maintained by the FMD-FOSS team.

- **FMD Android App**: https://gitlab.com/fmd-foss/fmd-android
- **FMD Server**: https://gitlab.com/fmd-foss/fmd-server
- **Website**: https://fmd-foss.org

This integration acts as a **client** for your FMD server, providing seamless integration with Home Assistant. See [CREDITS.md](CREDITS.md) for full attribution.

## Quick Start Overview

This integration provides **22 entities** to control your Android device:

🗺️ **Location Tracking**
- Real-time device location on Home Assistant map
- Multiple location providers (GPS, network, fused, cell)
- Configurable accuracy filtering
- On-demand location updates

📱 **Remote Commands**
- Ring device at max volume
- Lock device remotely
- Toggle Bluetooth on/off
- Control Do Not Disturb mode
- Change ringer mode (Normal/Vibrate/Silent)
- Factory reset with safety protection

📸 **Photo Capture**
- Remote camera control (front & rear)
- Automatic photo download to media library
- EXIF timestamp extraction
- Media browser integration

⚙️ **Smart Tracking**
- Normal polling mode (configurable interval)
- High-frequency active tracking mode
- Battery-conscious location source selection
- GPS only, Cell only, or Last Known options

## Prerequisites

Before installing this integration, you need:

### Required:
1. ✅ **Home Assistant** (2023.1 or newer recommended)
2. ✅ **FMD Server** (v012.0 recommended)
   - Self-hosted or hosted instance
   - TLS certificate - HTTPS is required, not just HTTP
   - FMD server must be  accessible from Home Assistant
   - **Compatibility**: This integration is designed to maintain compatibility with fmd-server and has been tested with versions 0.11.0 and 0.12.0. It will seek to maintain compatibility with the latest versions of fmd-server but cannot guarantee backwards compatibility.
3. ✅ **Android Device** with FMD app installed
   - Android 8.0 or newer
   - FMD app from [F-Droid](https://f-droid.org/) or [GitLab](https://gitlab.com/fmd-foss/fmd-android)
   - Device configured to connect to your FMD server
4. ✅ **FMD Account Credentials**
   - Device ID (from FMD app settings)
   - Password (set when registering device)

### Optional (for specific features):
- **Bluetooth Control**: Android 12+ with BLUETOOTH_CONNECT permission
- **DND/Ringer Control**: Do Not Disturb Access permission granted to FMD app
- **Device Wipe**: Device Admin permission granted to FMD app
- **Photos**: Camera permissions granted to FMD app

### Not Required:
- ❌ User access to the FMD server - this integration connects directly to the FMD API
- ❌ Public IP address (works on your local network if you are self-hosting FMD)
- ❌ Cloud services (fully self-hosted)

## Installation

### HACS Installation (Recommended)

You can install via the HACS Default store (once approved), or add as a Custom Repository today.

#### HACS (Default Store)
1. Open HACS in Home Assistant
2. Click the + button and search for "FMD"
3. Click "Download" and restart Home Assistant

#### HACS (Custom Repository)
1. Open HACS in Home Assistant
2. Click the three dots in the top right corner and select **Custom repositories**
3. Add this repository URL: `https://github.com/devinslick/home-assistant-fmd`
4. Select **Integration** as the category
5. Click **Add**
6. Click the "+" button in HACS
7. Search for "FMD" or "Find My Device"
8. Click "Download"
9. Restart Home Assistant

### Manual Installation

1.  Copy the `custom_components/fmd` directory to your Home Assistant `custom_components` directory.
2.  Restart Home Assistant.

## Configuration

1.  Go to **Settings** -> **Devices & Services**.
2.  Click **Add Integration**.
3.  Search for "FMD" and select it.
4.  Enter your FMD server URL, ID, and password.
5.  Configure the polling interval (in minutes) and location accuracy filtering.
    - **Allow inaccurate locations** (default: disabled) - When unchecked, filters out low-accuracy location updates from providers like BeaconDB. By default only Fused, GPS, and network locations will be accepted.
    - **Use imperial units** (default: disabled) - When checked, converts metric measurements to imperial (meters → feet, m/s → mph)
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
    - `gps_accuracy` - GPS accuracy in meters (or feet if imperial units enabled)
    - `gps_accuracy_unit` - Unit of measurement for GPS accuracy ("m" or "ft")
    - `altitude` - Altitude in meters (or feet if imperial units enabled)
    - `altitude_unit` - Unit of measurement for altitude ("m" or "ft")
    - `speed` - Speed in meters per second (or mph if imperial units enabled)
    - `speed_unit` - Unit of measurement for speed ("m/s" or "mph")
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

- **Photo: Max to retain** - Set maximum photos to keep in media folder (1-50, default: 10)
  - Entity ID example: `number.fmd_test_user_max_photos`
  - Controls retention limit for automatic cleanup
  - When "Photo: Auto-cleanup" is enabled, oldest photos are deleted after download if total exceeds this limit
  - Also controls how many photos are fetched from server (downloads N most recent)
  - ✅ **Fully implemented** - Works with auto-cleanup feature

### Button Entities (Configuration)
- **Location Update** - Request a new location from the device
  - Entity ID example: `button.fmd_test_user_location_update`
  - Sends a command to the FMD device to capture a new location using all available providers (Fused, GPS, network, cell)
  - Waits 10 seconds for the device to respond, then fetches the updated location from the server
  - ✅ **Fully implemented** - Triggers immediate location update on-demand

- **Volume: Ring device** - Make the device ring at maximum volume
  - Entity ID example: `button.fmd_test_user_ring`
  - Sends a ring command to the device, making it play a loud sound
  - Useful for finding a lost device nearby
  - ✅ **Fully implemented** - Triggers ring command immediately

- **Lock device** - Lock the device screen
  - Entity ID example: `button.fmd_test_user_lock`
  - Sends a lock command to secure the device
  - **Optional message support**: Set "Lock: Message" text entity to display a message on the lock screen
  - Example use: "Lost phone - please call 555-1234" or contact information
  - Client automatically sanitizes message for safety
  - Useful if device is lost or stolen
  - ✅ **Fully implemented** - Triggers lock command with optional message

- **Photo: Capture front** - Take a photo with the front-facing camera
  - Entity ID example: `button.fmd_test_user_capture_front`
  - Sends a "camera front" command to the device
  - Device captures photo and uploads to FMD server (~15-30 seconds)
  - Press "Photo: Download" button afterwards to retrieve the photo
  - ✅ **Fully implemented** - Triggers front camera photo capture

- **Photo: Capture rear** - Take a photo with the rear-facing camera
  - Entity ID example: `button.fmd_test_user_capture_rear`
  - Sends a "camera back" command to the device
  - Device captures photo and uploads to FMD server (~15-30 seconds)
  - Press "Photo: Download" button afterwards to retrieve the photo
  - ✅ **Fully implemented** - Triggers rear camera photo capture

- **Photo: Download** - Download photos from server to media folder
  - Entity ID example: `button.fmd_test_user_download_photos`
  - Fetches the N most recent photos from server (N = "Max Photos to Download" setting)
  - Decrypts and saves photos to `/config/media/fmd/device_name` folder
  - Photos automatically appear in Home Assistant's Media Browser
  - Updates the "Photo Count" sensor
  - ✅ **Fully implemented** - Downloads photos to media browser

- **Wipe: ⚠️ Execute ⚠️** - ⚠️ **DANGEROUS**: Factory reset the device (erases ALL data)
  - Entity ID example: `button.fmd_test_user_wipe_device`
  - **Requirements:**
    1. "Wipe: ⚠️ Safety switch ⚠️" must be enabled first
    2. "Wipe: PIN" must be set with a valid alphanumeric PIN
  - Validates PIN before sending wipe command (alphanumeric ASCII, no spaces)
  - Always passes confirmation flag to prevent accidental execution
  - ⚠️ **THIS CANNOT BE UNDONE** - All data on device will be permanently erased
  - Safety switch automatically disables after use to prevent accidental repeated presses
  - Icon: `mdi:delete-forever` to indicate destructive action
  - ✅ **Fully implemented** - Device wipe with safety mechanism and PIN validation

### Switch Entities (Configuration)
- **High Frequency Mode** - Enable active tracking with device location requests
  - Entity ID example: `switch.fmd_test_user_high_frequency_mode`
  - When enabled:
    - Immediately requests a new location from the device
    - Switches to high-frequency polling interval
    - Each poll requests fresh location data from the device using the selected **Location Source**
  - When disabled, returns to normal polling interval
  - ⚠️ **Battery impact**: Active tracking drains device battery faster
  - Useful for tracking during active travel, emergencies, or finding lost devices
  - ✅ **Fully implemented** - True active tracking mode

- **Location: allow inaccurate updates** - Toggle location filtering
  - Entity ID example: `switch.fmd_test_user_allow_inaccurate`
  - When **off** (default): Blocks location updates from low-accuracy providers (e.g., BeaconDB). Only accepts updates from accurate providers (Fused, GPS, and network).
  - When **on**: Accepts all location updates regardless of provider accuracy.
  - ✅ **Fully implemented** - Filtering is active and can be toggled at runtime.
  - _Note: You can also configure this during initial setup via the config flow._

- **Photo: Auto-cleanup** - Automatic deletion of old photos
  - Entity ID example: `switch.fmd_test_user_photo_auto_cleanup`
  - When **on**: Automatically deletes oldest photos after download if total exceeds "Photo: Max to retain" limit
  - When **off** (default): Photos are never automatically deleted
  - Deletion is based on file modification time (oldest first)
  - ⚠️ **Warning**: Deleted photos cannot be recovered
  - ✅ **Fully implemented** - Helps manage storage automatically

- **Wipe: ⚠️ Safety switch ⚠️** - Safety switch for device wipe command
  - Entity ID example: `switch.fmd_test_user_device_wipe_safety`
  - Must be enabled before the "Wipe: ⚠️ Execute ⚠️" button will function
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

- **Bluetooth** - Send Bluetooth enable/disable commands
  - Entity ID example: `select.fmd_test_user_bluetooth_command`
  - Options: "Send Command...", "Enable Bluetooth", "Disable Bluetooth"
  - Sends command to device, then resets to "Send Command..." placeholder
  - ⚠️ **Requires Android 12+ BLUETOOTH_CONNECT permission**
  - ✅ **Fully implemented** - Commands sent immediately, no state tracking

- **Volume: Do Not Disturb** - Send DND enable/disable commands
  - Entity ID example: `select.fmd_test_user_do_not_disturb_command`
  - Options: "Send Command...", "Enable Do Not Disturb", "Disable Do Not Disturb"
  - Sends command to device, then resets to placeholder
  - ⚠️ **Requires Do Not Disturb Access permission**
  - ✅ **Fully implemented** - Commands sent immediately, no state tracking

- **Volume: Ringer mode** - Set device ringer mode
  - Entity ID example: `select.fmd_test_user_ringer_mode_command`
  - Options: "Send Command...", "Normal (Sound + Vibrate)", "Vibrate Only", "Silent"
  - Sends command to device, then resets to placeholder
  - ⚠️ **Requires Do Not Disturb Access permission**
  - ⚠️ **Note**: Silent mode also enables Do Not Disturb (Android behavior)
  - ✅ **Fully implemented** - Commands sent immediately, no state tracking

### Text Entities (Configuration)
- **Wipe: PIN** - Alphanumeric PIN required for device wipe command
  - Entity ID example: `text.fmd_test_user_wipe_pin`
  - **Required for wipe operation** - Must be set before "Wipe: ⚠️ Execute ⚠️" button will work
  - **Validation requirements:**
    - Must be alphanumeric (letters and numbers only)
    - Cannot contain spaces
    - Must contain only ASCII characters
  - Password-mode text input (masked in UI for security)
  - ⚠️ **Note**: Future FMD server versions may require 16+ character PINs
  - Stored securely in config entry
  - Icon: `mdi:key-variant`
  - ✅ **Fully implemented** - PIN validation with clear error messages

- **Lock: Message** - Optional message to display on locked device screen
  - Entity ID example: `text.fmd_test_user_lock_message`
  - **Optional** - If set, message will be shown when device is locked
  - Plain text input (max 500 characters)
  - Client automatically sanitizes dangerous characters for safety
  - Useful for contact information or instructions (e.g., "Lost phone - call 555-1234")
  - Icon: `mdi:message-text-lock`
  - ✅ **Fully implemented** - Message passed to lock command automatically

### Sensor Entities
- **Photo count** - Total number of photos stored in media folder
  - Entity ID example: `sensor.fmd_test_user_photo_count`
  - Shows total `.jpg` files currently in `/config/media/fmd/`
  - **Attributes:**
    - `last_download_count` - Number of photos downloaded in the last operation
    - `last_download_time` - ISO timestamp of the last photo download
    - `photos_in_media_folder` - Same as main value (kept for backward compatibility)
  - ✅ **Fully implemented** - Updates automatically after photo downloads

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

**Switch Entities (4):**
12. `switch.fmd_test_user_high_frequency_mode` - High-frequency mode toggle
13. `switch.fmd_test_user_allow_inaccurate` - Location accuracy filter toggle
14. `switch.fmd_test_user_photo_auto_cleanup` - Photo: Auto-cleanup toggle
15. `switch.fmd_test_user_device_wipe_safety` - Safety switch for device wipe

**Select Entities (4):**
16. `select.fmd_test_user_location_source` - Location provider selection
17. `select.fmd_test_user_bluetooth_command` - Bluetooth enable/disable commands
18. `select.fmd_test_user_do_not_disturb_command` - DND enable/disable commands
19. `select.fmd_test_user_ringer_mode_command` - Ringer mode commands

**Text Entities (2):**
20. `text.fmd_test_user_wipe_pin` - Wipe PIN (required for device wipe)
21. `text.fmd_test_user_lock_message` - Lock message (optional for lock command)

**Sensor Entities (1):**
22. `sensor.fmd_test_user_photo_count` - Total stored photos on server

**Total: 22 entities per device**

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

## Performance & Resource Usage

### Polling Intervals

**Normal Mode** (default: 15 minutes)
- Minimal battery drain on device
- Queries FMD server for existing location data
- Does NOT request new device location from the android device
- Recommended for stationary devices and those that are sensitive to battery drain

**High Frequency Mode** (default: 5 minutes)
- ⚠️ **Higher battery drain** - requests new location each poll
- Actively asks device for new location information from a configured source
- Best for: lost device tracking, active travel while charging
- Auto-disable after tracking session

### Battery Impact on Android Device

| Feature | Battery Impact | When to Use |
|---------|----------------|-------------|
| Normal polling | ⚡ Minimal | Always |
| High frequency mode | ⚡⚡⚡ High | Lost device, active tracking |
| GPS Only location | ⚡⚡⚡ High | Need accuracy |
| Cell Only location | ⚡ Minimal | Fast/rough location |
| Last Known location | ⚡ None | No new request needed |
| Photo capture | ⚡⚡ Medium | As needed |

### Home Assistant Resource Usage

**Storage:**
- Photos: ~2-3 MB per photo
- Default 10 photos = ~25 MB per device
- Max 50 photos = ~125 MB per device
- Location data: Negligible (<1 MB)

**Network:**
- Location poll: ~1-5 KB per request
- Photo download: ~2-3 MB per photo
- Encrypted data transfer (HTTPS recommended)

**CPU:**
- Decryption: Minimal (async operations)
- Photo processing: Medium (EXIF extraction)
- Normal operation: Low impact

### Optimization Tips

**For Battery Life:**
- Use "Cell Only (Fast)" when battery < 30%
- Use "GPS Only (Accurate)" when charging
- Increase normal polling interval (60+ minutes)
- Disable high frequency mode when not needed

**For Accuracy:**
- Location Source: "GPS Only (Accurate)"
- Allow Inaccurate Locations: OFF
- High Frequency Mode: ON (when tracking actively)

**For Storage:**
- Set Max Photos to 5-10 (not 50)
- Manually delete old photos periodically
- Consider automation to clean media folder

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
Configure which location provider is used by the **Location Update button** AND **High Frequency Mode**:
- **All Providers (Default)**: Uses GPS, network, and fused location for best reliability
- **GPS Only (Accurate)**: Most accurate but slower, requires clear sky view, uses more battery
- **Cell Only (Fast)**: Fast but less accurate, uses cellular tower triangulation
- **Last Known (No Request)**: Returns cached location without new GPS request (instant, no battery use)

Use the Location Source select entity to change the provider. The setting persists and affects:
1. **Manual Updates**: When pressing the "Location Update" button.
2. **High Frequency Mode**: When active tracking is enabled, each poll uses this source.

*Note: Normal polling mode (passive) is unaffected by this setting as it only fetches existing data from the server.*

**Example automation for enabling battery-conscious location tracking:**
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
      - service: switch.turn_on
        target:
          entity_id: switch.fmd_test_user_high_frequency_mode
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
   - Turn on the "Wipe: ⚠️ Safety switch ⚠️"
   - This allows the wipe button to function
   - ⏰ **Automatically disables after 60 seconds**

2. **Press Wipe Button:**
   - While safety switch is enabled, press "Wipe: ⚠️ Execute ⚠️" button
   - Device will be factory reset (all data erased)
   - Safety switch automatically disables after use

**Use Cases:**
- Device is lost/stolen and you want to protect your data
- Device needs to be decommissioned or sold
- Final resort for security/privacy protection

**Important Notes:**
- This command **CANNOT BE UNDONE**
- All data: apps, files, photos, accounts (EVERYTHING!) will be deleted
- Device will return to factory settings
- You'll need physical access to set up the device again

**Note:** Bluetooth, DND, and Ringer commands are fire-and-forget. Home Assistant doesn't track the actual device state, so the select entities always show "Send Command..." as a placeholder.

## Automation Examples

### Basic Location Tracking

**Notify when device arrives home:**
```yaml
automation:
  - alias: "FMD: Notify device arrived home"
    trigger:
      - platform: zone
        entity_id: device_tracker.fmd_my_phone
        zone: zone.home
        event: enter
    action:
      - service: notify.mobile_app
        data:
          title: "Device Tracking"
          message: "My phone arrived home"
```

**Track device leaving work:**
```yaml
automation:
  - alias: "FMD: Start tracking when leaving work"
    trigger:
      - platform: zone
        entity_id: device_tracker.fmd_my_phone
        zone: zone.work
        event: leave
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.fmd_my_phone_high_frequency_mode
      - delay:
          minutes: 30
      - service: switch.turn_off
        target:
          entity_id: switch.fmd_my_phone_high_frequency_mode
```

### Remote Device Control

**Bedtime routine - Enable DND:**
```yaml
automation:
  - alias: "FMD: Bedtime DND"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.fmd_my_phone_do_not_disturb_command
        data:
          option: "Enable Do Not Disturb"
```

**Morning routine - Disable DND:**
```yaml
automation:
  - alias: "FMD: Morning wake up"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.workday_sensor
        state: "on"
    action:
      - service: select.select_option
        target:
          entity_id: select.fmd_my_phone_do_not_disturb_command
        data:
          option: "Disable Do Not Disturb"
```

**Silent mode during meetings:**
```yaml
automation:
  - alias: "FMD: Silent during calendar events"
    trigger:
      - platform: state
        entity_id: calendar.work_calendar
        to: "on"
    action:
      - service: select.select_option
        target:
          entity_id: select.fmd_my_phone_ringer_mode_command
        data:
          option: "Silent"
```

### Lost Device Actions

**Ring when device battery is low and not home:**
```yaml
automation:
  - alias: "FMD: Low battery not home alert"
    trigger:
      - platform: numeric_state
        entity_id: device_tracker.fmd_my_phone
        attribute: battery_level
        below: 15
    condition:
      - condition: not
        conditions:
          - condition: zone
            entity_id: device_tracker.fmd_my_phone
            zone: zone.home
    action:
      - service: notify.mobile_app
        data:
          title: "Low Battery Warning"
          message: "Phone battery at {{ states.device_tracker.fmd_my_phone.attributes.battery_level }}% and not home!"
      - service: button.press
        target:
          entity_id: button.fmd_my_phone_location_update
```

**Auto-capture photo when device enters geofence:**
```yaml
automation:
  - alias: "FMD: Capture photo on suspicious movement"
    trigger:
      - platform: zone
        entity_id: device_tracker.fmd_my_phone
        zone: zone.suspicious_area
        event: enter
    action:
      - service: button.press
        target:
          entity_id: button.fmd_my_phone_capture_rear
      - delay:
          seconds: 30
      - service: button.press
        target:
          entity_id: button.fmd_my_phone_download_photos
      - service: notify.mobile_app
        data:
          title: "Security Alert"
          message: "Device entered restricted zone - photo captured"
```

**Auto-capture photo when someone interacts with it (prior to unlock)**
```yaml
automation:
  - alias: "FMD: Capture photo on device interaction (uses optional sensor from Home Assistant App)"
    trigger:
      - trigger: state
        entity_id: binary_sensor.mydevice_interactive
        from: "off"
        to: "on"
    action:
      - service: button.press
        target:
          entity_id: button.fmd_my_phone_capture_rear
```
### Smart Tracking Modes

**Adaptive location precision based on motion:**
```yaml
automation:
  - alias: "FMD: Adaptive location precision"
    trigger:
      - platform: state
        entity_id: device_tracker.fmd_my_phone
        attribute: speed
    action:
      - choose:
          # Moving fast (vehicle) - use GPS only
          - conditions:
              - condition: template
                value_template: "{{ state_attr('device_tracker.fmd_my_phone', 'speed') | float(0) > 5 }}"
            sequence:
              - service: select.select_option
                target:
                  entity_id: select.fmd_my_phone_location_source
                data:
                  option: "GPS Only (Accurate)"
          # Stationary - use last known (save battery)
          - conditions:
              - condition: template
                value_template: "{{ state_attr('device_tracker.fmd_my_phone', 'speed') | float(0) == 0 }}"
            sequence:
              - service: select.select_option
                target:
                  entity_id: select.fmd_my_phone_location_source
                data:
                  option: "Last Known (No Request)"
        # Default - use all providers
        default:
          - service: select.select_option
            target:
              entity_id: select.fmd_my_phone_location_source
            data:
              option: "All Providers (Default)"
```

### Photo Management

**Daily photo capture and download:**
```yaml
automation:
  - alias: "FMD: Daily surveillance photo"
    trigger:
      - platform: time
        at: "12:00:00"
    action:
      - service: button.press
        target:
          entity_id: button.fmd_my_phone_capture_front
      - delay:
          seconds: 30
      - service: button.press
        target:
          entity_id: button.fmd_my_phone_download_photos
```

**Notify when new photos downloaded:**
```yaml
automation:
  - alias: "FMD: Photo download notification"
    trigger:
      - platform: state
        entity_id: sensor.fmd_my_phone_photo_count
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state | int(0) > trigger.from_state.state | int(0) }}"
    action:
      - service: notify.mobile_app
        data:
          title: "FMD Photos"
          message: "Downloaded {{ trigger.to_state.state }} new photo(s) from device"
```

## Security & Privacy

### Password-Free Authentication (fmd_api 2.0.4+)

**🔐 Enhanced Security with Authentication Artifacts**

Starting with fmd_api 2.0.4, this integration uses **password-free authentication** for improved security:

- **No raw password storage**: Your FMD password is never stored in Home Assistant
- **Secure artifacts**: Uses authentication tokens, private keys, and password hash instead
- **Automatic migration**: Existing installations automatically upgrade to secure storage
- **Seamless reauth**: Client automatically refreshes tokens without re-entering password
- **Future-proof**: Designed for long-term secure authentication

**How It Works:**
1. During initial setup, you enter your FMD password once
2. Integration authenticates and immediately exports secure artifacts
3. Password is discarded - only artifacts are stored
4. On startup, integration uses artifacts to reconnect (no password needed)
5. If credentials expire, reauth flow generates new artifacts

**Migration for Existing Users:**
- Automatic on next restart after upgrade
- No action required - seamless transition
- Old password-based entries converted to artifacts
- Reauth flow also uses new artifact-based system

### Best Practices

**🔐 Secure Your FMD Server**
- Use HTTPS (not HTTP) for your FMD server URL
- Use strong, unique passwords (20+ characters recommended)
- Run FMD server on a private network or VPN
- Keep FMD server software updated
- Use firewall rules to restrict access

**🔑 Home Assistant Security**
- Enable authentication on Home Assistant
- Use strong passwords or API tokens
- Consider network isolation for device tracking
- Regularly review Home Assistant logs
- Keep Home Assistant updated

**📱 Android App Permissions**

The FMD Android app requires these permissions:
- ✅ Location (always) - For tracking
- ✅ Camera - For photo capture
- ✅ Device Admin - For lock/wipe commands
- ⚠️ Bluetooth (Android 12+) - For Bluetooth control
- ⚠️ Do Not Disturb Access - For DND/ringer commands

**Grant permissions cautiously** - only enable what you need.

**🚨 Device Wipe Protection**

The integration includes multiple safety layers:
1. **Wipe PIN required** - Must set alphanumeric PIN (no spaces) before wipe works
2. **Safety switch required** - Must enable before wipe button activates
3. **60-second timeout** - Safety auto-disables after 1 minute
4. **PIN validation** - Ensures proper format before sending command
5. **Extensive logging** - CRITICAL warnings in logs
6. **Auto-disable after use** - Prevents repeated presses
7. **Cannot be undone** - Final warning in documentation

**PIN Requirements (fmd_api 2.0.4+):**
- Must be alphanumeric (letters and numbers only)
- Cannot contain spaces or special characters
- Must be ASCII characters only
- Recommended: 16+ characters (future-proofing)
- Set via "Wipe: PIN" text entity before attempting wipe

**⚠️ Privacy Considerations**
- Location data is encrypted in transit (RSA + AES-GCM)
- Photos are encrypted on FMD server
- Data is decrypted only on Home Assistant
- Photos stored locally on Home Assistant
- Review Home Assistant's `media/fmd/` permissions
- Consider who has access to your Home Assistant instance

**💡 Recommendations**
- Use this integration only on devices you own
- Inform device users they are being tracked
- Comply with local laws regarding tracking/surveillance
- Use device wipe only as last resort
- Test features in safe environment first
- Keep backups of important device data

## Testing

This integration includes comprehensive test coverage for Home Assistant Core submission requirements.

### Running Tests

**Install test dependencies:**
```bash
pip install -r requirements_test.txt
```

**Run all tests:**
```bash
pytest
```

**Run tests with coverage:**
```bash
pytest --cov=custom_components.fmd --cov-report=html --cov-report=term-missing
```

**View coverage report:**
```bash
# Open htmlcov/index.html in your browser
```

### Test Structure

The test suite includes:
- **Unit tests** - All platform entities (device_tracker, button, switch, select, number, sensor)
- **Integration tests** - Setup, unload, and error handling
- **Config flow tests** - User configuration, validation, and error scenarios
- **Fixtures** - Mock FMD API with realistic responses

**Test files:**
- `tests/conftest.py` - Shared fixtures and test helpers
- `tests/test_init.py` - Integration lifecycle tests
- `tests/test_config_flow.py` - Configuration flow tests
- `tests/test_device_tracker.py` - Device tracker entity tests
- `tests/test_button.py` - Button entity tests (7 buttons)
- `tests/test_switch.py` - Switch entity tests (4 switches)
- `tests/test_select.py` - Select entity tests (4 selects)
- `tests/test_number.py` - Number entity tests (3 numbers)
- `tests/test_sensor.py` - Sensor entity tests (photo count)

### Continuous Integration

Tests run automatically on every push and pull request via GitHub Actions:
- Python 3.11 and 3.12
- Coverage reporting to Codecov
- Automated test result checks

## Home Assistant Core Inclusion

### Requirements for Core Integration

To be included in Home Assistant Core, the following items must be completed:

**Code Quality & Standards:**
- [ ] **Code review** - Pass Home Assistant core team code review
- [x] **Type hints** - ✅ Add complete type hints to all functions and methods
- [ ] **Async best practices** - Ensure all I/O operations are properly async
- [ ] **Error handling** - Comprehensive error handling and user-friendly error messages
- [x] **Code coverage** - ✅ Achieve minimum 90% test coverage

**Testing:**
- [x] **Unit tests** - ✅ Write comprehensive unit tests for all components
- [x] **Integration tests** - ✅ Test config flow, entities, and device tracker
- [x] **Mock FMD server** - ✅ Create test fixtures for API responses
- [x] **Test coverage reports** - ✅ Set up pytest-cov and coverage reporting

**Documentation:**
- [ ] **Component documentation** - Create Home Assistant documentation page
- [ ] **Translation strings** - Add translation support for all UI strings
- [ ] **Configuration examples** - Provide YAML examples (if applicable)
- [ ] **Architecture documentation** - Document component architecture and design decisions

**Dependencies:**
- [x] **FMD client library** - Published as `fmd_api` PyPI package
  - ✅ Published at: https://pypi.org/project/fmd-api/
  - ✅ Follows semantic versioning (v0.1.0)
  - ✅ Separate repository with documentation
- [ ] **Dependency review** - All dependencies must be approved by HA core team

**Quality Assurance:**
- [ ] **Pylint/Flake8** - Pass all linting checks with HA configuration
- [ ] **MyPy** - Pass static type checking
- [ ] **hassfest** - Pass Home Assistant validation tool
- [ ] **Quality scale** - Achieve Bronze quality scale minimum (Silver preferred)

**Additional Requirements:**
- [x] **Branding** - ✅ Merged to Home Assistant brands repository
  - Official FMD icon now available globally
  - Path: `custom_integrations/fmd/`
- [ ] **IoT class** - Verify "cloud_polling" classification is appropriate
- [ ] **Breaking changes** - Document any breaking changes for migration
- [ ] **Performance** - Ensure efficient polling and minimal resource usage

### Planned Features

**Medium Priority:**
- [ ] **Device stats** - Display network information
  - IP address, WiFi SSID, WiFi BSSID
  - Requires FMD "stats" command parsing
  - Priority: Medium

- [ ] **GPS status** - Display GPS and battery status
  - GPS state (on/off), battery level
  - Requires FMD "gps" command parsing
  - Priority: Medium

**Low Priority:**
- [ ] **Account deletion** - FMD account management
  - Requires FMD server API addition
  - Low priority (can do manually on server)

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

### Known Limitations

**Location Updates:**
- ⏱️ Location polling is not real-time (minimum 1-minute interval)
- 🌍 Requires device to have internet connectivity
- 📡 GPS accuracy depends on device location (outdoors vs. indoors)
- ⚡ High frequency mode drains device battery faster

**Commands:**
- 📬 Commands are fire-and-forget (no confirmation from device)
- 🔄 Device must be online to receive commands
- ⏰ Command execution depends on device connectivity
- 🚫 No state feedback (can't query if Bluetooth is on/off)

**Photos:**
- 📸 Photo capture takes 15-30 seconds
- 💾 Photos remain on FMD server until manually deleted
- 📁 No automatic photo cleanup (must delete manually)
- 🖼️ EXIF timestamps may be missing from some photos

**Permissions:**
- ⚠️ Bluetooth control requires Android 12+ BLUETOOTH_CONNECT permission
- ⚠️ DND/Ringer control requires Do Not Disturb Access permission
- ⚠️ Some features may not work on all Android versions

**Device Wipe:**
- 🚨 Cannot be undone once device receives command
- ⏱️ Execution time depends on device (immediate to minutes)
- 📱 Requires device to be online to receive command
- 🔒 Device must have Device Admin permission granted to FMD app

## Version History

### v1.1.2 - November 18, 2025 (Maintenance)
Maintenance release to update dependencies and improve polling reliability.

Changes:
- 🎯 **Smarter High Frequency Tracking**: High Frequency Mode now respects your "Location Source" selection (e.g., Cell Only, GPS Only) instead of always forcing "All Providers".
- 📦 **Updated dependency** to `fmd-api==2.0.5`
- 🛡️ **Polling reliability**: Added protection against overlapping updates to prevent task pile-ups and ensure schedule adherence.
- 🔄 **Improved polling logic**: Ensures polling tasks are managed correctly, preventing stalls if the server or device is slow to respond.

### v1.1.1 - November 11, 2025 (Hotfix)
Short maintenance release focused on restoring button functionality introduced with the fmd_api 2.0.4 upgrade.

Changes:
- Fix: Button entities (Lock device, Photo: Download, Wipe: Execute) now work reliably by constructing `Device(client, device_id)` instead of calling a non-existent `client.device()` method. This also restores lock functionality, including support for custom lock-screen messages.
- Tests/Docs: Updated Device class mocking in tests and added Windows test setup guide at `docs/TESTS_WINDOWS.md`.

### v1.1.0 - November 9, 2025 (fmd_api 2.0.4 Integration)
**🔐 Security & Feature Update**

This version adopts all improvements from fmd_api 2.0.4, with focus on security and safety features.

**Highlights:**
- 🔐 **Password-free authentication** - Credentials stored as secure artifacts (no raw passwords)
- 📸 **Modern picture API** - Updated to use `get_picture_blobs()` and `decode_picture()`
- 🔑 **Wipe PIN validation** - Added required PIN entity for device wipe safety
- 💬 **Lock message support** - Optional message parameter for lock screen display
- 🛡️ **Enhanced error handling** - Specific exception types with clear user messages
- 📦 **Updated dependency** to `fmd-api==2.0.4`

**New Entities:**
- `text.fmd_{device}_wipe_pin` - Required alphanumeric PIN for device wipe (password-mode)
- `text.fmd_{device}_lock_message` - Optional message to display on lock screen

**Security Improvements:**
- **No raw password storage**: Automatic migration to secure authentication artifacts
- **PIN validation**: Wipe command requires validated alphanumeric PIN (no spaces)
- **Better errors**: FmdAuthError, FmdConnectionError, FmdError with actionable messages

**API Changes:**
- Deprecated picture methods replaced with modern alternatives
- Lock command now supports optional message parameter (client sanitizes automatically)
- Wipe command requires PIN and always passes confirm=True flag

**Migration:**
- **Automatic** - Existing installations migrate to password-free auth on startup
- **Seamless** - No user action required for authentication upgrade
- **Required** - Must set wipe PIN before device wipe button will work
- **Optional** - Lock message is optional (lock works without it)

**Upgrade Notes:**
1. Update via HACS (or pull latest release) and restart Home Assistant
2. Authentication automatically migrates to secure artifacts (password removed)
3. **Action required**: Set "Wipe: PIN" text entity before attempting device wipe
4. Optional: Set "Lock: Message" text entity for lock screen messages

**Breaking Changes:**
- Device wipe now requires PIN to be set (safety improvement)
- Internal picture API methods replaced (user-facing behavior unchanged)

### v1.0.0 - November 6, 2025 (Stable Release)
**🎉 First Stable Release**

This version marks the transition from beta to a stable, production-ready integration.

**Highlights:**
- 📦 Updated core dependency to `fmd-api==2.0.3` (performance & robustness improvements)
- ✅ Declared stable: no known critical issues after extended beta test of 0.9.x line
- 🧪 Maintains high test coverage (≥96%) across all entity platforms
- 🔐 Improved photo/media handling reliability in varied Home Assistant environments
- 🛠 Refined internal executor usage for non-blocking decrypt and file operations

**Upgrade Notes:**
1. Update via HACS (or pull latest release) and restart Home Assistant.
2. No reconfiguration required; existing config entries migrate seamlessly.
3. If you were on a pre-0.9.0 version, review the 0.9.x notes below for feature additions.

**Post-Upgrade Validation Checklist (optional):**
- Confirm device tracker updates within your configured interval.
- Press Location Update button and verify fresh attributes (provider, timestamp).
- (Optional) Capture and Download a photo to confirm media folder access.

**Looking Ahead:**
- Focus will shift to stablity and minor improvements to work towards inclusion in Home Assistant Core.

**Thanks** to all testers who helped harden the 0.9.x series.

### v0.9.9 - November 4, 2025
**🚀 MAJOR REWRITE: fmd-api v2.0.1 Migration (Beta)**

This was the final beta milestone preceding the stable 1.0.0 release and represented the most significant architectural overhaul since project inception.

**Breaking Changes:**
- 🔧 **Complete API rewrite** - Migrated from `fmd-api v1.x` to `fmd-api v2.0.1`
  - All FMD server communication now uses the new `FmdClient` class
  - Improved async/await patterns throughout
  - Enhanced error handling and connection management
- 📦 **Updated dependencies** - Now requires `fmd-api==2.0.1`
- 🔄 **Config flow improvements** - Added reauthentication flow support
- ⚙️ **State persistence** - All configuration entities (numbers, switches, selects) now properly restore state across restarts
- 🧪 **Test infrastructure overhaul** - Full test suite rewritten for new API patterns

**New Features:**
- ✅ **Reauthentication flow** - Update credentials without removing/re-adding integration
- ✅ **Persistent settings** - Entity configurations survive Home Assistant restarts
- ✅ **Improved location updates** - High-frequency mode now more reliable with better request handling
- ✅ **Better error handling** - ConfigEntryNotReady for graceful service outage handling

**Under the Hood:**
- 🏗️ **Modern API patterns** - `FmdClient.create()` factory method for async initialization
- 🔐 **Enhanced security** - Improved encryption and decryption handling via executor
- 📊 **Type safety** - Comprehensive type hints with TYPE_CHECKING guards
- 🧪 **Test coverage** - Maintained ~94% coverage with all 193 tests passing
- 🔧 **CI/CD improvements** - Resolved dependency conflicts (josepy/acme, aiohttp)
- 📝 **Code quality** - Removed migration comments, unified type hints, strict imports

**Migration Guide:**
1. Backup your configuration (Settings → System → Backups)
2. Update the integration via HACS
3. Restart Home Assistant
4. Verify all entities are working correctly
5. If you experience authentication errors, use the new reauthentication flow:
   - Go to Settings → Devices & Services → FMD
   - Click the three dots → Reconfigure
   - Enter your credentials again

**Known Issues:**
- None currently - please report any issues on GitHub!

**Transition:** Community testing of this version informed the stability designation in v1.0.0.

**Technical Details:**
- All code strictly imports `FmdClient` (no fallback imports)
- Tests updated to mock `FmdClient` instead of legacy `FmdApi`
- Photo downloads use executor for decryption (non-blocking)
- Location polling respects configured intervals and sources
- Total entities: **20 per device**

**Credits:**
- Huge thanks to the FMD-FOSS team for the excellent FMD ecosystem
- Special thanks to beta testers and contributors

### v0.9.8 - October 26, 2025
**Test entity state restore**
- ✅ Extended solution for entity state to all that store values needing restored!
- Total entities: **20 per device**

### v0.9.7 - October 26, 2025
**Test entity state restore**
- ✅ Tested solution for entity state restore on restart/reload (Issue #1)
- Total entities: **20 per device**

### v0.9.6 - October 25, 2025
**Translations and code coverage**
- ✅ Added translation files for several languages
- ✅ Improved code testing coverage
- ✅ Initial work on reauthentication flow
- Total entities: **20 per device**

### v0.9.5 - October 24, 2025
**Graceful Error Handling & Linting**
- ✅ Added ConfigEntryNotReady exception for graceful handling of temporary service outages
- ✅ Fixed pre-commit pipeline with dynamic Python version support
- ✅ Resolved all linting issues (unused imports, line length violations)
- ✅ Improved code quality and compliance
- Total entities: **20 per device**

### v0.9.0 - October 22, 2025
**Major Refactor: PyPI Package Migration**
- ✅ Migrated from embedded `fmd_client` to PyPI package `fmd-api`
- ✅ Simplified dependencies and improved maintainability
- ✅ Separate versioning for API client library
- ✅ Photo storage management improvements
  - Changed photo count sensor to show total stored photos
  - Added `last_download_count` attribute
  - Renamed "Max photos to download" → "Photo: Max to retain"
  - Added "Photo: Auto-cleanup" switch (default OFF)
  - Automatic deletion of oldest photos when limit exceeded
- ✅ Fixed entity icons for location update and high-frequency interval
- ✅ **Official branding merged to Home Assistant brands repository**
  - Integration now displays official FMD icon globally
  - Available at: `custom_integrations/fmd/`
- Total entities: **20 per device**

### v0.8.3 - October 22, 2025
**Icon Improvements**
- ✅ Submitted integration branding to Home Assistant brands repository
- ✅ Improved entity icon definitions
- Total entities: 20 per device

### v0.8.2 - October 20, 2025
**Unit Conversion Feature**
- ✅ Added imperial units configuration option
- ✅ Converts speed (m/s → mph), altitude (m → ft), and GPS accuracy (m → ft)
- ✅ Added unit indicators in device tracker attributes
- ✅ Configurable during initial setup
- Total entities: 20 per device

### v0.8.1 - October 20, 2025
**UX Improvements: Entity Naming & Organization**
- ✅ Improved entity naming for better organization
- ✅ Photo entities grouped with "Photo:" prefix
- ✅ Wipe entities clearly marked with ⚠️ warning symbol
- ✅ Simplified select entity names
- Total entities: 19 per device

### v0.8.0 - October 20, 2025
**Phase 4: Device Wipe with Safety Mechanism**
- ✅ Added Device Wipe button (factory reset)
- ✅ Added Device Wipe Safety switch (60-second timeout)
- ✅ Enhanced logging for wipe operations
- ✅ Two-step safety process to prevent accidents
- ✅ MIT License added
- ✅ Comprehensive FMD team attribution
- Total entities: 19 per device

### v0.7.0 - October 20, 2025
**Phase 2: Configurable Location Source**
- ✅ Added Location Source select entity
- ✅ Four location modes: All/GPS/Cell/Last Known
- ✅ Battery-conscious tracking support
- Total entities: 17 per device

### v0.6.0 - October 2025
**Phase 1: Device Control Commands**
- ✅ Added Bluetooth, DND, and Ringer Mode control
- ✅ Select entity placeholder pattern
- Total entities: 16 per device

### v0.5.0 - October 2025
**Photo Capture & Download**
- ✅ Front & rear camera capture
- ✅ Photo download with encryption
- ✅ Media browser integration
- ✅ EXIF timestamp extraction

## Frequently Asked Questions (FAQ)

**Q: Do I need to run my own FMD server?**
A: Hosting your own is preferred but this integration can be used with a publically hosted FMD server, like the one hosted by [Nulide](https://server.fmd-foss.org/).  To host your own please see [FMD Server setup](https://gitlab.com/fmd-foss/fmd-server).

**Q: Does this work without the FMD Android app?**
A: No, you must install the FMD Android app on the device you want to track. The app communicates with the FMD server though, not directly with the android app!

**Q: Can I track multiple devices?**
A: Yes! Add a new integration instance for each device. Each device gets its own set of entities.

**Q: Why is my location not updating?**
A: Check: 1) Device has internet, 2) FMD app is running, 3) Location permissions granted, 4) Device is sending data to server (check FMD server logs).  If you aren't seeing location data with this integration, first login to the FMD server directly to see if the data has actually been sent there.

**Q: How do I know if a command was received?**
A: Commands are fire-and-forget. Check device physically or use another method to confirm. There's no acknowledgment from the device.

**Q: Can I see Bluetooth/DND state in Home Assistant?**
A: No, FMD doesn't support querying device state. Commands are one-way only.  You can, however, configure the official Home Assistant App to enable sensors so it collects this information.

**Q: How much battery will this use on my android device?**
A: Normal mode: None, since it just polls the FMD server.
High-frequency mode: Can use significant battery depending on the location update type that is configured.  This will actively wake up the device every X minutes to request new or cached location information. See [Performance](#performance--resource-usage).

**Q: Where are photos stored?**
A: `/media/fmd/<device-id>/` (Docker/Core) or `/config/media/fmd/<device-id>/` (HAOS). Photos appear in Media Browser automatically.
They will not populate here automatically.  You'll need to click the Download button entity first.  If photos exist for that user, you'll see the photo_count entity reflect the number of saved photos.

**Q: Can I download photos older than the configured max?**
A: No, increase "Max Photos to Download" setting before pressing "Download Photos" to get more history.
If your photo_max_to_retain entity is configured with a value of 10 and you have 12 photos in your FMD account then the oldest 2 will be deleted when you click the Download button in Home Assistant.  This will only delete the copies in Home Assistant.  No changes will be made to your FMD account or the data stored there.

**Q: Is my data encrypted?**
A: It is encrypted on the FMD server but is not encrypted in Home Assistant.  Any users with access to Home Assistant will essentially have access to all of the features of FMD, including your photos and the ability to factory reset your device.  Use with caution!

**Q: What happens if I accidentally press the wipe button?**
A: Nothing! The safety switch must be enabled first. The wipe button is blocked by default.
If the safety switch is turned On and the Wipe/Execute button is pressed, a timer will begin that will factory reset your device in 60 seconds.

**Q: Can I undo a device wipe?**
A: No, device wipe is permanent. All data is erased. This is an FMD feature, not controllable by this integration.

**Q: Does this work on iOS/iPhone?**
A: No, FMD is Android-only. This integration only works with Android devices running the FMD app.

**Q: Can I use this for fleet/business tracking?**
A: Yes, the MIT License allows commercial use. Add one integration instance per device.

## Credits and Attribution

This integration would not exist without the excellent work of the **FMD-FOSS team**:

- **FMD Project**: https://fmd-foss.org
- **Created by**: [Nulide](http://nulide.de) (Founder)
- **Maintained by**: [Thore](https://thore.io) and the FMD-FOSS team
- **FMD Android App**: https://gitlab.com/fmd-foss/fmd-android
- **FMD Server**: https://gitlab.com/fmd-foss/fmd-server
- **FMD Home Assistant Integration**: https://github.com/devinslick/home-assistant-fmd

**Thank you** to Nulide, Thore, and all FMD contributors for creating this privacy-respecting, open source device tracking solution!

This integration is a third-party client that communicates with FMD servers. It is not affiliated with or endorsed by the FMD-FOSS project. For full attribution details, see [CREDITS.md](CREDITS.md).

### Supporting FMD

If you find this integration useful, please support the FMD project:
- ⭐ Star the [FMD repositories](https://gitlab.com/fmd-foss) on GitLab
- 📝 Contribute to the FMD project
- 📢 Spread the word about FMD

## Contributions

Contributions to this Home Assistant integration are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.

### Development
This integration uses:
- Async/await for all I/O operations
- aiohttp for HTTP communication
- RSA-3072 encryption for key exchange
- AES-GCM for data encryption
- Argon2id for password hashing

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

This integration is completely free and open source. You are free to use, modify, and distribute it according to the terms of the MIT License.

### What this means:
- ✅ **Free to use** for personal or commercial purposes
- ✅ **Free to modify** and create derivative works
- ✅ **Free to distribute** original or modified versions
- ✅ **No warranty** - provided "as is"
- ✅ **Attribution appreciated** but not legally required
