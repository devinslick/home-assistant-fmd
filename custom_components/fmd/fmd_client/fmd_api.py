"""
Core API library for interacting with an FMD server.

This module provides a class that handles authentication, key management,
and data decryption for FMD clients.
"""
import base64
import logging
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
        return await self._make_api_request("POST", "/api/v1/salt", {"IDT": fmd_id, "Data": ""})

    async def _get_access_token(self, fmd_id, password_hash, session_duration):
        payload = {
            "IDT": fmd_id, "Data": password_hash,
            "SessionDurationSeconds": session_duration
        }
        return await self._make_api_request("POST", "/api/v1/requestAccess", payload)

    async def _get_private_key_blob(self):
        return await self._make_api_request("POST", "/api/v1/key", {"IDT": self.access_token, "Data": "unused"})

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
        """Decrypts a data blob using the instance's private key."""
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
                    if not stream:
                        if expect_json:
                            # Try JSON first, fall back to text if content-type is wrong
                            content_type = resp.content_type.lower() if resp.content_type else ''
                            if 'json' in content_type:
                                json_data = await resp.json()
                                log.debug(f"{endpoint} JSON response: {json_data}")
                                return json_data["Data"]
                            else:
                                # Server returned non-JSON content type, read as text
                                log.debug(f"{endpoint} returned content-type '{resp.content_type}', reading as text")
                                text_data = await resp.text()
                                log.debug(f"{endpoint} text response length: {len(text_data)}, content: {text_data[:500]}")
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
        size_str = await self._make_api_request("POST", "/api/v1/locationDataSize", {"IDT": self.access_token, "Data": "unused"})
        size = int(size_str)
        log.debug(f"Server reports {size} locations available")
        if size == 0:
            log.info("No locations found to download.")
            return []

        locations = []
        if num_to_get == -1:  # Download all
            log.info(f"Found {size} locations to download.")
            indices = range(size)
            skip_empty = False  # Don't skip when downloading all
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
            blob = await self._make_api_request("POST", "/api/v1/location", {"IDT": self.access_token, "Data": str(i)})
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