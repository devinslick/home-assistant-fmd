"""
Core API library for interacting with an FMD server.

This module provides a client that communicates with FMD (Find My Device) servers
using the FMD API protocol, encryption scheme, and command format.

FMD Project Attribution:
    - FMD (Find My Device): https://fmd-foss.org
    - Created by Nulide (http://nulide.de)
    - Maintained by Thore (https://thore.io) and the FMD-FOSS team
    - FMD Server: https://gitlab.com/fmd-foss/fmd-server (AGPL-3.0)
    - FMD Android: https://gitlab.com/fmd-foss/fmd-android (GPL-3.0)

This Client Implementation:
    - MIT License - Copyright (c) 2025 Devin Slick
    - Independent client implementation for FMD API
    - Follows FMD's RSA-3072 + AES-GCM encryption protocol
    - Compatible with FMD server v012.0 API

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

class FmdCommands:
    """
    Constants for available FMD device commands.
    
    These commands are supported by the FMD Android app and can be sent
    via the send_command() method. Using these constants helps prevent typos
    and improves code discoverability.
    
    Command Categories:
        Location Requests:
            LOCATE_ALL, LOCATE_GPS, LOCATE_CELL, LOCATE_LAST
        
        Device Control:
            RING, LOCK, DELETE
        
        Camera:
            CAMERA_FRONT, CAMERA_BACK
        
        Audio/Notifications:
            BLUETOOTH_ON, BLUETOOTH_OFF
            NODISTURB_ON, NODISTURB_OFF
            RINGERMODE_NORMAL, RINGERMODE_VIBRATE, RINGERMODE_SILENT
        
        Information:
            STATS, GPS (battery/GPS status)
    
    Example:
        from fmd_api import FmdApi, FmdCommands
        
        api = await FmdApi.create('https://fmd.example.com', 'device-id', 'password')
        
        # Ring the device
        await api.send_command(FmdCommands.RING)
        
        # Request GPS location
        await api.send_command(FmdCommands.LOCATE_GPS)
        
        # Enable Do Not Disturb
        await api.send_command(FmdCommands.NODISTURB_ON)
    """
    # Location requests
    LOCATE_ALL = "locate"
    LOCATE_GPS = "locate gps"
    LOCATE_CELL = "locate cell"
    LOCATE_LAST = "locate last"
    
    # Device control
    RING = "ring"
    LOCK = "lock"
    DELETE = "delete"  # Wipes device data (destructive!)
    
    # Camera
    CAMERA_FRONT = "camera front"
    CAMERA_BACK = "camera back"
    
    # Bluetooth
    BLUETOOTH_ON = "bluetooth on"
    BLUETOOTH_OFF = "bluetooth off"
    
    # Do Not Disturb
    NODISTURB_ON = "nodisturb on"
    NODISTURB_OFF = "nodisturb off"
    
    # Ringer Mode
    RINGERMODE_NORMAL = "ringermode normal"
    RINGERMODE_VIBRATE = "ringermode vibrate"
    RINGERMODE_SILENT = "ringermode silent"
    
    # Information/Status
    STATS = "stats"  # Network info (IP addresses, WiFi networks)
    GPS = "gps"      # Battery and GPS status

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
        
        Complete list of available commands (or use FmdCommands constants):
        
        Location Requests:
            - "locate" - Request location using all available providers (GPS, network, fused)
            - "locate gps" - GPS-only location (most accurate, requires clear sky view)
            - "locate cell" - Cellular network location (fast, less accurate)
            - "locate last" - Return last known location without new request
        
        Device Control:
            - "ring" - Make device ring at full volume (ignores silent/DND mode)
            - "lock" - Lock the device screen
            - "delete" - ⚠️ DESTRUCTIVE: Wipes all device data (factory reset)
        
        Camera:
            - "camera front" - Take photo with front-facing camera
            - "camera back" - Take photo with rear-facing camera
        
        Audio & Notifications:
            - "bluetooth on" - Enable Bluetooth (Android 12+ requires permission)
            - "bluetooth off" - Disable Bluetooth
            - "nodisturb on" - Enable Do Not Disturb mode (requires permission)
            - "nodisturb off" - Disable Do Not Disturb mode
            - "ringermode normal" - Set ringer to normal (sound + vibrate)
            - "ringermode vibrate" - Set ringer to vibrate only
            - "ringermode silent" - Set ringer to silent (also enables DND)
        
        Information/Status:
            - "stats" - Get network info (IP addresses, WiFi SSID/BSSID)
            - "gps" - Get battery level and GPS status
        
        Args:
            command: The command string to send (see list above or use FmdCommands constants)
            
        Returns:
            bool: True if command was sent successfully to the server
            
        Raises:
            FmdApiException: If command sending fails
            
        Note:
            Commands are sent to the server immediately, but execution on the device
            depends on the device being online and the FMD app having necessary permissions.
            Some commands (bluetooth, nodisturb, ringermode) require special Android permissions.
            
        Examples:
            # Using string commands
            await api.send_command("ring")
            await api.send_command("locate gps")
            await api.send_command("bluetooth on")
            await api.send_command("nodisturb on")
            await api.send_command("ringermode vibrate")
            
            # Using constants (recommended to prevent typos)
            from fmd_api import FmdCommands
            await api.send_command(FmdCommands.RING)
            await api.send_command(FmdCommands.LOCATE_GPS)
            await api.send_command(FmdCommands.BLUETOOTH_ON)
            await api.send_command(FmdCommands.NODISTURB_ON)
            await api.send_command(FmdCommands.RINGERMODE_VIBRATE)
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

    async def toggle_bluetooth(self, enable: bool) -> bool:
        """Enable or disable Bluetooth on the device.
        
        Args:
            enable: True to enable Bluetooth, False to disable
            
        Returns:
            bool: True if command was sent successfully
            
        Raises:
            FmdApiException: If command sending fails
            
        Note:
            On Android 12+, the FMD app requires BLUETOOTH_CONNECT permission.
            
        Example:
            # Enable Bluetooth
            await api.toggle_bluetooth(True)
            
            # Disable Bluetooth
            await api.toggle_bluetooth(False)
        """
        command = FmdCommands.BLUETOOTH_ON if enable else FmdCommands.BLUETOOTH_OFF
        log.info(f"{'Enabling' if enable else 'Disabling'} Bluetooth")
        return await self.send_command(command)

    async def toggle_do_not_disturb(self, enable: bool) -> bool:
        """Enable or disable Do Not Disturb mode on the device.
        
        Args:
            enable: True to enable DND mode, False to disable
            
        Returns:
            bool: True if command was sent successfully
            
        Raises:
            FmdApiException: If command sending fails
            
        Note:
            Requires Do Not Disturb Access permission on the device.
            
        Example:
            # Enable Do Not Disturb
            await api.toggle_do_not_disturb(True)
            
            # Disable Do Not Disturb
            await api.toggle_do_not_disturb(False)
        """
        command = FmdCommands.NODISTURB_ON if enable else FmdCommands.NODISTURB_OFF
        log.info(f"{'Enabling' if enable else 'Disabling'} Do Not Disturb mode")
        return await self.send_command(command)

    async def set_ringer_mode(self, mode: str) -> bool:
        """Set the device ringer mode.
        
        Args:
            mode: Ringer mode to set:
                - "normal": Sound + vibrate enabled
                - "vibrate": Vibrate only, no sound
                - "silent": Silent mode (also enables Do Not Disturb)
                
        Returns:
            bool: True if command was sent successfully
            
        Raises:
            FmdApiException: If command sending fails or invalid mode
            ValueError: If mode is not one of the valid options
            
        Note:
            - Setting to "silent" also enables Do Not Disturb mode (Android behavior)
            - Requires Do Not Disturb Access permission on the device
            
        Example:
            # Set to vibrate only
            await api.set_ringer_mode("vibrate")
            
            # Set to normal (sound + vibrate)
            await api.set_ringer_mode("normal")
            
            # Set to silent (also enables DND)
            await api.set_ringer_mode("silent")
        """
        mode = mode.lower()
        mode_map = {
            "normal": FmdCommands.RINGERMODE_NORMAL,
            "vibrate": FmdCommands.RINGERMODE_VIBRATE,
            "silent": FmdCommands.RINGERMODE_SILENT
        }
        
        if mode not in mode_map:
            raise ValueError(f"Invalid ringer mode '{mode}'. Must be 'normal', 'vibrate', or 'silent'")
        
        command = mode_map[mode]
        log.info(f"Setting ringer mode to: {mode}")
        return await self.send_command(command)

    async def get_device_stats(self) -> bool:
        """Request device network statistics (IP addresses, WiFi info).
        
        The device will respond with information about:
        - IP addresses (IPv4 and IPv6)
        - Connected WiFi networks (SSID and BSSID)
        
        Returns:
            bool: True if command was sent successfully
            
        Raises:
            FmdApiException: If command sending fails
            
        Note:
            Requires Location permission on the device (needed to access WiFi info).
            The response is sent back to the device via the transport mechanism
            (e.g., SMS, push notification) rather than stored on the server.
            
        Example:
            # Request device statistics
            await api.get_device_stats()
        """
        log.info("Requesting device network statistics")
        return await self.send_command(FmdCommands.STATS)

    async def take_picture(self, camera: str = "back") -> bool:
        """Request the device to take a picture.
        
        Args:
            camera: Which camera to use - "front" or "back" (default: "back")
                
        Returns:
            bool: True if command was sent successfully
            
        Raises:
            FmdApiException: If command sending fails
            ValueError: If camera is not "front" or "back"
            
        Note:
            Pictures are uploaded to the server and can be retrieved using
            get_all_pictures() and decrypt_data_blob().
            
        Example:
            # Take picture with rear camera
            await api.take_picture("back")
            
            # Take picture with front camera (selfie)
            await api.take_picture("front")
        """
        camera = camera.lower()
        if camera not in ["front", "back"]:
            raise ValueError(f"Invalid camera '{camera}'. Must be 'front' or 'back'")
        
        command = FmdCommands.CAMERA_FRONT if camera == "front" else FmdCommands.CAMERA_BACK
        log.info(f"Requesting picture from {camera} camera")
        return await self.send_command(command)

