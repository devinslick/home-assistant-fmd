#!/usr/bin/env python3
"""Quick test script for sending ring command to FMD device."""
import asyncio
import sys
import argparse
sys.path.insert(0, '..')
from fmd_api import FmdApi

async def send_ring(url, device_id, password):
    print("Authenticating...")
    api = await FmdApi.create(url, device_id, password)
    print("✓ Authenticated")
    
    print("\nSending 'ring' command to device...")
    result = await api.send_command('ring')
    
    if result:
        print("✓ Ring command sent successfully!")
        print("\n🔔 Your device should start ringing now!")
        print("   (The ring will continue until you dismiss it on the device)")
    else:
        print("✗ Failed to send ring command")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send ring command to FMD device')
    parser.add_argument('--url', required=True, help='FMD server URL')
    parser.add_argument('--id', required=True, help='Device ID')
    parser.add_argument('--password', required=True, help='Device password')
    args = parser.parse_args()
    
    asyncio.run(send_ring(args.url, args.id, args.password))
