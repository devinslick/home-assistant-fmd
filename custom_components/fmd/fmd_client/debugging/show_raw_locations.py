#!/usr/bin/env python3
"""Quick script to dump raw location JSON to see all available fields"""
import sys
sys.path.insert(0, '..')
import asyncio
import json
import argparse
from fmd_api import FmdApi

async def main(url, device_id, password):
    api = await FmdApi.create(url, device_id, password)
    
    print("Fetching 20 most recent locations...")
    locs = await api.get_all_locations(20)
    
    print(f"\nFound {len(locs)} locations. Showing first 5:\n")
    
    for i, loc_blob in enumerate(locs[:5]):
        try:
            decrypted = api.decrypt_data_blob(loc_blob)
            loc_json = json.loads(decrypted)
            print(f"Location {i+1}:")
            print(json.dumps(loc_json, indent=2))
            print()
        except Exception as e:
            print(f"Location {i+1}: Error - {e}\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Show raw location JSON')
    parser.add_argument('--url', required=True, help='FMD server URL')
    parser.add_argument('--id', required=True, help='Device ID')
    parser.add_argument('--password', required=True, help='Device password')
    args = parser.parse_args()
    
    asyncio.run(main(args.url, args.id, args.password))
