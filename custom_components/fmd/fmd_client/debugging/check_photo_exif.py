"""
Check if FMD photos contain EXIF timestamp metadata.

This script downloads a photo and examines its EXIF data to see
if the original capture timestamp is preserved.

Usage:
    python check_photo_exif.py <fmd_url> <device_id> <password>

Example:
    python check_photo_exif.py https://fmd.example.com my-device-id mypassword
"""
import argparse
import asyncio
import base64
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from fmd_api import FmdApi

async def check_photo_exif(fmd_url: str, device_id: str, password: str):
    """Check if photos have EXIF timestamp data."""
    
    print(f"Connecting to FMD server: {fmd_url}")
    print(f"Device ID: {device_id}")
    
    api = await FmdApi.create(fmd_url, device_id, password)
    
    # Get one photo
    print("\nFetching 1 most recent photo...")
    pictures = await api.get_pictures(num_to_get=1)
    
    if not pictures:
        print("No photos available on server")
        return
    
    print(f"Found {len(pictures)} photo(s)")
    
    # Decrypt the first photo
    blob = pictures[0]
    decrypted = api.decrypt_data_blob(blob)
    image_bytes = base64.b64decode(decrypted)
    
    print(f"\nImage size: {len(image_bytes)} bytes")
    
    # Check for JPEG markers
    if image_bytes[:2] == b'\xff\xd8':
        print("✓ Valid JPEG file detected")
    else:
        print("✗ Not a valid JPEG file")
        return
    
    # Try to read EXIF data
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        import io
        
        img = Image.open(io.BytesIO(image_bytes))
        
        # Get EXIF data
        exif_data = img._getexif()
        
        if exif_data:
            print("\n✓ EXIF data found!")
            print("\nRelevant EXIF tags:")
            
            # Look for timestamp-related tags
            timestamp_tags = {
                'DateTime': 306,
                'DateTimeOriginal': 36867,
                'DateTimeDigitized': 36868,
            }
            
            found_timestamps = False
            for tag_name, tag_id in timestamp_tags.items():
                if tag_id in exif_data:
                    value = exif_data[tag_id]
                    print(f"  {tag_name}: {value}")
                    found_timestamps = True
            
            if not found_timestamps:
                print("  No timestamp tags found in EXIF data")
            
            # Show all EXIF tags for debugging
            print("\nAll EXIF tags:")
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                print(f"  {tag_name} ({tag_id}): {value}")
        else:
            print("\n✗ No EXIF data found in image")
            
    except ImportError:
        print("\n⚠ PIL/Pillow not installed. Install with: pip install pillow")
        print("Cannot check EXIF data without PIL")
    except Exception as e:
        print(f"\n✗ Error reading EXIF data: {e}")
    
    # FmdApi doesn't have a close method, no cleanup needed

def main():
    """Parse command line arguments and run the check."""
    parser = argparse.ArgumentParser(
        description='Check if FMD photos contain EXIF timestamp metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_photo_exif.py https://fmd.example.com my-device-id mypassword
  python check_photo_exif.py https://192.168.1.100:8080 phone-1 secret123
        """
    )
    parser.add_argument('fmd_url', help='FMD server URL (e.g., https://fmd.example.com)')
    parser.add_argument('device_id', help='Device ID registered with FMD server')
    parser.add_argument('password', help='Device password')
    
    args = parser.parse_args()
    
    asyncio.run(check_photo_exif(args.fmd_url, args.device_id, args.password))

if __name__ == "__main__":
    main()
