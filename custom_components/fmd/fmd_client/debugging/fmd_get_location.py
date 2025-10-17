"""
FMD Server End-to-End Location Retriever

This script automates the full workflow:
- Authenticates with the FMD server using username and password
- Retrieves the encrypted private key and decrypts it
- Retrieves the latest location data and decrypts it
- Prints the decrypted location as JSON

Usage:
    python fmd_get_location.py --url <server_url> --id <fmd_id> --password <password>

Dependencies:
    pip install aiohttp argon2-cffi cryptography
"""
import argparse
import asyncio
import json
import sys
import os

# Add parent directory to path to import fmd_api
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fmd_api import FmdApi

async def main():
    parser = argparse.ArgumentParser(description="FMD Server End-to-End Location Retriever")
    parser.add_argument('--url', required=True, help='Base URL of the FMD server (e.g. https://fmd.example.com)')
    parser.add_argument('--id', required=True, help='FMD ID (username)')
    parser.add_argument('--password', required=True, help='Password')
    parser.add_argument('--session', type=int, default=3600, help='Session duration in seconds (default: 3600)')
    parser.add_argument('--num', type=int, default=1, help='Number of locations to fetch (default: 1)')
    args = parser.parse_args()

    print("[1-3] Authenticating and retrieving keys...")
    api = await FmdApi.create(args.url, args.id, args.password, args.session)

    print(f"[4] Downloading {args.num} latest location(s)...")
    location_blobs = await api.get_all_locations(num_to_get=args.num, skip_empty=True)

    if not location_blobs:
        print("No location data found!")
        sys.exit(0)

    print(f"\n[5] Found {len(location_blobs)} location(s). Decrypting...")
    for idx, blob in enumerate(location_blobs):
        try:
            plaintext = api.decrypt_data_blob(blob)
            location_data = json.loads(plaintext)
            print(f"\nLocation {idx + 1}:")
            print(json.dumps(location_data, indent=2))
        except Exception as e:
            print(f"Failed to decrypt location {idx + 1}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
