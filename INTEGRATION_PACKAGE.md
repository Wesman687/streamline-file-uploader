# Stream-Line File Server Integration Package

This package contains everything you need to integrate your Python applications with the Stream-Line file server.

## 📦 What's Included

- **`streamline_file_client.py`** - Main client library (copy this to your project)
- **`integration_examples/`** - Framework-specific examples
  - `django_example.py` - Complete Django integration
  - `flask_example.py` - Complete Flask integration  
  - `fastapi_example.py` - Complete FastAPI integration
  - `generic_example.py` - Generic Python usage
- **`FILE_SERVER_INTEGRATION_GUIDE.md`** - Comprehensive documentation

## 🚀 Quick Start (2 minutes)

### 1. Copy the Client Library
```bash
# Copy to your project
cp streamline_file_client.py /path/to/your/project/
```

### 2. Install Dependencies
```bash
pip install requests
```

### 3. Use in Your Code
```python
from streamline_file_client import StreamLineFileClient

client = StreamLineFileClient("ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340")
result = client.upload_file("user123", "/path/to/file.jpg", "profile_pictures")
print(f"File available at: {result['public_url']}")
```

## 🔑 Production Service Token

Use this service token in your applications:
```
ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340
```

**Security Note**: Store this in environment variables in production:
```python
import os
SERVICE_TOKEN = os.getenv('STREAMLINE_FILE_TOKEN')
```

## 🌐 File Server URL

Production server: `https://file-server.stream-lineai.com`

## 📋 Common Integration Patterns

### User Profile Pictures
```python
from streamline_file_client import StreamLineFileManager

manager = StreamLineFileManager(client)
profile_url = manager.upload_profile_picture("user123", "/tmp/avatar.jpg")

# Store in your database
user.profile_picture_url = profile_url
user.save()
```

### Document Management
```python
# Upload contract
doc = manager.upload_document("user123", "/tmp/contract.pdf", "contract")

# Store in database
Document.objects.create(
    user_id="user123",
    file_key=doc['file_key'],
    public_url=doc['public_url'],
    document_type="contract"
)
```

### Direct File Access (No Auth Required)
```html
<!-- Immediate file access in HTML -->
<img src="https://file-server.stream-lineai.com/storage/user123/profile_pictures/avatar.jpg">
<a href="https://file-server.stream-lineai.com/storage/user123/documents/contract.pdf" download>Download</a>
```

## 🏗️ Framework Integration

### Django
- See `integration_examples/django_example.py`
- Includes models, views, templates, and JavaScript
- Ready-to-use upload endpoints

### Flask  
- See `integration_examples/flask_example.py`
- Complete API endpoints with HTML test page
- Simple authentication example

### FastAPI
- See `integration_examples/fastapi_example.py` 
- Pydantic models and async endpoints
- OpenAPI/Swagger documentation

### Generic Python
- See `integration_examples/generic_example.py`
- Works with any Python application
- Batch operations and database patterns

## 🗄️ Database Integration

Store URLs in your database, not files:

```sql
-- User profiles
CREATE TABLE user_profiles (
    user_id VARCHAR(50) PRIMARY KEY,
    profile_picture_url VARCHAR(500),
    updated_at TIMESTAMP
);

-- Documents
CREATE TABLE user_documents (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    file_key VARCHAR(255),
    public_url VARCHAR(500),
    original_name VARCHAR(255),
    document_type VARCHAR(20),
    file_size INTEGER,
    uploaded_at TIMESTAMP
);
```

## ✅ File Server Status

- **URL**: https://file-server.stream-lineai.com
- **Status**: ✅ Live and operational  
- **SSL**: ✅ Let's Encrypt certificate
- **Authentication**: ✅ Service tokens working
- **Storage**: ✅ 55+ GB available
- **Upload Workflow**: ✅ All endpoints working

## 🔧 Testing Your Integration

1. **Health Check**:
   ```python
   health = client.get_health_status()
   print(health)  # Should show server status
   ```

2. **Upload Test**:
   ```python
   result = client.upload_file("test-user", "/path/to/file.jpg")
   print(result['public_url'])  # Should return a URL
   ```

3. **Access Test**:
   ```python
   accessible = client.test_file_access(result['public_url'])
   print(accessible)  # Should be True
   ```

## 🚨 Important Notes

1. **Service Token**: Use the provided token for server-to-server uploads
2. **File URLs**: Store the public URLs in your database
3. **No Auth for Access**: Files are publicly accessible once uploaded
4. **File Organization**: Use folders for organization (profile_pictures, documents, etc.)
5. **Error Handling**: Always wrap uploads in try/catch blocks

## 📞 Support

If you have issues:
1. Check the examples in `integration_examples/`
2. Review the full documentation in `FILE_SERVER_INTEGRATION_GUIDE.md`
3. Test with the MVP: `python3 file_server_mvp.py`

## 🎯 Ready to Deploy

The file server is production-ready! Your applications can start uploading files immediately using the patterns in this package.

**No more 422 errors - everything is working!** 🎉
