#!/usr/bin/env python3
"""
Diagnostic script to test command signing and compare with web client.

This script will:
1. Show the exact payload being sent
2. Compare signature format with what the web client sends
3. Test if the server accepts the command
4. Check command logs (if available)
"""

import asyncio
import argparse
import json
import sys
import logging
import time
import base64
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fmd_api import FmdApi, FmdApiException
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


async def test_command_signing(url: str, device_id: str, password: str):
    """Test command signing in detail."""
    
    print("=" * 70)
    print("COMMAND SIGNING DIAGNOSTIC")
    print("=" * 70)
    
    # Authenticate
    print("\n[1] Authenticating...")
    api = await FmdApi.create(url, device_id, password)
    print("✓ Authenticated successfully")
    
    # Get private key info
    print(f"\n[2] Private Key Info:")
    print(f"    Type: {type(api.private_key).__name__}")
    print(f"    Key Size: {api.private_key.key_size} bits ({api.private_key.key_size // 8} bytes)")
    
    # Test command
    command = "locate gps"
    print(f"\n[3] Command to send: '{command}'")
    
    # Generate timestamp
    unix_time_ms = int(time.time() * 1000)
    print(f"    Unix Time (ms): {unix_time_ms}")
    
    # Sign the command
    command_bytes = command.encode('utf-8')
    print(f"    Command bytes: {command_bytes.hex()}")
    print(f"    Command length: {len(command_bytes)} bytes")
    
    signature = api.private_key.sign(
        command_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=32
        ),
        hashes.SHA256()
    )
    print(f"\n[4] Signature Generated:")
    print(f"    Raw signature length: {len(signature)} bytes")
    print(f"    First 32 bytes (hex): {signature[:32].hex()}")
    print(f"    Last 32 bytes (hex): {signature[-32:].hex()}")
    
    # Base64 encode
    signature_b64 = base64.b64encode(signature).decode('utf-8').rstrip('=')
    print(f"    Base64 (no padding): {signature_b64[:50]}...{signature_b64[-50:]}")
    print(f"    Base64 length: {len(signature_b64)} chars")
    
    # Show full payload
    payload = {
        "IDT": api.access_token,
        "Data": command,
        "UnixTime": unix_time_ms,
        "CmdSig": signature_b64
    }
    
    print(f"\n[5] Full Payload:")
    print(f"    IDT: {api.access_token[:20]}...{api.access_token[-20:]}")
    print(f"    Data: {command}")
    print(f"    UnixTime: {unix_time_ms}")
    print(f"    CmdSig: {signature_b64[:50]}...{signature_b64[-20:]}")
    
    # Try to send the command
    print(f"\n[6] Sending command to server...")
    try:
        result = await api._make_api_request(
            "POST",
            "/api/v1/command",
            payload,
            expect_json=False
        )
        print(f"✓ Server Response:")
        print(f"    Status: SUCCESS")
        print(f"    Response: {repr(result)}")
        print(f"    Response type: {type(result)}")
        print(f"    Response length: {len(result) if result else 0}")
    except Exception as e:
        print(f"✗ Command FAILED:")
        print(f"    Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Wait a moment and check for new location
    print(f"\n[7] Waiting 10 seconds to check location count...")
    await asyncio.sleep(10)
    
    size_str = await api._make_api_request("PUT", "/api/v1/locationDataSize", 
                                           {"IDT": api.access_token, "Data": "unused"})
    size = int(size_str)
    print(f"    Current location count: {size}")
    
    # Try to get the most recent location
    print(f"\n[8] Fetching most recent location...")
    locations = await api.get_all_locations(1)
    if locations and locations[0]:
        decrypted = api.decrypt_data_blob(locations[0])
        location = json.loads(decrypted)
        from datetime import datetime
        loc_time = datetime.fromtimestamp(location['date'] / 1000)
        now = datetime.now()
        age_seconds = (now - loc_time).total_seconds()
        print(f"    Location timestamp: {loc_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    Age: {age_seconds:.0f} seconds old")
        print(f"    Provider: {location.get('provider', 'unknown')}")
        
        if age_seconds < 15:
            print(f"    ✓ Location is RECENT - command may have worked!")
        else:
            print(f"    ✗ Location is OLD - command may not have reached device")
    
    # Try to check command logs (if endpoint exists)
    print(f"\n[9] Attempting to check command logs...")
    try:
        logs = await api._make_api_request("PUT", "/api/v1/commandLogs", 
                                          {"IDT": api.access_token, "Data": ""})
        print(f"    Command logs available!")
        print(f"    Logs: {logs}")
    except Exception as e:
        print(f"    Command logs not available or encrypted: {e}")
    
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Test command signing in detail')
    parser.add_argument('--url', required=True, help='FMD server URL')
    parser.add_argument('--id', required=True, help='Device ID')
    parser.add_argument('--password', required=True, help='Device password')
    
    args = parser.parse_args()
    
    asyncio.run(test_command_signing(args.url, args.id, args.password))


if __name__ == '__main__':
    main()
