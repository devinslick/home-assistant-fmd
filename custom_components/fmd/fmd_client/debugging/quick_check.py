#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '..')
from fmd_api import FmdApi
import json
import argparse
from datetime import datetime

async def check(url, device_id, password):
    api = await FmdApi.create(url, device_id, password)
    locs = await api.get_all_locations(3)
    
    print("Last 3 locations:")
    for i, loc_blob in enumerate(locs):
        loc = json.loads(api.decrypt_data_blob(loc_blob))
        dt = datetime.fromtimestamp(loc['date']/1000)
        age = (datetime.now() - dt).total_seconds()
        print(f"{i+1}. {dt.strftime('%Y-%m-%d %H:%M:%S')} ({age:.0f}s ago) - {loc.get('provider')} - {loc.get('accuracy', 'N/A')} m")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Quick check of recent locations')
    parser.add_argument('--url', required=True, help='FMD server URL')
    parser.add_argument('--id', required=True, help='Device ID')
    parser.add_argument('--password', required=True, help='Device password')
    args = parser.parse_args()
    
    asyncio.run(check(args.url, args.id, args.password))
