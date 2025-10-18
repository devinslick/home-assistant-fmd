#!/usr/bin/env python3
"""Quick script to dump raw location JSON to see all available fields"""
import sys
sys.path.insert(0, '..')
import asyncio
import json
from fmd_api import FmdApi

async def main():
    api = await FmdApi.create(
        'https://fmd.devinslick.com',
        'devinslick-p9',
        'cCBWpONsZblamq403YGG0pySbWu'
    )
    
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
    asyncio.run(main())
