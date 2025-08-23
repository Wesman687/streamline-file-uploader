# Setup Guide

## 1. Install the Package

```bash
pip install git+https://github.com/streamline-ai/file-uploader.git
or
pip install streamline-file-uploader
```

## 2. Set Environment Variables

```bash
export UPLOAD_BASE_URL="https://file-server.stream-lineai.com"
export AUTH_SERVICE_TOKEN="your-service-token-here"
# Note: NO DEFAULT_USER_EMAIL - you'll pass user_email for each upload
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
            folder="documents",
            user_email="user@example.com"  # ← REQUIRED: Pass the actual user
        )
        print(f"File uploaded to: {result.public_url}")

asyncio.run(upload_file())
```

## That's it! 🎉
