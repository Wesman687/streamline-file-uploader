# File Public Access Guide

## Understanding File Access in the File Server

Files uploaded through the SDK are **automatically public** and accessible via direct URLs. No additional "make public" step is required.

## How It Works

1. **Upload Process**:
   - Files are uploaded via the `/v1/files/init`, `/v1/files/part`, and `/v1/files/complete` endpoints
   - The server stores files with keys like: `storage/{user_id}/{folder}/{uuid_filename}`
   - The server returns the `file_key` in the response

2. **Public URL Construction**:
   - The SDK constructs the public URL as: `{base_url}/{file_key}`
   - Example: `https://file-server.stream-lineai.com/storage/user@example.com/folder/abc123_file.jpg`

3. **File Serving**:
   - Files are served publicly via the `/storage/{user_id}/{file_path:path}` endpoint
   - No authentication is required to access files via this endpoint
   - Files are immediately accessible after upload completes

## Common Issues and Solutions

### Issue 1: File Uploads but URL Returns 404

**Symptoms**: File uploads successfully, but accessing the public URL returns 404.

**Possible Causes**:
1. **Timing Issue**: File might not be immediately available after upload
2. **URL Construction Mismatch**: The file_key format doesn't match the expected URL structure
3. **Email Address Encoding**: User IDs with `@` symbols might need URL encoding

**Solutions**:

```python
from streamline_file_uploader import StreamlineFileUploader
import asyncio

async def upload_and_verify():
    uploader = StreamlineFileUploader(
        service_token="your-token"
    )
    
    # Upload file
    result = await uploader.upload_file(
        file_content=b"test content",
        filename="test.txt",
        folder="test",
        user_email="user@example.com"
    )
    
    print(f"File Key: {result.file_key}")
    print(f"Public URL: {result.public_url}")
    
    # Wait for file to be available (optional)
    is_available = await uploader.wait_for_file_availability(
        result.public_url,
        max_wait=30
    )
    
    if is_available:
        print("✅ File is accessible!")
    else:
        print("❌ File is not accessible")
        
        # Verify file exists by listing
        files = await uploader.list_files(
            user_email="user@example.com",
            folder="test"
        )
        print(f"Files in folder: {len(files)}")
        for f in files:
            print(f"  - {f.get('key')}")
    
    await uploader.close()

asyncio.run(upload_and_verify())
```

### Issue 2: Email Addresses in User IDs

**Problem**: User IDs containing `@` symbols (like email addresses) might cause URL issues.

**Solution**: The SDK and server handle email addresses automatically. FastAPI URL-encodes path parameters, so `user@example.com` is handled correctly.

**Verification**:
```python
# Test with email address
result = await uploader.upload_file(
    file_content=b"test",
    filename="test.txt",
    user_email="user@example.com"  # Email addresses work fine
)

# The public_url will be:
# https://file-server.stream-lineai.com/storage/user@example.com/test/abc123_test.txt
# FastAPI automatically handles the @ symbol
```

### Issue 3: Files Not Immediately Accessible

**Problem**: Files might take a moment to be available after upload.

**Solution**: Use the `wait_for_file_availability()` method:

```python
result = await uploader.upload_file(...)

# Wait up to 30 seconds for file to be available
is_available = await uploader.wait_for_file_availability(
    result.public_url,
    max_wait=30,
    check_interval=0.5
)

if is_available:
    print("File is ready!")
else:
    print("File did not become available in time")
```

### Issue 4: Verifying File Access

**Use the verification methods**:

```python
# Quick check
is_accessible = await uploader.verify_file_access(result.public_url)

# Or wait for availability
is_available = await uploader.wait_for_file_availability(result.public_url)
```

## Best Practices

1. **Always use the returned `public_url`**: Never manually construct URLs
   ```python
   # ✅ CORRECT
   result = await uploader.upload_file(...)
   url = result.public_url
   
   # ❌ WRONG
   url = f"{base_url}/storage/{user_email}/{folder}/{filename}"
   ```

2. **Verify access after upload** (optional but recommended):
   ```python
   result = await uploader.upload_file(...)
   if await uploader.verify_file_access(result.public_url):
       print("File is accessible!")
   ```

3. **Handle errors gracefully**:
   ```python
   try:
       result = await uploader.upload_file(...)
       # Verify access
       if not await uploader.verify_file_access(result.public_url):
           # Retry or log error
           pass
   except Exception as e:
       print(f"Upload failed: {e}")
   ```

## Testing Your Setup

Use the provided test script:

```bash
export AUTH_SERVICE_TOKEN="your-token"
export UPLOAD_BASE_URL="https://file-server.stream-lineai.com"
python test_public_access.py
```

This will:
1. Upload a test file
2. Verify the file is accessible
3. Check URL construction
4. List files to verify upload

## Debugging

If files aren't accessible:

1. **Check the file_key format**:
   ```python
   result = await uploader.upload_file(...)
   print(f"File Key: {result.file_key}")
   # Should be: storage/{user_id}/{folder}/{uuid_filename}
   ```

2. **Verify file exists**:
   ```python
   files = await uploader.list_files(user_email="user@example.com")
   for f in files:
       if f['key'] == result.file_key:
           print("File found in listing!")
   ```

3. **Test URL directly**:
   ```python
   import httpx
   async with httpx.AsyncClient() as client:
       response = await client.head(result.public_url)
       print(f"Status: {response.status_code}")
   ```

## API Reference

### New Methods Added

- `verify_file_access(public_url, timeout=10)`: Check if a file is accessible
- `wait_for_file_availability(public_url, max_wait=30, check_interval=0.5)`: Wait for file to become available

Both methods are available on:
- `StreamlineFileUploader` instance
- `FileManager` instance (via `uploader.file_manager`)

