#!/usr/bin/env python3
"""
Send commands to an FMD device.

Available commands:
  - ring                 Make device ring at maximum volume
  - lock                 Lock the device
  - locate               Request location (all providers)
  - locate gps           Request GPS location only
  - locate cell          Request cellular network location
  - locate last          Get last known location (no new request)
  - camera front         Take picture with front camera
  - camera back          Take picture with rear camera

Usage:
    python test_command.py ring
    python test_command.py "locate gps"
    python test_command.py "camera front"
    
    # With custom credentials:
    python test_command.py ring --url https://fmd.example.com --id device-id --password secret
"""

import asyncio
import argparse
import sys
sys.path.insert(0, '..')
from fmd_api import FmdApi, FmdApiException

async def send_command(url: str, device_id: str, password: str, command: str):
    """Send a command to the FMD device."""
    try:
        print(f"Authenticating with {url}...")
        api = await FmdApi.create(url, device_id, password)
        print("✓ Authenticated successfully")
        
        print(f"\nSending command: '{command}'")
        result = await api.send_command(command)
        
        if result:
            print("✓ Command sent successfully!")
            
            # Provide helpful context for each command type
            if command == 'ring':
                print("\n🔔 Your device should start ringing now!")
                print("   The ring will continue until you dismiss it on the device.")
            elif command == 'lock':
                print("\n🔒 Your device should now be locked.")
            elif 'locate' in command:
                print("\n📍 Location request sent to device.")
                print("   The device will capture and upload location in 10-60 seconds.")
                print("   Use request_location_example.py for full workflow with wait/fetch.")
            elif 'camera' in command:
                print("\n📷 Camera command sent to device.")
                print("   The device will take a picture and upload it.")
                print("   Check the FMD web interface or use get_pictures() to retrieve it.")
            
            return True
        else:
            print("✗ Command sending failed")
            return False
            
    except FmdApiException as e:
        print(f"✗ FMD API Error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Send commands to an FMD device',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  ring                 Make device ring at maximum volume
  lock                 Lock the device
  locate               Request location (all providers)
  locate gps           Request GPS location only
  locate cell          Request cellular network location
  locate last          Get last known location (no new request)
  camera front         Take picture with front camera
  camera back          Take picture with rear camera

Examples:
  python test_command.py ring
  python test_command.py "locate gps"
  python test_command.py lock --url https://fmd.example.com --id alice --password secret
        """
    )
    
    parser.add_argument('command', help='Command to send to the device')
    parser.add_argument('--url', required=True, help='FMD server URL')
    parser.add_argument('--id', required=True, help='Device ID')
    parser.add_argument('--password', required=True, help='Device password')
    
    args = parser.parse_args()
    
    # Run the async function
    success = asyncio.run(send_command(args.url, args.id, args.password, args.command))
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
