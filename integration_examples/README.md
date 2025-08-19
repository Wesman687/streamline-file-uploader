# Stream-Line File Server Integration Examples

This directory contains integration examples for different Python frameworks.

## Quick Start

1. **Copy the client library** into your project:
   ```bash
   # Copy the main client file
   cp streamline_file_client.py /path/to/your/project/
   ```

2. **Install dependencies**:
   ```bash
   pip install requests
   ```

3. **Use in your application**:
   ```python
   from streamline_file_client import StreamLineFileClient
   
   client = StreamLineFileClient("your-service-token")
   result = client.upload_file("user123", "/path/to/file.jpg", "photos")
   print(f"File available at: {result['public_url']}")
   ```

## Framework Examples

- [`django_example.py`](django_example.py) - Django integration
- [`flask_example.py`](flask_example.py) - Flask integration  
- [`fastapi_example.py`](fastapi_example.py) - FastAPI integration
- [`generic_example.py`](generic_example.py) - Generic Python usage

## Production Service Token

For your applications, use this service token:
```
ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340
```

**Important**: In production, store this in environment variables:
```python
import os
SERVICE_TOKEN = os.getenv('STREAMLINE_FILE_TOKEN', 'your-token-here')
```

## File Server URL

Production server: `https://file-server.stream-lineai.com`

## Common Use Cases

### 1. User Profile Pictures
```python
manager = StreamLineFileManager(client)
profile_url = manager.upload_profile_picture("user123", "/tmp/avatar.jpg")
# Save profile_url in your user database
```

### 2. Document Management
```python
# Upload contract
doc = manager.upload_document("user123", "/tmp/contract.pdf", "contract")

# Get all user contracts
contracts = manager.get_user_documents("user123", "contract")
```

### 3. Media Storage
```python
# Upload photo
photo = manager.upload_media("user123", "/tmp/photo.jpg", "photos")

# Upload video
video = manager.upload_media("user123", "/tmp/video.mp4", "videos")
```

## Direct File Access

Once uploaded, files are immediately accessible via direct URLs:
```
https://file-server.stream-lineai.com/storage/{user_id}/{folder}/{filename}
```

No authentication needed for file access - perfect for:
- `<img>` tags in HTML
- Video streaming
- Document downloads
- API responses

## Error Handling

```python
try:
    result = client.upload_file("user123", "/path/to/file.jpg")
    print(f"Success: {result['public_url']}")
except FileNotFoundError:
    print("File not found")
except requests.exceptions.HTTPError as e:
    print(f"Upload failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```
