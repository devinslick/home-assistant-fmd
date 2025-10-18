"""
Core API library for interacting with an FMD server.

This module provides a class that handles authentication, key management,
and data decryption for FMD clients.

Example Usage:
    import asyncio
    import json
    from fmd_api import FmdApi
    
    async def main():
        # Authenticate and create API client
        api = await FmdApi.create(
            'https://fmd.example.com',
            'your-device-id',
            'your-password'
        )
        
        # Get the 10 most recent locations
        location_blobs = await api.get_all_locations(num_to_get=10)
        
        # Decrypt and parse each location
        for blob in location_blobs:
            decrypted_bytes = api.decrypt_data_blob(blob)
            location = json.loads(decrypted_bytes)
            
            # Always-present fields:
            timestamp = location['time']      # Human-readable: "Sat Oct 18 14:08:20 CDT 2025"
            date_ms = location['date']        # Unix timestamp in milliseconds
            provider = location['provider']   # "gps", "network", "fused", or "BeaconDB"
            battery = location['bat']         # Battery percentage (0-100)
            latitude = location['lat']        # Latitude in degrees
            longitude = location['lon']       # Longitude in degrees
            
            # Optional fields (use .get() with default):
            accuracy = location.get('accuracy')   # GPS accuracy in meters (float)
            altitude = location.get('altitude')   # Altitude in meters (float)
            speed = location.get('speed')         # Speed in meters/second (float)
            heading = location.get('heading')     # Direction in degrees 0-360 (float)
            
            # Example: Convert speed to km/h and print if moving
            if speed is not None and speed > 0.5:  # Moving faster than 0.5 m/s
                speed_kmh = speed * 3.6
                direction = heading if heading else "unknown"
                print(f"{timestamp}: Moving at {speed_kmh:.1f} km/h, heading {direction}°")
            else:
                print(f"{timestamp}: Stationary at ({latitude}, {longitude})")
    
    asyncio.run(main())

Location Data Field Reference:
    Always Present:
        - time (str): Human-readable timestamp
        - date (int): Unix timestamp in milliseconds
        - provider (str): Location provider name
        - bat (int): Battery percentage
        - lat (float): Latitude
        - lon (float): Longitude
    
    Optional (GPS/Movement-Dependent):
        - accuracy (float): GPS accuracy radius in meters
        - altitude (float): Altitude above sea level in meters
        - speed (float): Speed in meters per second (only when moving)
        - heading (float): Direction in degrees 0-360 (only when moving with direction)
"""
import base64
import json
import logging
import time
import aiohttp
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- Constants ---
CONTEXT_STRING_LOGIN = "context:loginAuthentication"
CONTEXT_STRING_ASYM_KEY_WRAP = "context:asymmetricKeyWrap"
ARGON2_SALT_LENGTH = 16
AES_GCM_IV_SIZE_BYTES = 12
RSA_KEY_SIZE_BYTES = 384  # 3072 bits / 8

log = logging.getLogger(__name__)

class FmdApiException(Exception):
    """Base exception for FMD API errors."""
    pass

def _pad_base64(s):
    return s + '=' * (-len(s) % 4)

class FmdApi:
    """A client for the FMD server API."""

    def __init__(self, base_url, session_duration=3600):
        self.base_url = base_url.rstrip('/')
        self.access_token = None
        self.private_key = None
        self.session_duration = session_duration
        self._fmd_id = None
        self._password = None

    @classmethod
    async def create(cls, base_url, fmd_id, password, session_duration=3600):
        """Creates and authenticates an FmdApi instance."""
        instance = cls(base_url, session_duration)
        instance._fmd_id = fmd_id
        instance._password = password
        await instance.authenticate(fmd_id, password, session_duration)
        return instance

    async def authenticate(self, fmd_id, password, session_duration):
        """Performs the full authentication and key retrieval workflow."""
        log.info("[1] Requesting salt...")
        salt = await self._get_salt(fmd_id)
        log.info("[2] Hashing password with salt...")
        password_hash = self._hash_password(password, salt)
        log.info("[3] Requesting access token...")
        self.fmd_id = fmd_id
        self.access_token = await self._get_access_token(fmd_id, password_hash, session_duration)
        
        log.info("[3a] Retrieving encrypted private key...")
        privkey_blob = await self._get_private_key_blob()
        log.info("[3b] Decrypting private key...")
        privkey_bytes = self._decrypt_private_key_blob(privkey_blob, password)
        self.private_key = self._load_private_key_from_bytes(privkey_bytes)

    def _hash_password(self, password: str, salt: str) -> str:
        salt_bytes = base64.b64decode(_pad_base64(salt))
        password_bytes = (CONTEXT_STRING_LOGIN + password).encode('utf-8')
        hash_bytes = hash_secret_raw(
            secret=password_bytes, salt=salt_bytes, time_cost=1,
            memory_cost=131072, parallelism=4, hash_len=32, type=Type.ID
        )
        hash_b64 = base64.b64encode(hash_bytes).decode('utf-8').rstrip('=')
        return f"$argon2id$v=19$m=131072,t=1,p=4${salt}${hash_b64}"

    async def _get_salt(self, fmd_id):
        return await self._make_api_request("PUT", "/api/v1/salt", {"IDT": fmd_id, "Data": ""})

    async def _get_access_token(self, fmd_id, password_hash, session_duration):
        payload = {
            "IDT": fmd_id, "Data": password_hash,
            "SessionDurationSeconds": session_duration
        }
        return await self._make_api_request("PUT", "/api/v1/requestAccess", payload)

    async def _get_private_key_blob(self):
        return await self._make_api_request("PUT", "/api/v1/key", {"IDT": self.access_token, "Data": "unused"})

    def _decrypt_private_key_blob(self, key_b64: str, password: str) -> bytes:
        key_bytes = base64.b64decode(_pad_base64(key_b64))
        salt = key_bytes[:ARGON2_SALT_LENGTH]
        iv = key_bytes[ARGON2_SALT_LENGTH:ARGON2_SALT_LENGTH + AES_GCM_IV_SIZE_BYTES]
        ciphertext = key_bytes[ARGON2_SALT_LENGTH + AES_GCM_IV_SIZE_BYTES:]
        password_bytes = (CONTEXT_STRING_ASYM_KEY_WRAP + password).encode('utf-8')
        aes_key = hash_secret_raw(
            secret=password_bytes, salt=salt, time_cost=1, memory_cost=131072,
            parallelism=4, hash_len=32, type=Type.ID
        )
        aesgcm = AESGCM(aes_key)
        return aesgcm.decrypt(iv, ciphertext, None)

    def _load_private_key_from_bytes(self, privkey_bytes: bytes):
        try:
            return serialization.load_pem_private_key(privkey_bytes, password=None)
        except ValueError:
            return serialization.load_der_private_key(privkey_bytes, password=None)

    def decrypt_data_blob(self, data_b64: str) -> bytes:
        """Decrypts a location or picture data blob using the instance's private key.
        
        Args:
            data_b64: Base64-encoded encrypted blob from the server
            
        Returns:
            bytes: Decrypted data (JSON for locations, base64 string for pictures)
            
        Raises:
            FmdApiException: If blob is too small or decryption fails
            
        Example:
            # For locations:
            location_blob = await api.get_all_locations(1)
            decrypted = api.decrypt_data_blob(location_blob[0])
            location = json.loads(decrypted)
            
            # Access fields:
            lat = location['lat']
            lon = location['lon']
            accuracy = location.get('accuracy')  # Optional field
            speed = location.get('speed')        # Optional, only when moving
            heading = location.get('heading')    # Optional, only when moving
        """
        blob = base64.b64decode(_pad_base64(data_b64))
        
        # Check if blob is large enough to contain encrypted data
        min_size = RSA_KEY_SIZE_BYTES + AES_GCM_IV_SIZE_BYTES
        if len(blob) < min_size:
            raise FmdApiException(
                f"Blob too small for decryption: {len(blob)} bytes (expected at least {min_size} bytes). "
                f"This may indicate empty/invalid data from the server."
            )
        
        session_key_packet = blob[:RSA_KEY_SIZE_BYTES]
        iv = blob[RSA_KEY_SIZE_BYTES:RSA_KEY_SIZE_BYTES + AES_GCM_IV_SIZE_BYTES]
        ciphertext = blob[RSA_KEY_SIZE_BYTES + AES_GCM_IV_SIZE_BYTES:]
        session_key = self.private_key.decrypt(
            session_key_packet,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(), label=None
            )
        )
        aesgcm = AESGCM(session_key)
        return aesgcm.decrypt(iv, ciphertext, None)

    async def _make_api_request(self, method, endpoint, payload, stream=False, expect_json=True, retry_auth=True):
        """Helper function for making API requests."""
        url = self.base_url + endpoint
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, json=payload) as resp:
                    # Handle 401 Unauthorized by re-authenticating
                    if resp.status == 401 and retry_auth and self._fmd_id and self._password:
                        log.info("Received 401 Unauthorized, re-authenticating...")
                        await self.authenticate(self._fmd_id, self._password, self.session_duration)
                        # Retry the request with new token
                        payload["IDT"] = self.access_token
                        return await self._make_api_request(method, endpoint, payload, stream, expect_json, retry_auth=False)
                    
                    resp.raise_for_status()
                    
                    # Log response details for debugging
                    log.debug(f"{endpoint} response - status: {resp.status}, content-type: {resp.content_type}, content-length: {resp.content_length}")
                    
                    if not stream:
                        if expect_json:
                            # FMD server sometimes returns wrong content-type (application/octet-stream instead of application/json)
                            # Use content_type=None to force JSON parsing regardless of Content-Type header
                            try:
                                json_data = await resp.json(content_type=None)
                                log.debug(f"{endpoint} JSON response: {json_data}")
                                return json_data["Data"]
                            except (KeyError, ValueError, json.JSONDecodeError) as e:
                                # If JSON parsing fails, fall back to text
                                log.debug(f"{endpoint} JSON parsing failed ({e}), trying as text")
                                text_data = await resp.text()
                                log.debug(f"{endpoint} returned text length: {len(text_data)}")
                                if text_data:
                                    log.debug(f"{endpoint} first 200 chars: {text_data[:200]}")
                                else:
                                    log.warning(f"{endpoint} returned EMPTY response body")
                                return text_data
                        else:
                            text_data = await resp.text()
                            log.debug(f"{endpoint} text response status: {resp.status}, content-type: {resp.content_type}")
                            log.debug(f"{endpoint} text response length: {len(text_data)}, content: {text_data[:500]}")
                            return text_data
                    else:
                        return resp
        except aiohttp.ClientError as e:
            log.error(f"API request failed for {endpoint}: {e}")
            raise FmdApiException(f"API request failed for {endpoint}: {e}") from e
        except (KeyError, ValueError) as e:
            log.error(f"Failed to parse server response for {endpoint}: {e}")
            raise FmdApiException(f"Failed to parse server response for {endpoint}: {e}") from e

    async def get_all_locations(self, num_to_get=-1, skip_empty=True, max_attempts=10):
        """Fetches all or the N most recent location blobs.
        
        Args:
            num_to_get: Number of locations to get (-1 for all)
            skip_empty: If True, skip empty blobs and search backwards for valid data
            max_attempts: Maximum number of indices to try when skip_empty is True
        """
        log.debug(f"Getting locations, num_to_get={num_to_get}, skip_empty={skip_empty}")
        size_str = await self._make_api_request("PUT", "/api/v1/locationDataSize", {"IDT": self.access_token, "Data": "unused"})
        size = int(size_str)
        log.debug(f"Server reports {size} locations available")
        if size == 0:
            log.info("No locations found to download.")
            return []

        locations = []
        if num_to_get == -1:  # Download all
            log.info(f"Found {size} locations to download.")
            indices = range(size)
            # Download all, don't skip any
            for i in indices:
                log.info(f"  - Downloading location at index {i}...")
                blob = await self._make_api_request("PUT", "/api/v1/location", {"IDT": self.access_token, "Data": str(i)})
                locations.append(blob)
            return locations
        else:  # Download N most recent
            num_to_download = min(num_to_get, size)
            log.info(f"Found {size} locations. Downloading the {num_to_download} most recent.")
            start_index = size - 1
            
            if skip_empty:
                # When skipping empties, we'll try indices one at a time starting from most recent
                indices = range(start_index, max(0, start_index - max_attempts), -1)
                log.info(f"Will search for {num_to_download} non-empty location(s) starting from index {start_index}")
            else:
                end_index = size - num_to_download
                log.debug(f"Index calculation: start={start_index}, end={end_index}, range=({start_index}, {end_index - 1}, -1)")
                indices = range(start_index, end_index - 1, -1)
                log.info(f"Will fetch indices: {list(indices)}")

        for i in indices:
            log.info(f"  - Downloading location at index {i}...")
            blob = await self._make_api_request("PUT", "/api/v1/location", {"IDT": self.access_token, "Data": str(i)})
            log.debug(f"Received blob type: {type(blob)}, length: {len(blob) if blob else 0}")
            if blob and blob.strip():  # Check for non-empty, non-whitespace
                log.debug(f"First 100 chars: {blob[:100]}")
                locations.append(blob)
                log.info(f"Found valid location at index {i}")
                # If we got enough non-empty locations, stop
                if len(locations) >= num_to_get and num_to_get != -1:
                    break
            else:
                log.warning(f"Empty blob received for location index {i}, repr: {repr(blob[:50] if blob else blob)}")
        
        if not locations and num_to_get != -1:
            log.warning(f"No valid locations found after checking {min(max_attempts, size)} indices")
        
        return locations

    async def get_pictures(self, num_to_get=-1):
        """Fetches all or the N most recent picture blobs."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(f"{self.base_url}/api/v1/pictures", json={"IDT": self.access_token, "Data": ""}) as resp:
                    resp.raise_for_status()
                    all_pictures = await resp.json()
        except aiohttp.ClientError as e:
            log.warning(f"Failed to get pictures: {e}. The endpoint may not exist or requires a different method.")
            return []

        if num_to_get == -1:  # Download all
            log.info(f"Found {len(all_pictures)} pictures to download.")
            return all_pictures
        else:  # Download N most recent
            num_to_download = min(num_to_get, len(all_pictures))
            log.info(f"Found {len(all_pictures)} pictures. Selecting the {num_to_download} most recent.")
            return all_pictures[-num_to_download:][::-1]

    async def export_data_zip(self, output_file):
        """Downloads the pre-packaged export data zip file."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/v1/exportData", json={"IDT": self.access_token, "Data": "unused"}) as resp:
                    resp.raise_for_status()
                    with open(output_file, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
            log.info(f"Exported data saved to {output_file}")
        except aiohttp.ClientError as e:
            log.error(f"Failed to export data: {e}")
            raise FmdApiException(f"Failed to export data: {e}") from e
    async def send_command(self, command: str) -> bool:
        """Sends a command to the device.
        
        Available commands:
            - "locate" or "locate all": Request location using all providers
            - "locate gps": Request GPS-only location
            - "locate cell": Request cellular network location
            - "locate last": Get last known location (no new request)
            - "ring": Make device ring
            - "lock": Lock the device
            - "camera front": Take picture with front camera
            - "camera back": Take picture with rear camera
            
        Args:
            command: The command string to send to the device
            
        Returns:
            bool: True if command was sent successfully
            
        Raises:
            FmdApiException: If command sending fails
            
        Example:
            # Request a new GPS location
            await api.send_command("locate gps")
            
            # Request location with all providers
            await api.send_command("locate")
            
            # Make the device ring
            await api.send_command("ring")
        """
        log.info(f"Sending command to device: {command}")
        
        # Get current Unix time in milliseconds
        unix_time_ms = int(time.time() * 1000)
        
        # Sign the command using RSA-PSS
        # IMPORTANT: The web client signs "timestamp:command", not just the command!
        # See fmd-server/web/logic.js line 489: sign(key, `${time}:${message}`)
        message_to_sign = f"{unix_time_ms}:{command}"
        message_bytes = message_to_sign.encode('utf-8')
        signature = self.private_key.sign(
            message_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=32
            ),
            hashes.SHA256()
        )
        signature_b64 = base64.b64encode(signature).decode('utf-8').rstrip('=')
        
        try:
            result = await self._make_api_request(
                "POST",
                "/api/v1/command",
                {
                    "IDT": self.access_token,
                    "Data": command,
                    "UnixTime": unix_time_ms,
                    "CmdSig": signature_b64
                },
                expect_json=False
            )
            log.info(f"Command sent successfully: {command}")
            return True
        except Exception as e:
            log.error(f"Failed to send command '{command}': {e}")
            raise FmdApiException(f"Failed to send command '{command}': {e}") from e

    async def request_location(self, provider: str = "all") -> bool:
        """Convenience method to request a new location update from the device.
        
        This triggers the FMD Android app to capture a new location and upload it
        to the server. The location will be available after a short delay (typically
        10-60 seconds depending on GPS acquisition time).
        
        Args:
            provider: Which location provider to use:
                - "all" (default): Use all available providers (GPS, network, fused)
                - "gps": GPS only (most accurate, slower, requires clear sky)
                - "cell" or "network": Cellular network location (fast, less accurate)
                - "last": Don't request new location, just get last known
                
        Returns:
            bool: True if request was sent successfully
            
        Raises:
            FmdApiException: If request fails
            
        Example:
            # Request a new GPS-only location
            api = await FmdApi.create('https://fmd.example.com', 'device-id', 'password')
            await api.request_location('gps')
            
            # Wait for device to capture and upload location
            await asyncio.sleep(30)
            
            # Fetch the new location
            locations = await api.get_all_locations(1)
            location = json.loads(api.decrypt_data_blob(locations[0]))
            print(f"New location: {location['lat']}, {location['lon']}")
        """
        provider_map = {
            "all": "locate",
            "gps": "locate gps",
            "cell": "locate cell",
            "network": "locate cell",
            "last": "locate last"
        }
        
        command = provider_map.get(provider.lower(), "locate")
        log.info(f"Requesting location update with provider: {provider} (command: {command})")
        return await self.send_command(command)
