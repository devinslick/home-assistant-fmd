# Home Assistant FMD Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

This is a Home Assistant integration for FMD (Find My Device). It allows you to track the location of your devices.

## Installation

### Manual Installation

1.  Copy the `custom_components/fmd` directory to your Home Assistant `custom_components` directory.
2.  Restart Home Assistant.

## Configuration

1.  Go to **Settings** -> **Devices & Services**.
2.  Click **Add Integration**.
3.  Search for "FMD" and select it.
4.  Enter your FMD server URL, ID, and password. You can also set the polling interval in minutes.
5.  Click **Submit**.

The integration will create a device tracker entity for your device.

## Contributions

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.
