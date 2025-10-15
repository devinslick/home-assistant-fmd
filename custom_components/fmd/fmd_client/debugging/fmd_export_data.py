"""
FMD Server Export Data Script

This script authenticates with the FMD server and downloads the exported data as a zip file using the 'export data' function.

Usage:
    python fmd_export_data.py --url <server_url> --id <fmd_id> --password <password> --output <output.zip>

Dependencies:
    pip install requests argon2-cffi cryptography
"""
import argparse
from fmd_api import FmdApi

def main():
    parser = argparse.ArgumentParser(description="FMD Server Export Data Script")
    parser.add_argument('--url', required=True, help='Base URL of the FMD server (e.g. https://fmd.example.com)')
    parser.add_argument('--id', required=True, help='FMD ID (username)')
    parser.add_argument('--password', required=True, help='Password')
    parser.add_argument('--output', required=True, help='Output zip file path')
    parser.add_argument('--session', type=int, default=3600, help='Session duration in seconds (default: 3600)')
    args = parser.parse_args()

    base_url = args.url.rstrip('/')
    fmd_id = args.id
    password = args.password
    session_duration = args.session
    output_file = args.output

    # Authenticate to get a valid session and access token
    api = FmdApi(base_url, fmd_id, password, session_duration)

    print("[4] Downloading exported data...")
    api.export_data_zip(output_file)

if __name__ == "__main__":
    main()
