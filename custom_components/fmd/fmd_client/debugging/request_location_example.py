#!/usr/bin/env python3
"""
Example script demonstrating how to request a new location update from a device.

This script shows the complete workflow:
1. Connect to FMD server and authenticate
2. Send a location request command to the device
3. Wait for the device to capture and upload the location
4. Fetch and display the new location

Usage:
    python request_location_example.py --url https://fmd.example.com --id device-id --password your-password

    Optional arguments:
    --provider all|gps|cell|last  Location provider to use (default: all)
    --wait SECONDS               Seconds to wait for location (default: 30)
"""

import asyncio
import argparse
import json
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path so we can import fmd_api
sys.path.insert(0, str(Path(__file__).parent.parent))

from fmd_api import FmdApi, FmdApiException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


async def request_and_fetch_location(url: str, device_id: str, password: str, provider: str = "all", wait_seconds: int = 30):
    """Request a new location and fetch it after a delay."""
    
    try:
        # Step 1: Authenticate
        log.info(f"Connecting to FMD server: {url}")
        api = await FmdApi.create(url, device_id, password)
        log.info("✓ Successfully authenticated")
        
        # Step 2: Get the current most recent location (for comparison)
        log.info("Fetching current location for comparison...")
        old_locations = await api.get_all_locations(1)
        old_location = None
        if old_locations and old_locations[0]:
            old_location = json.loads(api.decrypt_data_blob(old_locations[0]))
            old_time = datetime.fromtimestamp(old_location['date'] / 1000)
            log.info(f"Current location captured at: {old_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            log.info("No previous location found")
        
        # Step 3: Request a new location
        log.info(f"Requesting new location with provider: {provider}")
        await api.request_location(provider)
        log.info("✓ Location request sent to device")
        
        # Step 4: Wait for device to respond
        log.info(f"Waiting {wait_seconds} seconds for device to capture and upload location...")
        await asyncio.sleep(wait_seconds)
        
        # Step 5: Fetch the new location
        log.info("Fetching latest location...")
        new_locations = await api.get_all_locations(1)
        
        if not new_locations or not new_locations[0]:
            log.warning("No location found after waiting. Device may be offline or need more time.")
            log.info("Tip: Try waiting longer or check if the device has internet connectivity.")
            return
        
        new_location = json.loads(api.decrypt_data_blob(new_locations[0]))
        new_time = datetime.fromtimestamp(new_location['date'] / 1000)
        
        # Step 6: Check if we got a new location
        if old_location and new_location['date'] == old_location['date']:
            log.warning("Location has not been updated yet. Same timestamp as before.")
            log.info("Tip: Device may need more time, or may not have received the command.")
        else:
            log.info("✓ New location received!")
        
        # Step 7: Display the location details
        print("\n" + "=" * 70)
        print("LOCATION DETAILS")
        print("=" * 70)
        print(f"Timestamp:  {new_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Provider:   {new_location.get('provider', 'unknown')}")
        print(f"Latitude:   {new_location['lat']}")
        print(f"Longitude:  {new_location['lon']}")
        print(f"Battery:    {new_location.get('bat', 'unknown')}%")
        
        # Optional fields (GPS-dependent)
        if 'accuracy' in new_location:
            print(f"Accuracy:   {new_location['accuracy']:.1f} meters")
        if 'altitude' in new_location:
            print(f"Altitude:   {new_location['altitude']:.1f} meters")
        if 'speed' in new_location:
            print(f"Speed:      {new_location['speed']:.2f} m/s ({new_location['speed'] * 3.6:.1f} km/h)")
        if 'heading' in new_location:
            print(f"Heading:    {new_location['heading']:.1f}°")
        
        # Google Maps link
        print(f"\nMap link:   https://www.google.com/maps?q={new_location['lat']},{new_location['lon']}")
        print("=" * 70 + "\n")
        
        # Provide guidance based on results
        if old_location and new_location['date'] == old_location['date']:
            print("💡 TIPS FOR TROUBLESHOOTING:")
            print("   • Check that the FMD Android app is running on the device")
            print("   • Verify the device has internet connectivity")
            print("   • GPS locations can take 30-60 seconds to acquire (especially indoors)")
            print("   • Try increasing --wait time to 60+ seconds for GPS")
            print("   • Use --provider cell for faster (but less accurate) results")
        else:
            time_diff = (new_location['date'] - old_location['date']) / 1000 if old_location else 0
            if time_diff > 0:
                print(f"✓ Location was updated {time_diff:.0f} seconds after the previous one")
        
    except FmdApiException as e:
        log.error(f"FMD API error: {e}")
        sys.exit(1)
    except Exception as e:
        log.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Request a new location update from an FMD device')
    parser.add_argument('--url', required=True, help='FMD server URL (e.g., https://fmd.example.com)')
    parser.add_argument('--id', required=True, help='Device ID')
    parser.add_argument('--password', required=True, help='Device password')
    parser.add_argument('--provider', default='all', choices=['all', 'gps', 'cell', 'last'],
                       help='Location provider to use (default: all)')
    parser.add_argument('--wait', type=int, default=30,
                       help='Seconds to wait for location update (default: 30)')
    
    args = parser.parse_args()
    
    # Run the async function
    asyncio.run(request_and_fetch_location(args.url, args.id, args.password, args.provider, args.wait))


if __name__ == '__main__':
    main()
