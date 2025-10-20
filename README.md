# Home Assistant FMD Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for [FMD (Find My Device)](https://fmd-foss.org) that allows you to track and control Android devices running the FMD app through your self-hosted FMD server.

## About FMD

**FMD (Find My Device)** is a free and open source device tracking solution created by [Nulide](http://nulide.de) and maintained by the FMD-FOSS team.

- **FMD Android App**: https://gitlab.com/fmd-foss/fmd-android
- **FMD Server**: https://gitlab.com/fmd-foss/fmd-server
- **Website**: https://fmd-foss.org

This integration acts as a **client** for your FMD server, providing seamless integration with Home Assistant. See [CREDITS.md](CREDITS.md) for full attribution.

## Quick Start Overview

This integration provides **19 entities** to control your Android device:

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
2. ✅ **FMD Server** (v012.0 or compatible)
   - Self-hosted or hosted instance
   - HTTPS recommended (not HTTP)
   - Network accessible from Home Assistant
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
- ❌ FMD web interface (integration connects directly to API)
- ❌ Public IP address (works on local network)
- ❌ Cloud services (fully self-hosted)

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

- **Ring device** - Make the device ring at maximum volume
  - Entity ID example: `button.fmd_test_user_ring`
  - Sends a ring command to the device, making it play a loud sound
  - Useful for finding a lost device nearby
  - ✅ **Fully implemented** - Triggers ring command immediately

- **Lock device** - Lock the device screen
  - Entity ID example: `button.fmd_test_user_lock`
  - Sends a lock command to secure the device
  - Useful if device is lost or stolen
  - ✅ **Fully implemented** - Triggers lock command immediately

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
  - Decrypts and saves photos to `/config/media/fmd/` folder
  - Photos automatically appear in Home Assistant's Media Browser
  - Updates the "Photo Count" sensor
  - ✅ **Fully implemented** - Downloads photos to media browser

- **⚠️ Wipe: Execute** - ⚠️ **DANGEROUS**: Factory reset the device (erases ALL data)
  - Entity ID example: `button.fmd_test_user_wipe_device`
  - **Requires "⚠️ Wipe: Safety switch" to be enabled first**
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

- **⚠️ Wipe: Safety switch** - Safety switch for device wipe command
  - Entity ID example: `switch.fmd_test_user_device_wipe_safety`
  - Must be enabled before the "⚠️ Wipe: Execute" button will function
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

- **Do Not Disturb** - Send DND enable/disable commands
  - Entity ID example: `select.fmd_test_user_do_not_disturb_command`
  - Options: "Send Command...", "Enable Do Not Disturb", "Disable Do Not Disturb"
  - Sends command to device, then resets to placeholder
  - ⚠️ **Requires Do Not Disturb Access permission**
  - ✅ **Fully implemented** - Commands sent immediately, no state tracking

- **Ringer mode** - Set device ringer mode
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

## Performance & Resource Usage

### Polling Intervals

**Normal Mode** (default: 30 minutes)
- Minimal battery drain on device
- Queries FMD server for existing location data
- Does NOT request new device location
- Recommended for stationary devices

**High Frequency Mode** (default: 5 minutes)
- ⚠️ **Higher battery drain** - requests new location each poll
- Actively asks device for fresh GPS data
- Best for: lost device tracking, active travel
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
   - Turn on the "⚠️ Wipe: Safety switch"
   - This allows the wipe button to function
   - ⏰ **Automatically disables after 60 seconds**

2. **Press Wipe Button:**
   - While safety switch is enabled, press "⚠️ Wipe: Execute" button
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
1. **Safety switch required** - Must enable before wipe works
2. **60-second timeout** - Safety auto-disables after 1 minute
3. **Extensive logging** - CRITICAL warnings in logs
4. **Auto-disable after use** - Prevents repeated presses
5. **Cannot be undone** - Final warning in documentation

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

## TODO & Planned Features

### Known Issues
- [ ] **BUG: Entity icons** - Integration icon and 2 entity icons not displaying
  - Affected: integration, `high_frequency_interval`, `location_update`
  - Priority: Low (cosmetic)

### UX Improvements
- [ ] **Entity naming consistency** - "High frequency mode" → "Tracking mode"
  - Consider renaming for better clarity
  - Priority: Medium

### Planned Features

**High Priority:**
- [ ] **Photo cleanup** - Automatic or manual deletion of old photos
  - Option 1: Delete after X days
  - Option 2: "Delete All Photos" button
  - Priority: High (storage management)

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

### Version History

#### v0.8.1 (Current) - October 20, 2025
**UX Improvements: Entity Naming & Organization**
- ✅ Improved entity naming for better organization
- ✅ Photo entities grouped with "Photo:" prefix
- ✅ Wipe entities clearly marked with ⚠️ warning symbol
- ✅ Simplified select entity names (removed redundant "command")
- ✅ Device control entities clarified ("Ring device", "Lock device")
- Total entities: 19 per device

#### v0.8.0 - October 20, 2025
**Phase 4: Device Wipe with Safety Mechanism**
- ✅ Added Device Wipe button (factory reset)
- ✅ Added Device Wipe Safety switch (60-second timeout)
- ✅ Enhanced logging for wipe operations
- ✅ Two-step safety process to prevent accidents
- ✅ MIT License added
- ✅ Comprehensive FMD team attribution (CREDITS.md, NOTICE)
- Total entities: 19 per device

#### v0.7.0 - October 20, 2025
**Phase 2: Configurable Location Source**
- ✅ Added Location Source select entity
- ✅ Four location modes: All/GPS/Cell/Last Known
- ✅ Battery-conscious tracking support
- ✅ Dynamic location provider selection
- Total entities: 17 per device

#### v0.6.0 - October 2025
**Phase 1: Device Control Commands**
- ✅ Added Bluetooth control select entity
- ✅ Added Do Not Disturb control select entity
- ✅ Added Ringer Mode control select entity
- ✅ Select entity placeholder pattern (resets after command)
- Total entities: 16 per device

#### v0.5.0-0.5.6 - October 2025
**Photo Capture & Download**
- ✅ Front & rear camera capture buttons
- ✅ Photo download button
- ✅ Media browser integration
- ✅ EXIF timestamp extraction
- ✅ Photo Count sensor
- ✅ Max Photos configurable (1-50)
- ✅ Duplicate prevention via content hash

#### Earlier Versions
**Core Functionality**
- ✅ Device tracker entity
- ✅ Location polling (normal & high-frequency modes)
- ✅ Ring & Lock buttons
- ✅ Update interval configuration
- ✅ Location accuracy filtering
- ✅ Smart location selection (5 most recent)

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

## Frequently Asked Questions (FAQ)

**Q: Do I need to run my own FMD server?**  
A: Yes, this integration requires a self-hosted or hosted FMD server. The integration connects to YOUR server, not a centralized service. See [FMD Server setup](https://gitlab.com/fmd-foss/fmd-server).

**Q: Does this work without the FMD Android app?**  
A: No, you must install the FMD Android app on the device you want to track. The app communicates with the FMD server.

**Q: Can I track multiple devices?**  
A: Yes! Add a new integration instance for each device. Each device gets its own set of 19 entities.

**Q: Why is my location not updating?**  
A: Check: 1) Device has internet, 2) FMD app is running, 3) Location permissions granted, 4) Device is sending data to server (check FMD server logs).

**Q: How do I know if a command was received?**  
A: Commands are fire-and-forget. Check device physically or use another method to confirm. There's no acknowledgment from the device.

**Q: Can I see Bluetooth/DND state in Home Assistant?**  
A: No, FMD doesn't support querying device state. Commands are one-way only.

**Q: How much battery does this use?**  
A: Normal mode: minimal (just checks server). High frequency mode: significant (actively requests GPS). See [Performance](#performance--resource-usage).

**Q: Where are photos stored?**  
A: `/media/fmd/<device-id>/` (Docker/Core) or `/config/media/fmd/<device-id>/` (HAOS). Photos appear in Media Browser automatically.

**Q: Can I download photos older than the configured max?**  
A: No, increase "Max Photos to Download" setting before pressing "Download Photos" to get more history.

**Q: Is my data encrypted?**  
A: Yes! Location and photos are encrypted end-to-end using RSA-3072 + AES-GCM. Only your Home Assistant instance can decrypt.

**Q: What happens if I accidentally press the wipe button?**  
A: Nothing! The safety switch must be enabled first. The wipe button is blocked by default.

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
