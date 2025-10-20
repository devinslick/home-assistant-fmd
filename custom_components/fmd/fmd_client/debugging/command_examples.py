#!/usr/bin/env python3
"""
Comprehensive examples demonstrating all FMD device commands.

This script shows how to use each command type with the FmdApi class,
including string commands, constants, and convenience methods.

Usage:
    python command_examples.py --url <server_url> --id <device_id> --password <password>
"""
import argparse
import asyncio
import sys
import os

# Add parent directory to path to import fmd_api
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fmd_api import FmdApi, FmdCommands


async def demonstrate_location_commands(api):
    """Demonstrate all location request variations."""
    print("\n=== Location Commands ===")
    
    # Using convenience method (RECOMMENDED)
    print("1. Request location with all providers (convenience method):")
    await api.request_location('all')
    
    print("2. Request GPS-only location:")
    await api.request_location('gps')
    
    print("3. Request cellular network location:")
    await api.request_location('cell')
    
    # Using constants
    print("4. Using FmdCommands constants:")
    await api.send_command(FmdCommands.LOCATE_GPS)
    
    # Using raw strings
    print("5. Using raw command strings:")
    await api.send_command('locate')


async def demonstrate_device_control(api):
    """Demonstrate device control commands."""
    print("\n=== Device Control Commands ===")
    
    # Ring
    print("1. Ring device (full volume, ignores DND):")
    await api.send_command(FmdCommands.RING)
    # Alternative: await api.send_command('ring')
    
    # Lock
    print("2. Lock device screen:")
    await api.send_command(FmdCommands.LOCK)
    # Alternative: await api.send_command('lock')
    
    # Delete (COMMENTED OUT - DESTRUCTIVE!)
    print("3. Delete/wipe device (DESTRUCTIVE - NOT EXECUTED):")
    print("   # await api.send_command(FmdCommands.DELETE)")
    print("   # await api.send_command('delete')")


async def demonstrate_camera_commands(api):
    """Demonstrate camera commands."""
    print("\n=== Camera Commands ===")
    
    # Using convenience method (RECOMMENDED)
    print("1. Take picture with rear camera (convenience method):")
    await api.take_picture('back')
    
    print("2. Take picture with front camera:")
    await api.take_picture('front')
    
    # Using constants
    print("3. Using FmdCommands constants:")
    await api.send_command(FmdCommands.CAMERA_BACK)
    await api.send_command(FmdCommands.CAMERA_FRONT)
    
    # Using raw strings
    print("4. Using raw command strings:")
    await api.send_command('camera back')
    await api.send_command('camera front')


async def demonstrate_bluetooth_commands(api):
    """Demonstrate Bluetooth control."""
    print("\n=== Bluetooth Commands ===")
    print("Note: Android 12+ requires BLUETOOTH_CONNECT permission")
    
    # Using convenience method (RECOMMENDED)
    print("1. Enable Bluetooth (convenience method):")
    await api.toggle_bluetooth(True)
    
    print("2. Disable Bluetooth:")
    await api.toggle_bluetooth(False)
    
    # Using constants
    print("3. Using FmdCommands constants:")
    await api.send_command(FmdCommands.BLUETOOTH_ON)
    await api.send_command(FmdCommands.BLUETOOTH_OFF)
    
    # Using raw strings
    print("4. Using raw command strings:")
    await api.send_command('bluetooth on')
    await api.send_command('bluetooth off')


async def demonstrate_dnd_commands(api):
    """Demonstrate Do Not Disturb control."""
    print("\n=== Do Not Disturb Commands ===")
    print("Note: Requires Do Not Disturb Access permission")
    
    # Using convenience method (RECOMMENDED)
    print("1. Enable DND (convenience method):")
    await api.toggle_do_not_disturb(True)
    
    print("2. Disable DND:")
    await api.toggle_do_not_disturb(False)
    
    # Using constants
    print("3. Using FmdCommands constants:")
    await api.send_command(FmdCommands.NODISTURB_ON)
    await api.send_command(FmdCommands.NODISTURB_OFF)
    
    # Using raw strings
    print("4. Using raw command strings:")
    await api.send_command('nodisturb on')
    await api.send_command('nodisturb off')


async def demonstrate_ringer_mode_commands(api):
    """Demonstrate ringer mode control."""
    print("\n=== Ringer Mode Commands ===")
    print("Note: 'silent' mode also enables DND (Android behavior)")
    print("      Requires Do Not Disturb Access permission")
    
    # Using convenience method (RECOMMENDED)
    print("1. Set to normal mode (sound + vibrate) - convenience method:")
    await api.set_ringer_mode('normal')
    
    print("2. Set to vibrate mode:")
    await api.set_ringer_mode('vibrate')
    
    print("3. Set to silent mode (also enables DND):")
    await api.set_ringer_mode('silent')
    
    # Using constants
    print("4. Using FmdCommands constants:")
    await api.send_command(FmdCommands.RINGERMODE_NORMAL)
    await api.send_command(FmdCommands.RINGERMODE_VIBRATE)
    await api.send_command(FmdCommands.RINGERMODE_SILENT)
    
    # Using raw strings
    print("5. Using raw command strings:")
    await api.send_command('ringermode normal')
    await api.send_command('ringermode vibrate')
    await api.send_command('ringermode silent')


async def demonstrate_info_commands(api):
    """Demonstrate information/status commands."""
    print("\n=== Information/Status Commands ===")
    
    # Using convenience method (RECOMMENDED)
    print("1. Get network statistics (convenience method):")
    await api.get_device_stats()
    
    # Using constants
    print("2. Using FmdCommands constants:")
    await api.send_command(FmdCommands.STATS)
    await api.send_command(FmdCommands.GPS)
    
    # Using raw strings
    print("3. Using raw command strings:")
    await api.send_command('stats')  # IP addresses, WiFi SSID/BSSID
    await api.send_command('gps')    # Battery and GPS status


async def main():
    parser = argparse.ArgumentParser(
        description='Comprehensive examples of all FMD device commands',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Show all location command examples
    python command_examples.py --url https://fmd.example.com --id alice --password secret

    # The script demonstrates but doesn't actually execute commands by default.
    # Uncomment specific sections to test commands on your device.
        """
    )
    parser.add_argument('--url', required=True, help='FMD server URL')
    parser.add_argument('--id', required=True, help='FMD device ID')
    parser.add_argument('--password', required=True, help='FMD password')
    
    args = parser.parse_args()
    
    print("FMD Command Examples")
    print("=" * 60)
    print(f"Server: {args.url}")
    print(f"Device: {args.id}")
    print()
    print("NOTE: This script demonstrates command syntax but does NOT")
    print("      actually execute commands. Uncomment sections below")
    print("      to test specific commands on your device.")
    print("=" * 60)
    
    # Authenticate
    print("\nAuthenticating...")
    api = await FmdApi.create(args.url, args.id, args.password)
    print("✓ Authenticated successfully")
    
    # Demonstrate each command category
    # UNCOMMENT the ones you want to actually test:
    
    # await demonstrate_location_commands(api)
    # await demonstrate_device_control(api)
    # await demonstrate_camera_commands(api)
    # await demonstrate_bluetooth_commands(api)
    # await demonstrate_dnd_commands(api)
    # await demonstrate_ringer_mode_commands(api)
    # await demonstrate_info_commands(api)
    
    print("\n" + "=" * 60)
    print("Command Examples Complete")
    print("=" * 60)
    print("\nTo actually execute commands:")
    print("1. Edit this script and uncomment the demonstrate_*() calls")
    print("2. Or use test_command.py for individual command testing:")
    print("   python test_command.py 'ring' --url <url> --id <id> --password <pass>")


if __name__ == '__main__':
    asyncio.run(main())
