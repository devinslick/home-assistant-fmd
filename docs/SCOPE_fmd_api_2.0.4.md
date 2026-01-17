fmd_api 2.0.3 → 2.0.4 update brief for Home Assistant
Target: Update the HA integration to adopt password-free auth artifacts, align with picture API renames, respect stricter wipe validation, and leverage improved error/reauth paths in fmd_api v2.0.4.

Key changes that affect the integration

Password-free resume and reauth
New: FmdClient.create(..., drop_password=True), export_auth_artifacts(), from_auth_artifacts(), resume(), drop_password()
401 handling: If raw password missing but password_hash is present in artifacts, client performs hash-based reauth automatically.
Private key load supports PEM or DER artifacts.
Picture API renaming (Device)
New canonical: get_picture_blobs() and decode_picture()
Deprecated wrappers still work but emit DeprecationWarning: take_front_photo(), take_rear_photo(), fetch_pictures(), get_pictures() (Device), get_picture(), download_photo()
download_photo() now directly calls decode_picture() to avoid chained deprecations.
Wipe (factory reset) validation
Device.wipe(pin=..., confirm=True) required and PIN must be alphanumeric ASCII with no spaces. Future 8+ enforcement may come upstream; don’t enforce locally yet.
Lock message
Device.lock(message=...) now allows a message; it’s sanitized client-side. Safe to expose as optional parameter.
Export ZIP robustness
export_data_zip detects PNG vs default JPG, records per-item errors in manifests, and tolerates odd/non-list responses.
Error handling and retries
Improved 429 (Retry-After number/date), connection/5xx backoff, and explicit no-retry on unsafe command POSTs.
401 with no password/hash now raises clearly.
What to change in HA integration

Authentication and client lifecycle
On initial setup:
Use FmdClient.create(base_url, fmd_id, password, drop_password=True) to avoid retaining raw password.
Immediately call artifacts = await client.export_auth_artifacts() and persist artifacts securely in HA storage (ConfigEntry data or secret store).
On subsequent starts:
Resume with client = await FmdClient.from_auth_artifacts(artifacts) instead of asking for raw password.
On token expiry (401):
No action needed if artifacts include password_hash; client auto-reauths. Ensure artifacts persist password_hash; if missing, prompt user once to re-onboard and regenerate artifacts.
Migration path:
If existing entries store raw password, convert to artifacts once: export_auth_artifacts(), persist, then drop password. Remove password from storage.
Picture handling
Replace deprecated Device wrappers:
For taking pictures: use await client.take_picture("front"|"back") (still in client) or device.take_front_picture()/take_rear_picture() (preferred).
For fetching/decoding:
blobs = await device.get_picture_blobs(n) # list[str]
photo = await device.decode_picture(blobs[i]) # PhotoResult: data (bytes), mime_type, timestamp, raw
Remove calls to device.fetch_pictures(), device.get_pictures(), device.get_picture(), device.download_photo() where possible. Keep temporary compatibility if needed but migrate codepaths.
Wipe command UI/validation
Ensure wipe action enforces:
confirm=True in the call
PIN required and must be alphanumeric ASCII with no spaces. Provide helpful validation message in UI. Don’t enforce 8+ yet; just display a warning note that future server versions may require it.
Lock with message
Surface an optional “Lock message” input in the service or config flow. Integration can pass message through device.lock(message=...). Client sanitizes dangerous characters and caps length.
Error handling improvements
Assume client.get_locations(), get_pictures() may return empty lists safely; non-dict or odd server JSON is handled internally.
Keep service-level retries minimal; rely on client’s backoff for GET/PUT. Don’t retry unsafe POST command replays in the integration.
On irrecoverable errors, surface user-friendly messages and suggest reauth only if artifacts are missing or invalid.
Storage contract for artifacts
Required fields to persist from export_auth_artifacts():
base_url, fmd_id, access_token, private_key (PEM string), password_hash (optional but recommended), session_duration, token_issued_at.
Ensure secret storage where possible; treat password_hash and private_key as sensitive.
Minimal code patterns

On first auth:
client = await FmdClient.create(url, fmd_id, password, drop_password=True)
artifacts = await client.export_auth_artifacts()
store artifacts in config_entry.data (mark sensitive where supported)
await client.close()
On setup_entry:
client = await FmdClient.from_auth_artifacts(config_entry.data["artifacts"])
keep a shared client for platforms; ensure graceful close on unload
Picture flow:
blobs = await device.get_picture_blobs(num)
results = []
for b in blobs: results.append(await device.decode_picture(b))
Wipe:
await device.wipe(pin, confirm=True)
HA checklist

Replace any usage of deprecated device picture methods with get_picture_blobs()/decode_picture().
Introduce artifact storage; migrate from password storage to artifacts on next successful auth.
Ensure resume path uses from_auth_artifacts(); remove reliance on raw password post-migration.
Update any wipe service schemas to validate alphanumeric ASCII PIN without spaces; keep confirm=True.
Add optional lock message parameter to the lock service.
Validate that service error handling relies on fmd_api exceptions; keep UI error messages clear.
Update integration docs to reflect password-free storage and picture API changes.
Notes for reviewers

Backward compatibility: Deprecated methods still function, but migration is encouraged to avoid warnings and future removals.
Security posture improves by eliminating raw password storage; artifacts still sensitive and should use HA’s secure storage when possible.
If you paste this into the HA repo and ask Copilot to “apply these updates across the integration,” it should have enough context to propose specific file edits (config flows, services, storage, and platform code).
