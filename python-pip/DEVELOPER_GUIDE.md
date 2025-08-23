# 🧑‍💻 Developer Guide - Stream-Line File Uploader

Complete guide for integrating file uploads into your applications.

## 📋 **Table of Contents**

1. [Quick Start](#-quick-start)
2. [Installation](#-installation)
3. [Basic Usage](#-basic-usage)
4. [Advanced Features](#-advanced-features)
5. [File Lookup & Search](#-file-lookup--search)
6. [Error Handling](#-error-handling)
7. [Examples](#-examples)
8. [API Reference](#-api-reference)

---

## 🚀 **Quick Start**

### **1. Copy Package to Your Project**
```bash
cp -r /path/to/file-uploader/python-package/streamline_file_uploader /your/project/
```

### **2. Set Environment Variables**
```bash
export AUTH_SERVICE_TOKEN="your-service-token"
export DEFAULT_USER_EMAIL="user@example.com"
```

### **3. Use in 3 Lines**
```python
import asyncio
from streamline_file_uploader import StreamlineFileUploader

async def upload():
    async with StreamlineFileUploader() as uploader:
        result = await uploader.upload_file(
            file_content=b"Hello World!",
            filename="hello.txt",
            folder="documents"
        )
        print(f"Uploaded: {result.public_url}")

asyncio.run(upload())
```

---

## 📦 **Installation**

### **Option 1: Copy Package (Recommended)**
```bash
# Copy the entire package folder
cp -r /path/to/file-uploader/python-package/streamline_file_uploader /your/project/

# Your project structure:
your-project/
├── streamline_file_uploader/
│   ├── __init__.py
│   ├── client.py
│   ├── batch.py
│   ├── file_manager.py
│   ├── file_lookup.py
│   ├── models.py
│   └── exceptions.py
├── main.py
└── requirements.txt
```

### **Option 2: Install Dependencies**
```bash
pip install httpx pydantic
```

---

## 🔧 **Basic Usage**

### **Initialize Uploader**
```python
from streamline_file_uploader import StreamlineFileUploader

# With environment variables
uploader = StreamlineFileUploader()

# Or with explicit parameters
uploader = StreamlineFileUploader(
    service_token="your-token",
    default_user_email="user@example.com",
    base_url="https://file-server.stream-lineai.com"
)
```

### **Upload a File**
```python
# Upload text content
result = await uploader.upload_file(
    file_content=b"File content here",
    filename="document.txt",
    folder="documents"
)

# Upload from file path
result = await uploader.upload_file(
    file_content="/path/to/video.mp4",
    filename="video.mp4",
    folder="veo/videos"
)

# Upload with custom user
result = await uploader.upload_file(
    file_content=video_bytes,
    filename="video.mp4",
    folder="veo/videos",
    user_email="different@user.com"
)
```

### **What You Get Back**
```python
print(f"File key: {result.file_key}")
print(f"Public URL: {result.public_url}")
print(f"Size: {result.size} bytes")
print(f"MIME type: {result.mime_type}")
print(f"Folder: {result.folder}")
print(f"Filename: {result.filename}")
print(f"SHA256: {result.sha256}")
```

---

## 🚀 **Advanced Features**

### **Batch Upload Multiple Files**
```python
files = [
    {
        'content': video_bytes,
        'filename': 'video1.mp4',
        'folder': 'veo/videos'
    },
    {
        'content': doc_bytes,
        'filename': 'doc1.pdf',
        'folder': 'documents'
    },
    {
        'content': image_bytes,
        'filename': 'img1.jpg',
        'folder': 'images'
    }
]

results = await uploader.batch.upload_files(files)
print(f"Uploaded {len(results)} files!")
```

### **Upload with Options**
```python
from streamline_file_uploader import UploadOptions

options = UploadOptions(
    folder="veo/videos",
    mime_type="video/mp4",
    metadata={
        "category": "tutorial",
        "tags": ["python", "coding"],
        "description": "Python tutorial video"
    },
    preserve_filename=True
)

result = await uploader.upload_file(
    file_content=video_bytes,
    filename="tutorial.mp4",
    options=options
)
```

---

## 🔍 **File Lookup & Search**

### **List Files**
```python
# List all files
all_files = await uploader.files.list_files()

# List files in specific folder
videos = await uploader.files.list_files(folder="veo/videos")

# Limit number of results
recent_files = await uploader.files.list_files(limit=10)
```

### **Search Files**
```python
# Search by filename pattern
docs = await uploader.files.search_files(filename_pattern="document")

# Search by MIME type
videos = await uploader.files.search_files(mime_type="video/mp4")

# Search by size
large_files = await uploader.files.search_files(min_size=100*1024*1024)  # >100MB

# Search in specific folder
folder_videos = await uploader.files.search_files(
    folder="veo/videos",
    mime_type="video/mp4"
)
```

### **Advanced Lookup Methods**
```python
# Find all video files
videos = await uploader.lookup.find_video_files(folder="veo/videos")

# Find all image files
images = await uploader.lookup.find_image_files(folder="images")

# Find all document files
documents = await uploader.lookup.find_document_files(folder="documents")

# Find large files (>100MB)
large_files = await uploader.lookup.find_large_files(min_size_mb=100.0)

# Find recent files (last 7 days)
recent_files = await uploader.lookup.find_recent_files(days=7)

# Find files by extension
mp4_files = await uploader.lookup.find_files_by_extension("mp4")

# Get file counts by type
type_counts = await uploader.lookup.get_file_count_by_type()
print(f"Videos: {type_counts.get('video/mp4', 0)}")
print(f"Images: {type_counts.get('image/jpeg', 0)}")
```

---

## 📥 **Download & Access**

### **Get Download URL**
```python
# Get signed download URL
download_url = await uploader.files.get_download_url(
    file_key="storage/user/folder/file.mp4",
    expires_in=3600  # 1 hour
)
print(f"Download: {download_url}")
```

### **Get File Information**
```python
# Get detailed file info
file_info = await uploader.files.get_file_info(file_key="storage/user/folder/file.mp4")
print(f"File size: {file_info.get('file_size')} bytes")
print(f"MIME type: {file_info.get('mime_type')}")
```

### **Get Folder Statistics**
```python
# Get folder stats
stats = await uploader.files.get_folder_stats(folder="veo/videos")
print(f"File count: {stats['file_count']}")
print(f"Total size: {stats['total_size']} bytes")
print(f"MIME types: {stats['mime_types']}")
```

---

## 🚨 **Error Handling**

### **Handle Different Error Types**
```python
from streamline_file_uploader import (
    UploadError, 
    AuthenticationError, 
    FileServerError, 
    ValidationError
)

try:
    result = await uploader.upload_file(...)
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except FileServerError as e:
    print(f"File server error: {e} (Status: {e.status_code})")
except UploadError as e:
    print(f"Upload failed at {e.stage}: {e}")
except ValidationError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### **Check for Specific Errors**
```python
try:
    result = await uploader.upload_file(...)
except FileServerError as e:
    if e.status_code == 404:
        print("File not found")
    elif e.status_code == 403:
        print("Access denied")
    elif e.status_code == 500:
        print("Server error")
    else:
        print(f"HTTP error: {e.status_code}")
```

---

## 📚 **Examples**

### **Video Upload App**
```python
async def upload_video(video_path: str, user_email: str):
    async with StreamlineFileUploader() as uploader:
        # Upload video
        result = await uploader.upload_file(
            file_content=video_path,
            filename=Path(video_path).name,
            folder="veo/videos",
            user_email=user_email
        )
        
        print(f"✅ Video uploaded!")
        print(f"   File key: {result.file_key}")
        print(f"   Public URL: {result.public_url}")
        print(f"   Size: {result.size} bytes")
        
        # List all videos in folder
        videos = await uploader.lookup.find_video_files(folder="veo/videos")
        print(f"📁 Found {len(videos)} videos in veo/videos")
        
        return result

# Usage
result = await upload_video("/path/to/video.mp4", "user@example.com")
```

### **Document Management App**
```python
async def manage_documents(user_email: str):
    async with StreamlineFileUploader() as uploader:
        # Upload multiple documents
        documents = [
            {'content': doc1_bytes, 'filename': 'report.pdf', 'folder': 'reports'},
            {'content': doc2_bytes, 'filename': 'invoice.pdf', 'folder': 'invoices'},
            {'content': doc3_bytes, 'filename': 'contract.pdf', 'folder': 'contracts'}
        ]
        
        results = await uploader.batch.upload_files(documents, user_email=user_email)
        print(f"📄 Uploaded {len(results)} documents")
        
        # Get document statistics
        doc_stats = await uploader.lookup.get_file_count_by_type()
        pdf_count = doc_stats.get('application/pdf', 0)
        print(f"📊 Total PDF documents: {pdf_count}")
        
        return results
```

### **File Search App**
```python
async def search_user_files(user_email: str, query: str):
    async with StreamlineFileUploader() as uploader:
        # Search by filename
        name_results = await uploader.lookup.find_files_by_name(
            filename=query,
            user_email=user_email
        )
        
        # Search by extension
        ext_results = await uploader.lookup.find_files_by_extension(
            extension=query,
            user_email=user_email
        )
        
        # Search recent files
        recent_results = await uploader.lookup.find_recent_files(
            days=7,
            user_email=user_email
        )
        
        return {
            'by_name': name_results,
            'by_extension': ext_results,
            'recent': recent_results
        }

# Usage
results = await search_user_files("user@example.com", "mp4")
print(f"Found {len(results['by_extension'])} MP4 files")
```

---

## 📖 **API Reference**

### **StreamlineFileUploader**

#### **Constructor**
```python
StreamlineFileUploader(
    base_url: Optional[str] = None,
    service_token: Optional[str] = None,
    default_user_email: Optional[str] = None,
    timeout: float = 30.0
)
```

#### **Main Methods**
- `upload_file()` - Upload a single file
- `upload_files()` - Upload multiple files (batch)
- `files.list_files()` - List files
- `files.search_files()` - Search files
- `files.get_download_url()` - Get download URL
- `lookup.find_video_files()` - Find video files
- `lookup.find_image_files()` - Find image files
- `lookup.find_document_files()` - Find document files

### **UploadOptions**
```python
class UploadOptions:
    folder: Optional[str] = None          # Folder path
    mime_type: Optional[str] = None      # MIME type
    metadata: Optional[Dict[str, Any]]   # Custom metadata
    preserve_filename: bool = True        # Keep original filename
```

### **UploadResult**
```python
class UploadResult:
    file_key: str        # Unique identifier
    public_url: str      # Public access URL
    size: int            # File size in bytes
    mime_type: str       # MIME type
    folder: Optional[str] # Folder path
    filename: str        # Filename
    sha256: str          # File hash
```

---

## 🎯 **Best Practices**

### **1. Use Context Manager**
```python
# ✅ Good - Automatic cleanup
async with StreamlineFileUploader() as uploader:
    result = await uploader.upload_file(...)

# ❌ Bad - Manual cleanup required
uploader = StreamlineFileUploader()
result = await uploader.upload_file(...)
await uploader.close()
```

### **2. Set Default User Email**
```python
# ✅ Good - Set default user
uploader = StreamlineFileUploader(default_user_email="user@example.com")
result = await uploader.upload_file(file_content, filename, folder)

# ❌ Bad - Pass user_email every time
result = await uploader.upload_file(file_content, filename, folder, user_email="user@example.com")
```

### **3. Use Environment Variables**
```bash
# ✅ Good - Environment variables
export AUTH_SERVICE_TOKEN="your-token"
export DEFAULT_USER_EMAIL="user@example.com"

# ❌ Bad - Hardcoded in code
uploader = StreamlineFileUploader(
    service_token="hardcoded-token",
    default_user_email="hardcoded@email.com"
)
```

### **4. Handle Errors Gracefully**
```python
try:
    result = await uploader.upload_file(...)
except FileServerError as e:
    if e.status_code == 404:
        # Handle not found
        pass
    elif e.status_code == 403:
        # Handle access denied
        pass
    else:
        # Handle other errors
        raise
```

---

## 🚀 **That's It!**

**You now have a complete, production-ready file upload solution that:**

- ✅ **Preserves filenames** - No more "uploaded_file" names
- ✅ **Organizes files** - Files go to the right folders
- ✅ **Handles errors** - Clear error messages and handling
- ✅ **Provides search** - Find files by type, size, date, name
- ✅ **Supports batch** - Upload multiple files at once
- ✅ **Easy integration** - Just copy the package and use it

**Your applications can now handle file uploads with just a few lines of code!** 🎉

