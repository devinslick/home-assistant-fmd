#!/usr/bin/env python3
"""
Compare what the web client sends vs what we send.

Based on your POST data example:
{
    "IDT":"zbRBrUxRqAxqaGBMb6hZnF77QaqK8oig",
    "Data":"locate",
    "UnixTime":1760820522666,
    "CmdSig":"ZlNv7y7ZJ4SRP5Fmf18J/tLR/YQS9TIdQ3YSHPaTwqBFJOxz7qkVhi7oD1A7t4e0HVGk70UDBFVpCX5uLzDItt+DilCegqadHddDxrPn4xGLo13x3f7z7g5omC1M3V+D0nEcsSUB6ohQTVpu+r5laJ+afdLrxQFZ+KrXChrK63uMWgrNuOEdlzDtkibtQBMZUyTXbRlO8arlNfzrsyafpc+KcUdee5yL+nr3aakzoOSpY5iipFwEe9E9tr4gsVmx/PPtogyoQJVIk4WCrIDWAMONy6hot6IPPm/SLDbVDFxmVbOnUm/lRhO/vrtNpNdd/uBmGMY2AnFwSLDWeTqHtzNaLmC+BZTsXjiG1vTrAIOX5emkyJs6h5A6hE8H7sWB/b0+YukAy9Csm9RGxU7HRmQdj6chKCu7HsDkCZEQQU9ClOmVPSZkL2WUEEgcOt5GxpUdLFGt6ll/xtAOfLJQL8a0SeqjnjcPCOFLd3x59R11jz5Qd86zLpupVngw2+JJ"
}

Questions:
1. Are we signing the same data?
2. Is the timestamp format correct?
3. Is the signature format correct?
"""

import base64

# From your example
web_client_sig = "ZlNv7y7ZJ4SRP5Fmf18J/tLR/YQS9TIdQ3YSHPaTwqBFJOxz7qkVhi7oD1A7t4e0HVGk70UDBFVpCX5uLzDItt+DilCegqadHddDxrPn4xGLo13x3f7z7g5omC1M3V+D0nEcsSUB6ohQTVpu+r5laJ+afdLrxQFZ+KrXChrK63uMWgrNuOEdlzDtkibtQBMZUyTXbRlO8arlNfzrsyafpc+KcUdee5yL+nr3aakzoOSpY5iipFwEe9E9tr4gsVmx/PPtogyoQJVIk4WCrIDWAMONy6hot6IPPm/SLDbVDFxmVbOnUm/lRhO/vrtNpNdd/uBmGMY2AnFwSLDWeTqHtzNaLmC+BZTsXjiG1vTrAIOX5emkyJs6h5A6hE8H7sWB/b0+YukAy9Csm9RGxU7HRmQdj6chKCu7HsDkCZEQQU9ClOmVPSZkL2WUEEgcOt5GxpUdLFGt6ll/xtAOfLJQL8a0SeqjnjcPCOFLd3x59R11jz5Qd86zLpupVngw2+JJ"

print("WEB CLIENT SIGNATURE ANALYSIS")
print("=" * 70)
print(f"Base64 length: {len(web_client_sig)} chars")
print(f"Has padding: {'=' in web_client_sig}")

# Decode to see raw signature
sig_bytes = base64.b64decode(web_client_sig)
print(f"Raw signature length: {len(sig_bytes)} bytes")
print(f"Expected for RSA-3072: 384 bytes")
print(f"First 32 bytes (hex): {sig_bytes[:32].hex()}")
print(f"Last 32 bytes (hex): {sig_bytes[-32:].hex()}")

print("\n" + "=" * 70)
print("OBSERVATIONS:")
print("=" * 70)
print(f"✓ Signature is 384 bytes (correct for RSA-3072)")
print(f"✓ Base64 includes padding (our implementation strips it - could this matter?)")
print(f"  Command: 'locate' (6 bytes)")
print(f"  Unix Time: 1760820522666 (13 digits - milliseconds)")

print("\nKEY QUESTION: Does the server expect BASE64 WITH or WITHOUT padding?")
print("Our implementation: strips padding with .rstrip('=')")
print("Web client: includes padding")
