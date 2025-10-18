"""
FMD Server Client

This is the main client script for interacting with the FMD server.
It can export locations and pictures to a local directory or zip file.

Usage:
    python fmd_client.py --url <server_url> --id <fmd_id> --password <password> --output <output_path> [--locations [N]] [--pictures [N]]

Dependencies:
    pip install aiohttp argon2-cffi cryptography
"""
import argparse
import asyncio
import base64
import sys
import os
import zipfile
import json
from fmd_api import FmdApi, _pad_base64

def save_locations_csv(api, location_blobs, out_path):
    header = "Date,Provider,Battery %,Latitude,Longitude,Accuracy (m),Altitude (m),Speed (m/s),Heading (°)\n"
    lines = [header]
    skipped_count = 0
    for idx, location_blob in enumerate(location_blobs):
        loc = None
        try:            
            decrypted_bytes = api.decrypt_data_blob(location_blob)
            loc = json.loads(decrypted_bytes)
        except Exception as e:
            skipped_count += 1
            print(f"Warning: Skipping location {idx} - {e}")
            continue

        if not loc:
            continue

        date = loc.get('time', 'N/A')
        provider = loc.get('provider', 'N/A')
        bat = loc.get('bat', 'N/A')
        lat = loc.get('lat', 'N/A')
        lon = loc.get('lon', 'N/A')
        accuracy = loc.get('accuracy', 'N/A')
        altitude = loc.get('altitude', 'N/A')
        speed = loc.get('speed', 'N/A')
        heading = loc.get('heading', 'N/A')  # Changed from 'bearing' to 'heading'
        lines.append(f"{date},{provider},{bat},{lat},{lon},{accuracy},{altitude},{speed},{heading}\n")
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    if skipped_count > 0:
        print(f"Note: Skipped {skipped_count} invalid/empty location(s) out of {len(location_blobs)} total")

def save_pictures(api, picture_blobs, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    skipped_count = 0
    for idx, pic_blob in enumerate(picture_blobs):
        try:
            if pic_blob:
                decrypted_payload_bytes = api.decrypt_data_blob(pic_blob)
                # The decrypted payload is likely a base64 string, possibly with a data URI prefix.
                decrypted_text = decrypted_payload_bytes.decode('utf-8')
                base64_data = decrypted_text.split(',')[-1]
                image_bytes = base64.b64decode(_pad_base64(base64_data))
                with open(os.path.join(out_dir, f"{idx}.png"), 'wb') as f:
                    f.write(image_bytes)
        except Exception as e:
            skipped_count += 1
            print(f"Warning: Skipping picture {idx} - {e}")
    
    if skipped_count > 0:
        print(f"Note: Skipped {skipped_count} invalid/empty picture(s) out of {len(picture_blobs)} total")

async def main():
    parser = argparse.ArgumentParser(description="FMD Server Client")
    parser.add_argument('--url', required=True, help='Base URL of the FMD server (e.g. https://fmd.example.com)')
    parser.add_argument('--id', required=True, help='FMD ID (username)')
    parser.add_argument('--password', required=True, help='Password')
    parser.add_argument('--output', required=True, help='Output .zip file or directory')
    parser.add_argument('--locations', nargs='?', const=-1, default=None, type=int, help='Include all locations, or specify a number for the most recent N locations.')
    parser.add_argument('--pictures', nargs='?', const=-1, default=None, type=int, help='Include all pictures, or specify a number for the most recent N pictures.')
    parser.add_argument('--session', type=int, default=3600, help='Session duration in seconds (default: 3600)')
    args = parser.parse_args()

    base_url = args.url.rstrip('/')
    fmd_id = args.id
    password = args.password
    session_duration = args.session
    output_path = args.output
    num_locations_to_get = args.locations
    num_pictures_to_get = args.pictures

    if num_locations_to_get is None and num_pictures_to_get is None:
        print("Nothing to export: specify --locations and/or --pictures")
        sys.exit(1)

    print("[1-3] Authenticating and retrieving keys...")
    api = await FmdApi.create(base_url, fmd_id, password, session_duration)

    locations_json = None
    pictures_json = None
    if num_locations_to_get is not None:
        print("[4] Downloading locations...")
        locations_json = await api.get_all_locations(num_locations_to_get)
    if num_pictures_to_get is not None:
        print("[5] Downloading pictures...")
        pictures_json = await api.get_pictures(num_pictures_to_get)

    is_zip = output_path.lower().endswith('.zip')
    if is_zip:
        print(f"[6] Writing to zip: {output_path}")
        skipped_locations = 0
        skipped_pictures = 0
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if num_locations_to_get is not None and locations_json is not None:
                import io
                csv_buf = io.StringIO()
                header = "Date,Provider,Battery %,Latitude,Longitude,Accuracy (m),Altitude (m),Speed (m/s),Heading (°)\n"
                csv_buf.write(header)
                location_list = locations_json
                for idx, location_blob in enumerate(location_list):
                    if not location_blob: continue
                    loc = None
                    try:
                        decrypted_bytes = api.decrypt_data_blob(location_blob)
                        loc = json.loads(decrypted_bytes)
                    except Exception as e:
                        skipped_locations += 1
                        print(f"Warning: Skipping location {idx} for zip - {e}")
                        continue

                    if not loc:
                        continue
                    date = loc.get('time', 'N/A')
                    provider = loc.get('provider', 'N/A')
                    bat = loc.get('bat', 'N/A')
                    lat = loc.get('lat', 'N/A')
                    lon = loc.get('lon', 'N/A')
                    accuracy = loc.get('accuracy', 'N/A')
                    altitude = loc.get('altitude', 'N/A')
                    speed = loc.get('speed', 'N/A')
                    heading = loc.get('heading', 'N/A')  # Changed from 'bearing' to 'heading'
                    csv_buf.write(f"{date},{provider},{bat},{lat},{lon},{accuracy},{altitude},{speed},{heading}\n")
                zf.writestr('locations.csv', csv_buf.getvalue())
                if skipped_locations > 0:
                    print(f"Note: Skipped {skipped_locations} invalid/empty location(s) in zip")
            if num_pictures_to_get is not None and pictures_json is not None:
                picture_list = pictures_json
                for idx, pic_blob in enumerate(picture_list):
                    if pic_blob:
                        try:
                            decrypted_payload_bytes = api.decrypt_data_blob(pic_blob)
                            decrypted_text = decrypted_payload_bytes.decode('utf-8')
                            base64_data = decrypted_text.split(',')[-1]
                            image_bytes = base64.b64decode(_pad_base64(base64_data))
                            zf.writestr(f'pictures/{idx}.png', image_bytes)
                        except Exception as e:
                            skipped_pictures += 1
                            print(f"Warning: Skipping picture {idx} for zip - {e}")
                if skipped_pictures > 0:
                    print(f"Note: Skipped {skipped_pictures} invalid/empty picture(s) in zip")
        print(f"Exported data saved to {output_path}")
    else:
        print(f"[6] Writing to directory: {output_path}")
        os.makedirs(output_path, exist_ok=True)
        if num_locations_to_get is not None and locations_json is not None:
            save_locations_csv(api, locations_json, os.path.join(output_path, 'locations.csv'))
        if num_pictures_to_get is not None and pictures_json is not None:
            save_pictures(api, pictures_json, os.path.join(output_path, 'pictures'))
        print(f"Exported data saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
