# 🚀 Quick Install & Use Guide

## **Option 1: Copy Package to Your Project (Recommended)**

```bash
# Copy the package directly to your project
cp -r /path/to/file-uploader/python-package/streamline_file_uploader /your/project/

# Your project structure:
your-project/
├── streamline_file_uploader/  ← Copy this folder
├── main.py
└── requirements.txt
```

**Then use it:**
```python
from streamline_file_uploader import StreamlineFileUploader
```

## **Option 2: Install from Local Directory**

```bash
cd /path/to/file-uploader/python-package
pip install -e .
```

## **Option 3: Install from GitHub (Recommended)**

```bash
pip install git+https://github.com/Wesman687/streamline-file-uploader.git#subdirectory=python-package
```

---

## 🔧 **Setup (3 Steps)**

### **1. Set Environment Variables**
```bash
export AUTH_SERVICE_TOKEN="your-service-token-here"
export UPLOAD_BASE_URL="https://file-server.stream-lineai.com"
# Note: NO DEFAULT_USER_EMAIL - you'll pass user_email for each upload
```

### **2. Install Dependencies**
```bash
pip install httpx pydantic
```

### **3. Use in Your Code**
```python
import asyncio
from streamline_file_uploader import StreamlineFileUploader

async def main():
    async with StreamlineFileUploader() as uploader:
        result = await uploader.upload_file(
            file_content=b"Hello World!",
            filename="hello.txt",
            folder="documents",
            user_email="user@example.com"  # ← REQUIRED: Pass the actual user
        )
        print(f"Uploaded: {result.public_url}")

asyncio.run(main())
```

---

## 🎯 **That's It!**

**No more filename changes, no more wrong folders, no more complex API calls.**

Just copy the package and use it in 3 lines! 🚀

