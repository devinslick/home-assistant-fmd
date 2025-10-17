"""Quick test of exportData endpoint."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fmd_api import FmdApi

async def main():
    if len(sys.argv) < 4:
        print("Usage: python test_export.py URL ID PASSWORD")
        return
    
    api = await FmdApi.create(sys.argv[1], sys.argv[2], sys.argv[3])
    print("Testing exportData endpoint...")
    try:
        # This might return a large file
        result = await api._make_api_request('POST', '/api/v1/exportData', 
                                             {'IDT': api.access_token, 'Data': 'unused'})
        print(f"Got response, length: {len(result) if result else 0}")
        if result and len(result) > 0:
            print("Export data endpoint WORKS - data is available via this endpoint!")
            print(f"First 200 chars: {result[:200]}")
        else:
            print("Export data endpoint also returns empty")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
