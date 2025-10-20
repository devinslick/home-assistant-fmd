# FMD API Location Fields Reference

Quick reference for application developers using `fmd_api.py` to work with location data.

## Basic Usage

```python
import asyncio
import json
from fmd_api import FmdApi

async def main():
    api = await FmdApi.create('https://fmd.example.com', 'device-id', 'password')
    blobs = await api.get_all_locations(10)
    
    for blob in blobs:
        location = json.loads(api.decrypt_data_blob(blob))
        # Use location fields here (see below)

asyncio.run(main())
```

## Location Data Fields

### Always Present

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `time` | `str` | Human-readable timestamp | `"Sat Oct 18 14:08:20 CDT 2025"` |
| `date` | `int` | Unix timestamp (milliseconds) | `1760814500242` |
| `provider` | `str` | Location provider | `"gps"`, `"network"`, `"fused"`, `"BeaconDB"` |
| `bat` | `int` | Battery percentage | `78` (= 78%) |
| `lat` | `float` | Latitude | `32.8429147` |
| `lon` | `float` | Longitude | `-97.0714002` |

### Optional (GPS/Movement-Dependent)

| Field | Type | Description | Present When | Example |
|-------|------|-------------|--------------|---------|
| `accuracy` | `float` | GPS accuracy radius (meters) | GPS provider used | `13.793` |
| `altitude` | `float` | Altitude above sea level (meters) | GPS provider used | `150.3` |
| `speed` | `float` | Speed (meters/second) | Device is moving | `2.68` (= 9.6 km/h) |
| `heading` | `float` | Direction (degrees, 0-360) | Device moving with direction | `77.9` (= ENE) |

## Code Examples

### Example 1: Safe Field Access

```python
# Always-present fields - use direct access
latitude = location['lat']
longitude = location['lon']
battery = location['bat']

# Optional fields - use .get() to avoid KeyError
accuracy = location.get('accuracy')      # Returns None if not present
altitude = location.get('altitude')      # Returns None if not present
speed = location.get('speed')            # Returns None if not present
heading = location.get('heading')        # Returns None if not present
```

### Example 2: Check if Device is Moving

```python
speed = location.get('speed')
if speed is not None and speed > 1.0:  # > 1 m/s = 3.6 km/h
    print(f"Device is moving at {speed * 3.6:.1f} km/h")
else:
    print("Device is stationary")
```

### Example 3: Convert Speed to Different Units

```python
speed_ms = location.get('speed')
if speed_ms:
    speed_kmh = speed_ms * 3.6        # kilometers/hour
    speed_mph = speed_ms * 2.237      # miles/hour
    speed_knots = speed_ms * 1.944    # knots
    print(f"Speed: {speed_kmh:.1f} km/h ({speed_mph:.1f} mph)")
```

### Example 4: Convert Heading to Compass Direction

```python
heading = location.get('heading')
if heading is not None:
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                 "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((heading + 11.25) / 22.5) % 16
    compass = directions[idx]
    print(f"Heading: {heading:.1f}° ({compass})")
```

### Example 5: Check Location Quality

```python
accuracy = location.get('accuracy')
if accuracy is not None:
    if accuracy < 20:
        quality = "Excellent (< 20m)"
    elif accuracy < 50:
        quality = "Good (< 50m)"
    elif accuracy < 100:
        quality = "Fair (< 100m)"
    else:
        quality = f"Poor ({accuracy:.0f}m)"
    print(f"GPS Quality: {quality}")
```

### Example 6: Generate Map Links

```python
lat = location['lat']
lon = location['lon']

# Google Maps
google_url = f"https://www.google.com/maps?q={lat},{lon}"

# OpenStreetMap
osm_url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=16"

# Apple Maps
apple_url = f"https://maps.apple.com/?ll={lat},{lon}"
```

### Example 7: Filter High-Speed Locations

```python
# Find all locations where device was traveling > 50 km/h (13.9 m/s)
high_speed_locations = []
for blob in await api.get_all_locations():
    location = json.loads(api.decrypt_data_blob(blob))
    speed = location.get('speed')
    if speed and speed > 13.9:
        high_speed_locations.append(location)

print(f"Found {len(high_speed_locations)} high-speed locations")
```

## Common Pitfalls

### ❌ Don't Do This (will crash if field missing):
```python
heading = location['heading']  # KeyError if not present!
```

### ✅ Do This Instead:
```python
heading = location.get('heading')  # Returns None if not present
if heading is not None:
    # Safe to use heading here
    print(f"Heading: {heading}°")
```

### ❌ Don't Assume All Locations Have Speed:
```python
if location['speed'] > 5:  # KeyError if stationary!
    print("Fast!")
```

### ✅ Check if Speed Exists First:
```python
speed = location.get('speed')
if speed and speed > 5:
    print("Fast!")
```

## Provider Characteristics

Different providers include different optional fields:

| Provider | Accuracy | Altitude | Speed | Heading |
|----------|----------|----------|-------|---------|
| `gps` | ✅ Yes | ✅ Yes | ✅ If moving | ✅ If moving |
| `fused` | ✅ Yes | ✅ Yes | ⚠️ Sometimes | ⚠️ Sometimes |
| `network` | ✅ Yes | ⚠️ Sometimes | ❌ Rare | ❌ Rare |
| `BeaconDB` | ✅ Yes | ❌ No | ❌ No | ❌ No |

## Complete Working Example

See `debugging/example_location_fields.py` for a complete, runnable example demonstrating all location field usage patterns.
