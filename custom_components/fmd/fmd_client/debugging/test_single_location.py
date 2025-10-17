"""
Test script to debug a single location request and see the raw HTTP response.
"""
import argparse
import asyncio
import sys
import os
import logging
import aiohttp

# Add parent directory to path to import fmd_api
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fmd_api import FmdApi

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

async def test_raw_request(base_url, token, index):
    """Make a raw request to see exactly what the server returns."""
    url = f"{base_url}/api/v1/location"
    payload = {"IDT": token, "Data": str(index)}
    
    print(f"\n=== RAW HTTP REQUEST ===")
    print(f"URL: {url}")
    print(f"Method: PUT")
    print(f"Payload: {payload}")
    
    async with aiohttp.ClientSession() as session:
        async with session.put(url, json=payload) as resp:
            print(f"\n=== RAW HTTP RESPONSE ===")
            print(f"Status: {resp.status}")
            print(f"Headers: {dict(resp.headers)}")
            print(f"Content-Type: {resp.content_type}")
            print(f"Content-Length: {resp.content_length}")
            
            # Try reading as bytes
            raw_bytes = await resp.read()
            print(f"\nRaw bytes length: {len(raw_bytes)}")
            print(f"Raw bytes: {raw_bytes}")
            
            # Try reading as text (need to re-fetch)
    
    async with aiohttp.ClientSession() as session:
        async with session.put(url, json=payload) as resp:
            text = await resp.text()
            print(f"\nText length: {len(text)}")
            print(f"Text repr: {repr(text)}")
            
            return text

async def main():
    parser = argparse.ArgumentParser(description="Test single location fetch")
    parser.add_argument('--url', required=True, help='Base URL of the FMD server')
    parser.add_argument('--id', required=True, help='FMD ID (username)')
    parser.add_argument('--password', required=True, help='Password')
    parser.add_argument('--index', type=int, default=0, help='Location index to fetch (default: 0)')
    parser.add_argument('--test-range', action='store_true', help='Test multiple indices to find valid data')
    args = parser.parse_args()

    print("\n=== Authenticating ===")
    api = await FmdApi.create(args.url, args.id, args.password)
    
    print(f"\n=== Getting location count ===")
    size_str = await api._make_api_request("PUT", "/api/v1/locationDataSize", {"IDT": api.access_token, "Data": "unused"})
    size = int(size_str)
    print(f"Server reports {size} locations available")
    
    # Test raw request first to see actual server response
    print(f"\n=== Testing raw HTTP request ===")
    raw_blob = await test_raw_request(args.url.rstrip('/'), api.access_token, args.index)
    print(f"Raw response type: {type(raw_blob)}, length: {len(raw_blob) if raw_blob else 0}")
    
    # Now test using the actual API method
    print(f"\n=== Testing via FmdApi._make_api_request ===")
    blob = await api._make_api_request("PUT", "/api/v1/location", 
                                       {"IDT": api.access_token, "Data": str(args.index)},
                                       expect_json=True)
    
    print(f"\n=== Results ===")
    print(f"Blob type: {type(blob)}")
    print(f"Blob length: {len(blob) if blob else 0}")
    print(f"Blob repr: {repr(blob[:100] if blob else blob)}")
    
    if blob and len(blob) > 0:
        print(f"\n=== Attempting to decrypt ===")
        try:
            decrypted = api.decrypt_data_blob(blob)
            print(f"Decrypted successfully!")
            print(f"Decrypted data: {decrypted}")
        except Exception as e:
            print(f"Decryption failed: {e}")
    else:
        print("\nBlob is empty - cannot decrypt")

if __name__ == "__main__":
    asyncio.run(main())
