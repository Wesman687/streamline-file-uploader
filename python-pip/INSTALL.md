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

## **Option 3: Install from GitHub (When Available)**

```bash
pip install git+https://github.com/YOUR_USERNAME/file-uploader.git
```

---

## 🔧 **Setup (3 Steps)**

### **1. Set Environment Variables**
```bash
export AUTH_SERVICE_TOKEN="your-service-token-here"
export DEFAULT_USER_EMAIL="user@example.com"
export UPLOAD_BASE_URL="https://file-server.stream-lineai.com"
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
            folder="documents"
        )
        print(f"File uploaded: {result.public_url}")

asyncio.run(main())
```

---

## 🎯 **That's It!**

**No more filename changes, no more wrong folders, no more complex API calls.**

Just copy the package and use it in 3 lines! 🚀

