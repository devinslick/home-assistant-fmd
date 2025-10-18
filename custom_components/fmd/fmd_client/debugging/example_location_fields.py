#!/usr/bin/env python3
"""
Example script demonstrating how to use fmd_api.py to extract and work with
all location data fields including accuracy, altitude, speed, and heading.

This is a reference implementation for application developers integrating
the FMD API into their own applications.
"""
import sys
sys.path.insert(0, '..')
import asyncio
import json
from datetime import datetime
from fmd_api import FmdApi


async def main():
    """Demonstrates extracting and using all location data fields."""
    
    # 1. Authenticate and create API client
    print("Authenticating with FMD server...")
    api = await FmdApi.create(
        'https://fmd.example.com',  # Replace with your FMD server URL
        'your-device-id',            # Replace with your device ID
        'your-password'              # Replace with your password
    )
    print("✓ Authenticated successfully\n")
    
    # 2. Fetch recent locations
    print("Fetching 5 most recent locations...")
    location_blobs = await api.get_all_locations(num_to_get=5)
    print(f"✓ Retrieved {len(location_blobs)} location(s)\n")
    
    # 3. Process each location
    for i, blob in enumerate(location_blobs, 1):
        print(f"--- Location {i} ---")
        
        # Decrypt the blob
        decrypted_bytes = api.decrypt_data_blob(blob)
        location = json.loads(decrypted_bytes)
        
        # === ALWAYS-PRESENT FIELDS ===
        timestamp = location['time']      # "Sat Oct 18 14:08:20 CDT 2025"
        date_ms = location['date']        # Unix timestamp in milliseconds
        provider = location['provider']   # "gps", "network", "fused", "BeaconDB"
        battery = location['bat']         # 0-100
        latitude = location['lat']        # degrees
        longitude = location['lon']       # degrees
        
        print(f"Time: {timestamp}")
        print(f"Provider: {provider}")
        print(f"Battery: {battery}%")
        print(f"Coordinates: ({latitude:.6f}, {longitude:.6f})")
        
        # === OPTIONAL FIELDS (use .get() to avoid KeyError) ===
        
        # Accuracy (meters) - GPS uncertainty radius
        accuracy = location.get('accuracy')
        if accuracy is not None:
            print(f"Accuracy: ±{accuracy:.1f} meters")
        else:
            print("Accuracy: Not available")
        
        # Altitude (meters above sea level)
        altitude = location.get('altitude')
        if altitude is not None:
            print(f"Altitude: {altitude:.1f} meters")
        else:
            print("Altitude: Not available")
        
        # Speed (meters/second) - Only present when device is moving
        speed = location.get('speed')
        if speed is not None:
            # Convert to different units
            speed_kmh = speed * 3.6
            speed_mph = speed * 2.237
            print(f"Speed: {speed:.2f} m/s ({speed_kmh:.1f} km/h, {speed_mph:.1f} mph)")
        else:
            print("Speed: Not available (stationary or no GPS)")
        
        # Heading (degrees 0-360) - Compass direction of movement
        heading = location.get('heading')
        if heading is not None:
            # Convert to compass direction
            directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                         "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            idx = int((heading + 11.25) / 22.5) % 16
            compass = directions[idx]
            print(f"Heading: {heading:.1f}° ({compass})")
        else:
            print("Heading: Not available (stationary or no direction)")
        
        # === PRACTICAL EXAMPLES ===
        
        # Example 1: Check if device is moving significantly
        if speed is not None and speed > 1.0:  # > 1 m/s = 3.6 km/h
            print(f"🚶 Device is MOVING")
        else:
            print(f"🏠 Device is STATIONARY")
        
        # Example 2: Check location quality
        if accuracy is not None:
            if accuracy < 20:
                quality = "Excellent"
            elif accuracy < 50:
                quality = "Good"
            elif accuracy < 100:
                quality = "Fair"
            else:
                quality = "Poor"
            print(f"Location Quality: {quality}")
        
        # Example 3: Generate Google Maps link
        maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
        print(f"Map Link: {maps_url}")
        
        print()  # Blank line between locations
    
    # 4. Advanced: Filter locations by criteria
    print("\n--- Advanced: Finding High-Speed Locations ---")
    all_locations = await api.get_all_locations(num_to_get=20)
    
    high_speed_count = 0
    for blob in all_locations:
        try:
            decrypted = api.decrypt_data_blob(blob)
            loc = json.loads(decrypted)
            speed = loc.get('speed')
            
            if speed is not None and speed > 5.0:  # > 18 km/h (biking/driving)
                high_speed_count += 1
                speed_kmh = speed * 3.6
                print(f"  {loc['time']}: {speed_kmh:.1f} km/h")
        except Exception as e:
            print(f"  Skipped invalid location: {e}")
    
    print(f"\nFound {high_speed_count} high-speed location(s) out of {len(all_locations)} total")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
