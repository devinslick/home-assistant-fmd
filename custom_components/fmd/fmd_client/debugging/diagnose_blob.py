"""
Diagnostic script to examine the structure of encrypted location blobs.
This will help identify if the blob format has changed.
"""
import argparse
import base64
import sys
sys.path.insert(0, '..')
from fmd_api import FmdApi, _pad_base64

def main():
    parser = argparse.ArgumentParser(description="FMD Blob Structure Diagnostic")
    parser.add_argument('--url', required=True, help='Base URL of the FMD server')
    parser.add_argument('--id', required=True, help='FMD ID (username)')
    parser.add_argument('--password', required=True, help='Password')
    args = parser.parse_args()

    print("[*] Authenticating...")
    api = FmdApi(args.url, args.id, args.password)
    
    print("[*] Retrieving private key info...")
    # Check the private key size
    from cryptography.hazmat.primitives import serialization
    private_pem = api.private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    print(f"    Private key type: {type(api.private_key).__name__}")
    print(f"    Private key size: {api.private_key.key_size} bits ({api.private_key.key_size // 8} bytes)")
    
    print("\n[*] Downloading one location blob...")
    location_blobs = api.get_all_locations(num_to_get=1)
    
    if not location_blobs:
        print("No locations available!")
        return
    
    blob_b64 = location_blobs[0]
    print(f"\n[*] Blob analysis:")
    print(f"    Base64 length: {len(blob_b64)} characters")
    
    # Decode the blob
    blob = base64.b64decode(_pad_base64(blob_b64))
    print(f"    Raw blob length: {len(blob)} bytes")
    
    # Expected structure based on current code
    RSA_KEY_SIZE_BYTES = 384  # 3072 bits / 8
    AES_GCM_IV_SIZE_BYTES = 12
    
    print(f"\n[*] Expected structure (current code):")
    print(f"    RSA session key packet: {RSA_KEY_SIZE_BYTES} bytes (0-{RSA_KEY_SIZE_BYTES-1})")
    print(f"    AES-GCM IV: {AES_GCM_IV_SIZE_BYTES} bytes ({RSA_KEY_SIZE_BYTES}-{RSA_KEY_SIZE_BYTES+AES_GCM_IV_SIZE_BYTES-1})")
    print(f"    Ciphertext: {len(blob) - RSA_KEY_SIZE_BYTES - AES_GCM_IV_SIZE_BYTES} bytes (remaining)")
    
    # Try different RSA key sizes
    possible_sizes = [256, 384, 512]  # 2048-bit, 3072-bit, 4096-bit
    print(f"\n[*] Testing possible RSA key sizes:")
    for size in possible_sizes:
        remaining = len(blob) - size - AES_GCM_IV_SIZE_BYTES
        print(f"    {size} bytes ({size*8} bits): IV at {size}-{size+AES_GCM_IV_SIZE_BYTES-1}, ciphertext {remaining} bytes")
        if remaining > 0 and remaining < 500:  # Location JSON is typically small
            print(f"      ^ This looks plausible for location data!")
    
    # Show first few bytes in hex
    print(f"\n[*] First 32 bytes (hex): {blob[:32].hex()}")
    print(f"[*] Last 32 bytes (hex): {blob[-32:].hex()}")

if __name__ == "__main__":
    main()
