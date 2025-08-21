# Setup Guide

## 1. Install the Package

```bash
pip install streamline-file-uploader
```

## 2. Set Environment Variables

```bash
export UPLOAD_BASE_URL="https://file-server.stream-lineai.com"
export AUTH_SERVICE_TOKEN="your-service-token-here"
export DEFAULT_USER_ID="user@example.com"
```

## 3. Run the Example

```bash
python example.py
```

## 4. Use in Your Code

```python
import asyncio
from streamline_file_uploader import StreamlineFileUploader

async def upload_file():
    async with StreamlineFileUploader() as uploader:
        result = await uploader.upload_file(
            file_content=b"Hello World!",
            filename="hello.txt",
            folder="documents"
        )
        print(f"File uploaded to: {result.public_url}")

asyncio.run(upload_file())
```

## That's it! 🎉
