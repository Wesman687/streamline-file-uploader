# 📖 Stream-Line File Server - Complete Integration Guide

## 🚀 **Getting Started with Stream-Line File Server**

Your file server is live at: **https://file-server.stream-lineai.com**

This guide shows exactly how your applications should integrate with the file server for uploads, downloads, and file management.

## 🔐 **Authentication Methods**

### **Option 1: Service Token (Recommended for Server-to-Server)**

Use this for your backend services that need to manage files on behalf of users:

```bash
curl -H "X-Service-Token: ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340" \
     "https://file-server.stream-lineai.com/v1/files/all?user_id=user123"
```

### **Option 2: JWT Token (For User Context)**

Use this when you have user sessions and want proper user authentication:

```bash
curl -H "Authorization: Bearer <jwt-token>" \
     "https://file-server.stream-lineai.com/v1/files/all"
```

## 📁 **Core Use Cases & Examples**

### **1. Upload Files**

#### **Simple File Upload (Most Common)**

```python
import requests
import json

def upload_file_to_stream_line(user_id: str, file_path: str, folder: str = None):
    """Upload a file to Stream-Line file server."""
    
    # Step 1: Initialize upload
    init_data = {
        "mode": "single",
        "files": [{
            "name": "my-document.pdf",
            "size": 1024000,  # File size in bytes
            "mime": "application/pdf"
        }]
    }
    
    if folder:
        init_data["folder"] = folder  # e.g., "documents" or "main/pictures"
    
    response = requests.post(
        "https://file-server.stream-lineai.com/v1/files/init",
        headers={
            "X-Service-Token": "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340",
            "Content-Type": "application/json"
        },
        json=init_data
    )
    
    upload_session = response.json()
    upload_id = upload_session["uploadId"]
    
    # Step 2: Upload the file data
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    # Convert to base64 for API
    import base64
    file_b64 = base64.b64encode(file_data).decode('utf-8')
    
    complete_data = {
        "uploadId": upload_id,
        "parts": [{"data": file_b64}],
        "meta": {"user_id": user_id}
    }
    
    response = requests.post(
        "https://file-server.stream-lineai.com/v1/files/complete",
        headers={
            "X-Service-Token": "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340",
            "Content-Type": "application/json"
        },
        json=complete_data
    )
    
    result = response.json()
    return {
        "file_key": result["fileKey"],
        "public_url": f"https://file-server.stream-lineai.com/storage/{user_id}/{folder}/{result['fileKey'].split('_', 1)[1]}" if folder else f"https://file-server.stream-lineai.com/storage/{user_id}/{result['fileKey'].split('_', 1)[1]}"
    }

# Usage
result = upload_file_to_stream_line(
    user_id="user123",
    file_path="/path/to/document.pdf",
    folder="documents"
)
print(f"File uploaded! Access at: {result['public_url']}")
```

### **2. List User's Files**

```python
def get_user_files(user_id: str, folder: str = None):
    """Get all files for a user, optionally filtered by folder."""
    
    params = {"user_id": user_id}
    if folder:
        params["folder"] = folder
    
    response = requests.get(
        "https://file-server.stream-lineai.com/v1/files/all",
        headers={
            "X-Service-Token": "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
        },
        params=params
    )
    
    return response.json()

# Examples
all_files = get_user_files("user123")
pictures = get_user_files("user123", folder="main/pictures")
documents = get_user_files("user123", folder="documents")
```

### **3. Direct File Access (No API Needed)**

Once uploaded, files are directly accessible via clean URLs:

```python
# These URLs work immediately after upload - no API calls needed!

# User's profile picture
profile_pic = f"https://file-server.stream-lineai.com/storage/user123/main/pictures/profile.jpg"

# User's documents
document = f"https://file-server.stream-lineai.com/storage/user123/documents/contract.pdf"

# User's videos (supports streaming!)
video = f"https://file-server.stream-lineai.com/storage/user123/videos/tutorial.mp4"

# Use these URLs directly in your HTML, apps, etc.
html = f'<img src="{profile_pic}" alt="Profile">'
html = f'<video src="{video}" controls></video>'
```

### **4. File Organization**

Organize files into logical folders:

```python
# Examples of good folder organization
folders = {
    "profile_pictures": "main/pictures",
    "documents": "documents", 
    "videos": "videos",
    "temp_files": "temp",
    "shared_files": "shared",
    "project_assets": "projects/project1/assets"
}

# Upload to specific folders
upload_file_to_stream_line("user123", "/path/to/profile.jpg", "main/pictures")
upload_file_to_stream_line("user123", "/path/to/contract.pdf", "documents")
upload_file_to_stream_line("user123", "/path/to/video.mp4", "videos")
```

## 🛠️ **Integration Patterns for Your Apps**

### **Pattern 1: User Profile Pictures**

```python
def set_user_profile_picture(user_id: str, image_file_path: str):
    """Upload and set a user's profile picture."""
    
    result = upload_file_to_stream_line(
        user_id=user_id,
        file_path=image_file_path,
        folder="main/pictures"
    )
    
    # Save the public URL in your user database
    profile_url = result["public_url"]
    
    # Update user record in your database
    # user.profile_picture_url = profile_url
    # user.save()
    
    return profile_url

# Usage in your app
new_pic_url = set_user_profile_picture("user123", "/tmp/uploaded_image.jpg")
```

### **Pattern 2: Document Storage**

```python
def store_user_document(user_id: str, document_file: str, document_type: str):
    """Store a user document with proper organization."""
    
    folder_mapping = {
        "contract": "documents/contracts",
        "invoice": "documents/invoices", 
        "receipt": "documents/receipts",
        "id_document": "documents/identification"
    }
    
    folder = folder_mapping.get(document_type, "documents")
    
    result = upload_file_to_stream_line(
        user_id=user_id,
        file_path=document_file,
        folder=folder
    )
    
    return {
        "document_url": result["public_url"],
        "file_key": result["file_key"],
        "folder": folder
    }
```

### **Pattern 3: Video/Media Streaming**

```python
def upload_video_for_streaming(user_id: str, video_file: str, title: str):
    """Upload a video that will be streamable."""
    
    result = upload_file_to_stream_line(
        user_id=user_id,
        file_path=video_file,
        folder="videos"
    )
    
    # The video URL supports HTTP range requests for streaming
    streaming_url = result["public_url"]
    
    # Save to your media database
    # media_record = {
    #     "user_id": user_id,
    #     "title": title,
    #     "streaming_url": streaming_url,
    #     "file_key": result["file_key"]
    # }
    
    return streaming_url
```

## 🔄 **Complete Workflow Examples**

### **Workflow 1: User Registration with Profile Picture**

```python
def register_user_with_picture(user_data: dict, profile_image_path: str):
    """Complete user registration workflow with profile picture."""
    
    # 1. Create user in your system
    user_id = create_user_in_database(user_data)
    
    # 2. Upload profile picture to file server
    if profile_image_path:
        profile_result = upload_file_to_stream_line(
            user_id=str(user_id),
            file_path=profile_image_path,
            folder="main/pictures"
        )
        
        # 3. Update user record with profile picture URL
        update_user_profile_picture(user_id, profile_result["public_url"])
    
    return user_id
```

### **Workflow 2: Document Management System**

```python
def create_document_library(user_id: str):
    """Create a complete document management system."""
    
    # Get user's existing documents
    documents = get_user_files(user_id, folder="documents")
    
    # Organize by subfolder
    doc_library = {
        "contracts": get_user_files(user_id, folder="documents/contracts"),
        "invoices": get_user_files(user_id, folder="documents/invoices"),
        "receipts": get_user_files(user_id, folder="documents/receipts"),
        "other": get_user_files(user_id, folder="documents")
    }
    
    return doc_library

def add_document_to_library(user_id: str, file_path: str, doc_type: str, metadata: dict):
    """Add a document to user's organized library."""
    
    result = store_user_document(user_id, file_path, doc_type)
    
    # Save document metadata in your database
    # document_record = {
    #     "user_id": user_id,
    #     "file_key": result["file_key"],
    #     "public_url": result["document_url"],
    #     "document_type": doc_type,
    #     "folder": result["folder"],
    #     "metadata": metadata,
    #     "uploaded_at": datetime.now()
    # }
    
    return result
```

## 📱 **Frontend Integration Examples**

### **HTML/JavaScript (Direct File Display)**

```html
<!-- Profile Picture -->
<img src="https://file-server.stream-lineai.com/storage/user123/main/pictures/profile.jpg" 
     alt="Profile Picture"
     onerror="this.src='/default-avatar.png'">

<!-- Document Download Link -->
<a href="https://file-server.stream-lineai.com/storage/user123/documents/contract.pdf" 
   download="contract.pdf">
   Download Contract
</a>

<!-- Video Player with Streaming -->
<video controls width="100%">
    <source src="https://file-server.stream-lineai.com/storage/user123/videos/tutorial.mp4" 
            type="video/mp4">
    Your browser does not support video playback.
</video>

<!-- Image Gallery -->
<div id="gallery"></div>
<script>
async function loadUserGallery(userId) {
    const response = await fetch(`/api/user/${userId}/pictures`); // Your API endpoint
    const pictures = await response.json();
    
    const gallery = document.getElementById('gallery');
    pictures.forEach(pic => {
        const img = document.createElement('img');
        img.src = `https://file-server.stream-lineai.com/storage/${userId}/main/pictures/${pic.filename}`;
        img.style.width = '200px';
        img.style.margin = '10px';
        gallery.appendChild(img);
    });
}
</script>
```

### **React Component Example**

```jsx
import React, { useState, useEffect } from 'react';

function UserMediaGallery({ userId }) {
    const [media, setMedia] = useState([]);
    
    useEffect(() => {
        // Fetch user's media files from your API
        fetch(`/api/users/${userId}/media`)
            .then(res => res.json())
            .then(files => setMedia(files));
    }, [userId]);
    
    return (
        <div className="media-gallery">
            {media.map(file => (
                <div key={file.file_key} className="media-item">
                    {file.mime.startsWith('image/') ? (
                        <img 
                            src={`https://file-server.stream-lineai.com/storage/${userId}/${file.folder}/${file.filename}`}
                            alt={file.original_name}
                            style={{ maxWidth: '200px' }}
                        />
                    ) : file.mime.startsWith('video/') ? (
                        <video 
                            src={`https://file-server.stream-lineai.com/storage/${userId}/${file.folder}/${file.filename}`}
                            controls
                            style={{ maxWidth: '300px' }}
                        />
                    ) : (
                        <a 
                            href={`https://file-server.stream-lineai.com/storage/${userId}/${file.folder}/${file.filename}`}
                            download={file.original_name}
                        >
                            📄 {file.original_name}
                        </a>
                    )}
                </div>
            ))}
        </div>
    );
}
```

## 🏗️ **Architecture Recommendations**

### **In Your Main Application Database**

Store file references, not the files themselves:

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255),
    email VARCHAR(255),
    profile_picture_url TEXT,  -- Points to file server
    created_at TIMESTAMP
);

-- User documents table
CREATE TABLE user_documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    file_key VARCHAR(255),     -- File server key
    public_url TEXT,           -- Direct file server URL
    original_name VARCHAR(255),
    document_type VARCHAR(100),
    folder VARCHAR(255),
    uploaded_at TIMESTAMP
);

-- User media table
CREATE TABLE user_media (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    file_key VARCHAR(255),
    public_url TEXT,
    media_type VARCHAR(50),    -- 'image', 'video', 'audio'
    folder VARCHAR(255),
    metadata JSONB,            -- Additional metadata
    created_at TIMESTAMP
);
```

### **API Endpoints in Your Application**

```python
# Your application's API endpoints

@app.route('/api/users/<user_id>/upload-picture', methods=['POST'])
def upload_user_picture(user_id):
    """Handle profile picture upload."""
    file = request.files['picture']
    
    # Save temporarily
    temp_path = f"/tmp/{file.filename}"
    file.save(temp_path)
    
    # Upload to file server
    result = upload_file_to_stream_line(user_id, temp_path, "main/pictures")
    
    # Update user record
    user = User.query.get(user_id)
    user.profile_picture_url = result["public_url"]
    db.session.commit()
    
    # Clean up temp file
    os.remove(temp_path)
    
    return {"profile_url": result["public_url"]}

@app.route('/api/users/<user_id>/documents', methods=['GET'])
def get_user_documents(user_id):
    """Get user's documents from file server."""
    documents = get_user_files(user_id, folder="documents")
    return documents

@app.route('/api/users/<user_id>/media', methods=['GET'])
def get_user_media(user_id):
    """Get user's media files."""
    pictures = get_user_files(user_id, folder="main/pictures")
    videos = get_user_files(user_id, folder="videos")
    
    return {
        "pictures": pictures["files"],
        "videos": videos["files"]
    }
```

## 🎯 **Best Practices**

### **1. File Organization**
- Use consistent folder structures across your apps
- Group related files together
- Use descriptive folder names

### **2. Error Handling**
```python
def safe_upload(user_id: str, file_path: str, folder: str = None):
    """Upload with proper error handling."""
    try:
        result = upload_file_to_stream_line(user_id, file_path, folder)
        return {"success": True, "data": result}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Upload failed: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
```

### **3. File Validation**
```python
def validate_file_before_upload(file_path: str, max_size_mb: int = 50):
    """Validate file before uploading."""
    import os
    
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    file_size = os.path.getsize(file_path)
    if file_size > max_size_mb * 1024 * 1024:
        return False, f"File too large (max {max_size_mb}MB)"
    
    return True, "Valid"
```

### **4. Caching Strategy**
```python
# Cache file listings to reduce API calls
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def cached_get_user_files(user_id: str, folder: str, cache_time: int):
    """Cache file listings for 5 minutes."""
    return get_user_files(user_id, folder)

def get_cached_user_files(user_id: str, folder: str = None):
    # Cache for 5 minutes
    cache_key = int(time.time() / 300)  # 300 seconds = 5 minutes
    return cached_get_user_files(user_id, folder, cache_key)
```

---

This documentation shows exactly how your applications should integrate with the file server. The key points:

1. **Use service tokens** for server-to-server communication
2. **Store file URLs** in your database, not the files themselves  
3. **Use direct URLs** for displaying files (no API calls needed)
4. **Organize files** into logical folders
5. **Handle errors** gracefully

Would you like me to create a specific MVP example for one of your use cases?
