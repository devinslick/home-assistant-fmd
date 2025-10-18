# Security Fix: Removed Hardcoded Credentials

## Issue
Hardcoded credentials were present in multiple debugging scripts and have been rotated and removed.

## Changes Made

All debugging scripts now require credentials to be passed as command-line arguments:

### 1. `show_raw_locations.py`
**Before:** Hardcoded URL, device ID, and password
**After:** Requires `--url`, `--id`, `--password` arguments

**Usage:**
```bash
python show_raw_locations.py --url https://fmd.example.com --id device-id --password your-password
```

### 2. `quick_check.py`
**Before:** Hardcoded URL, device ID, and password
**After:** Requires `--url`, `--id`, `--password` arguments

**Usage:**
```bash
python quick_check.py --url https://fmd.example.com --id device-id --password your-password
```

### 3. `test_ring.py`
**Before:** Hardcoded URL, device ID, and password
**After:** Requires `--url`, `--id`, `--password` arguments

**Usage:**
```bash
python test_ring.py --url https://fmd.example.com --id device-id --password your-password
```

### 4. `test_command.py`
**Before:** Had DEFAULT_URL, DEFAULT_ID, DEFAULT_PASSWORD constants with real credentials
**After:** Requires `--url`, `--id`, `--password` arguments (no defaults)

**Usage:**
```bash
python test_command.py ring --url https://fmd.example.com --id device-id --password your-password
python test_command.py "locate gps" --url https://fmd.example.com --id device-id --password your-password
```

## Recommended Actions

1. **Rotate the exposed password** - ✅ User has already changed the password
2. **Review GitHub commit history** - Consider if sensitive commits need to be removed from history
3. **Use environment variables** - For frequent testing, consider using environment variables:
   ```bash
   export FMD_URL="https://fmd.example.com"
   export FMD_ID="device-id"
   export FMD_PASSWORD="your-password"
   ```
   Then create a wrapper script that reads from env vars if needed.

4. **Add to .gitignore** - Consider adding a `.env` file pattern if using environment variables:
   ```
   .env
   *.env
   credentials.txt
   ```

## Security Best Practices Going Forward

1. **Never commit credentials** - Always use command-line arguments or environment variables
2. **Use example values in documentation** - Use `alice`, `secret`, `https://fmd.example.com` as examples
3. **Review before committing** - Check for hardcoded secrets before `git commit`
4. **Consider using git hooks** - Set up pre-commit hooks to scan for potential secrets
