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
    pip install requests argon2-cffi cryptography
"""
import argparse
import json
import sys
from fmd_api import FmdApi

def main():
    parser = argparse.ArgumentParser(description="FMD Server End-to-End Location Retriever")
    parser.add_argument('--url', required=True, help='Base URL of the FMD server (e.g. https://fmd.example.com)')
    parser.add_argument('--id', required=True, help='FMD ID (username)')
    parser.add_argument('--password', required=True, help='Password')
    parser.add_argument('--session', type=int, default=3600, help='Session duration in seconds (default: 3600)')
    args = parser.parse_args()

    api = FmdApi(args.url, args.id, args.password, args.session)

    print("[4] Downloading latest location...")
    location_blobs = api.get_all_locations(num_to_get=1)

    if not location_blobs:
        sys.exit(0)

    print("[5] Decrypting location data...")
    plaintext = api.decrypt_data_blob(location_blobs[0])

    print("\nDecrypted Location Data:")
    # Pretty-print the JSON
    print(json.dumps(json.loads(plaintext), indent=2))

if __name__ == "__main__":
    main()
