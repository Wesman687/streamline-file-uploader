# Stream-Line File Uploader

A simple, powerful Python package for uploading files to the Stream-Line file server with automatic folder organization and filename preservation.

## 🚀 Features

- **Easy to use**: Simple API that handles all the complexity
- **Folder organization**: Automatically organize files into folders
- **Filename preservation**: Keep your original filenames
- **Async support**: Built for modern Python async applications
- **Error handling**: Comprehensive error handling with custom exceptions
- **Flexible input**: Accept bytes, file paths, or file objects
- **Auto MIME detection**: Automatically detect file types
- **Environment config**: Easy configuration via environment variables
- **Batch uploads**: Upload multiple files at once
- **File search**: Find files by filename, type, size, or folder
- **File management**: List, search, and get download URLs
- **Folder statistics**: Get file counts and size information

## 📦 Installation

```bash
pip install streamline-file-uploader
```

## 🔧 Quick Start

### Basic Usage

```python
import asyncio
from streamline_file_uploader import StreamlineFileUploader

async def main():
    # Initialize uploader
    uploader = StreamlineFileUploader(
        service_token="your-service-token",
        default_user="user@example.com"
    )
    
    # Upload a file
    result = await uploader.upload_file(
        file_content=b"Hello, World!",
        filename="hello.txt",
        folder="documents"
    )
    
    print(f"File uploaded: {result.public_url}")
    print(f"File key: {result.file_key}")
    print(f"File size: {result.size} bytes")
    
    await uploader.close()

asyncio.run(main())
```

### Environment Variables

Set these environment variables for easy configuration:

```bash
export UPLOAD_BASE_URL="https://file-server.stream-lineai.com"
export AUTH_SERVICE_TOKEN="your-service-token"
export DEFAULT_USER_ID="user@example.com"
```

Then use the uploader without parameters:

```python
uploader = StreamlineFileUploader()  # Uses environment variables
```

### Upload to Specific Folders

```python
# Upload to veo/videos folder
result = await uploader.upload_file(
    file_content=video_bytes,
    filename="my_video.mp4",
    folder="veo/videos",
    user_id="user@example.com"
)

# Upload to documents/invoices folder
result = await uploader.upload_file(
    file_content=invoice_bytes,
    filename="invoice_2024.pdf",
    folder="documents/invoices"
)
```

### Upload from File Path

```python
# Upload from file path
result = await uploader.upload_file(
    file_content="/path/to/video.mp4",
    filename="video.mp4",
    folder="veo/videos"
)
```

### Upload with Metadata

```python
from streamline_file_uploader import UploadOptions

options = UploadOptions(
    folder="veo/videos",
    metadata={
        "category": "tutorial",
        "tags": ["python", "coding"],
        "description": "Python tutorial video"
    }
)

result = await uploader.upload_file(
    file_content=video_bytes,
    filename="tutorial.mp4",
    options=options
)
```

### Context Manager Usage

```python
async with StreamlineFileUploader() as uploader:
    result = await uploader.upload_file(
        file_content=file_bytes,
        filename="file.txt",
        folder="documents"
    )
    # Uploader automatically closes
```

## 📚 API Reference

### StreamlineFileUploader

#### Constructor

```python
StreamlineFileUploader(
    base_url: Optional[str] = None,
    service_token: Optional[str] = None,
    default_user: Optional[str] = None,
    timeout: float = 30.0
)
```

#### Methods

##### upload_file()

```python
async def upload_file(
    self,
    file_content: Union[bytes, BinaryIO, str, Path],
    filename: str,
    user_id: Optional[str] = None,
    options: Optional[UploadOptions] = None,
    **kwargs
) -> UploadResult
```

Upload a file to the Stream-Line file server.

**Parameters:**
- `file_content`: File content as bytes, file object, file path, or string path
- `filename`: Name of the file
- `user_id`: User ID for the upload (defaults to default_user)
- `options`: Upload options object
- `**kwargs`: Additional options (folder, mime_type, metadata, preserve_filename)

**Returns:**
- `UploadResult` object with file details

### UploadOptions

```python
class UploadOptions:
    folder: Optional[str] = None          # Folder path (e.g., "veo/videos")
    mime_type: Optional[str] = None      # MIME type (auto-detected if not provided)
    metadata: Optional[Dict[str, Any]]   # Additional metadata
    preserve_filename: bool = True        # Whether to preserve original filename
```

### UploadResult

```python
class UploadResult:
    file_key: str        # Unique identifier for the uploaded file
    public_url: str      # Public URL to access the file
    size: int            # Size of the uploaded file in bytes
    mime_type: str       # MIME type of the uploaded file
    folder: Optional[str] # Folder the file was uploaded to
    filename: str        # Name of the uploaded file
    sha256: str          # SHA256 hash of the uploaded file
    
    # Properties
    download_url: str    # Direct download URL
    file_id: str         # File ID extracted from file key
```

## 🚨 Error Handling

The package provides custom exceptions for different error scenarios:

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
```

## 🔍 Examples

### Upload Video Files

```python
async def upload_video(video_path: str, user_id: str):
    async with StreamlineFileUploader() as uploader:
        result = await uploader.upload_file(
            file_content=video_path,
            filename=Path(video_path).name,
            folder="veo/videos",
            user_id=user_id
        )
        return result

# Usage
result = await upload_video("/path/to/video.mp4", "user@example.com")
print(f"Video uploaded to: {result.public_url}")
```

### Upload Multiple Files

```python
async def upload_multiple_files(files: list, user_id: str):
    async with StreamlineFileUploader() as uploader:
        results = []
        for file_path in files:
            result = await uploader.upload_file(
                file_content=file_path,
                filename=Path(file_path).name,
                folder="documents",
                user_id=user_id
            )
            results.append(result)
        return results

# Usage
files = ["doc1.pdf", "doc2.docx", "doc3.txt"]
results = await upload_multiple_files(files, "user@example.com")
```

### Upload with Custom Metadata

```python
async def upload_with_metadata(file_content: bytes, filename: str, user_id: str):
    options = UploadOptions(
        folder="projects/assets",
        metadata={
            "project_id": "proj_123",
            "asset_type": "image",
            "tags": ["logo", "branding"],
            "created_by": user_id
        }
    )
    
    async with StreamlineFileUploader() as uploader:
        result = await uploader.upload_file(
            file_content=file_content,
            filename=filename,
            options=options,
            user_id=user_id
        )
        return result
```

## 🧪 Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=streamline_file_uploader

# Lint code
ruff check .

# Format code
black .
```

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/streamline-ai/file-uploader/issues)
- **Documentation**: [GitHub README](https://github.com/streamline-ai/file-uploader#readme)
- **Email**: support@stream-lineai.com

## 🔗 Related

- [Stream-Line File Server](https://file-server.stream-lineai.com)
- [Stream-Line AI](https://stream-lineai.com)
