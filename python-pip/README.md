# Stream-Line File Uploader - Simple Usage Guide

A Python package that makes it incredibly easy to upload files to your Stream-Line file server with automatic folder organization.

## 🚀 Quick Start

### 1. Install the Package
```bash
pip install git+https://github.com/Wesman687/streamline-file-uploader.git#subdirectory=python-package
```

### 2. Set Environment Variables
```bash
export UPLOAD_BASE_URL="https://file-server.stream-lineai.com"
export AUTH_SERVICE_TOKEN="your-service-token-here"
# Note: NO DEFAULT_USER_EMAIL - you'll pass user_email for each upload
```

### 3. Upload a File (3 lines!)
```python
import asyncio
from streamline_file_uploader import StreamlineFileUploader

async def upload():
    async with StreamlineFileUploader() as uploader:
        result = await uploader.upload_file(
            file_content=b"Hello World!",
            filename="hello.txt",
            folder="documents",
            user_email="user@example.com"  # ← REQUIRED: Pass the actual user
        )
        print(f"File uploaded to: {result.public_url}")

asyncio.run(upload())
```

## 📁 Upload to Specific Folders

```python
# Upload to veo/videos folder
result = await uploader.upload_file(
    file_content=video_bytes,
    filename="my_video.mp4",
    folder="veo/videos"
)

# Upload to documents/invoices folder
result = await uploader.upload_file(
    file_content=invoice_bytes,
    filename="invoice_2024.pdf",
    folder="documents/invoices"
)
```

## 📦 Batch Upload Multiple Files

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
    }
]

results = await uploader.batch.upload_files(files)
print(f"Uploaded {len(results)} files!")
```

## 🔍 Find Your Files

```python
# List all files
all_files = await uploader.files.list_files()

# List files in a specific folder
videos = await uploader.files.list_files(folder="veo/videos")

# Search for specific files
mp4_files = await uploader.files.search_files(
    mime_type="video/mp4",
    folder="veo/videos"
)

# Search by filename
docs = await uploader.files.search_files(filename_pattern="document")
```

## 🔎 Advanced File Lookup

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
print(f"Documents: {type_counts.get('application/pdf', 0)}")

## 📥 Download Files

```python
# Get a download URL for a file
download_url = await uploader.files.get_download_url(file_key="storage/user/folder/file.mp4")
print(f"Download: {download_url}")
```

## 📊 Get Folder Information

```python
# Get statistics for a folder
stats = await uploader.files.get_folder_stats(folder="veo/videos")
print(f"Folder has {stats['file_count']} files")
print(f"Total size: {stats['total_size']} bytes")
```

## 🎯 Complete Example

```python
import asyncio
from streamline_file_uploader import StreamlineFileUploader

async def main():
    async with StreamlineFileUploader() as uploader:
        # Upload a video for user1
        result1 = await uploader.upload_file(
            file_content=open("video.mp4", "rb").read(),
            filename="my_video.mp4",
            folder="veo/videos",
            user_email="user1@example.com"  # ← REQUIRED: Pass the actual user
        )
        
        print(f"✅ Video uploaded for user1!")
        print(f"   File key: {result1.file_key}")
        print(f"   Public URL: {result1.public_url}")
        print(f"   Size: {result1.size} bytes")
        
        # Upload a document for user2
        result2 = await uploader.upload_file(
            file_content=open("document.pdf", "rb").read(),
            filename="report.pdf",
            folder="documents",
            user_email="user2@example.com"  # ← REQUIRED: Pass the actual user
        )
        
        print(f"✅ Document uploaded for user2!")
        print(f"   File key: {result2.file_key}")
        
        # List all videos for user1
        videos = await uploader.files.list_files(
            folder="veo/videos",
            user_email="user1@example.com"  # ← REQUIRED: Pass the actual user
        )
        print(f"📁 Found {len(videos)} videos for user1 in veo/videos")
        
        # Get download URL for user1's video
        download_url = await uploader.files.get_download_url(result1.file_key)
        print(f"🔗 Download URL: {download_url}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 Configuration Options

### Environment Variables (Recommended)
```bash
UPLOAD_BASE_URL=https://file-server.stream-lineai.com
AUTH_SERVICE_TOKEN=your-service-token
# Note: NO DEFAULT_USER_EMAIL - pass user_email for each upload
```

### Or Pass Parameters Directly
```python
uploader = StreamlineFileUploader(
    base_url="https://file-server.stream-lineai.com",
    service_token="your-token"
    # Note: NO default_user_email - pass user_email for each upload
)
```

## 📋 What You Get

Every upload returns an `UploadResult` object with:
- `file_key`: Unique identifier for the file
- `public_url`: Public URL to access the file
- `size`: File size in bytes
- `mime_type`: MIME type of the file
- `folder`: Folder the file was uploaded to
- `filename`: Name of the uploaded file
- `sha256`: SHA256 hash of the file

## 🚨 Error Handling

```python
try:
    result = await uploader.upload_file(...)
except Exception as e:
    print(f"Upload failed: {e}")
```

## 🎉 That's It!

**No more filename changes, no more files going to wrong folders, no more complex API calls.**

Just 3 lines to upload a file with proper folder organization and filename preservation!

```python
async with StreamlineFileUploader() as uploader:
    result = await uploader.upload_file(file_content, filename, folder)
    print(f"Done! {result.public_url}")
```
