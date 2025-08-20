# 📦 Stream-Line File Client MVP
## How to Use Your Existing File Server

Your file server is already running. This is just the **client library** to connect your applications to it.

---

## 🚀 **Quick Start (Copy & Paste)**

### **1. Download Client Library**
```bash
# Download the client (do this once)
wget https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/streamline_file_client.py
```

### **2. Basic Usage**
```python
from streamline_file_client import StreamLineFileClient

# Connect to YOUR file server (replace with your actual server URL)
client = StreamLineFileClient(
    service_token="ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340",
    base_url="https://your-domain.com"  # Your server URL
)

# Upload a file
result = client.upload_file(
    user_id="user123",
    file_path="/path/to/local/file.jpg", 
    folder="profile_pictures"
)

print(f"✅ File uploaded!")
print(f"📁 Server path: {result['key']}")
print(f"🌐 Public URL: {result['public_url']}")
print(f"📋 File info: {result['metadata']}")
```

### **3. Result**
```python
{
    'key': 'storage/user123/profile_pictures/file-abc123.jpg',
    'public_url': 'https://your-domain.com/storage/user123/profile_pictures/file-abc123.jpg',
    'metadata': {
        'size': 1024000,
        'mime': 'image/jpeg',
        'filename': 'file.jpg'
    }
}
```

---

## 🎯 **File Organization on Your Server**

Files are stored at: `/home/ubuntu/file-uploader/storage/`

```
storage/
├── user123/
│   ├── profile_pictures/
│   │   └── avatar-abc123.jpg
│   ├── documents/
│   │   └── report-def456.pdf
│   └── uploads/
│       └── file-ghi789.txt
└── user456/
    └── media/
        └── video-jkl012.mp4
```

**Direct URLs:**
- `https://your-domain.com/storage/user123/profile_pictures/avatar-abc123.jpg`
- `https://your-domain.com/storage/user123/documents/report-def456.pdf`

---

## 📋 **Framework Examples**

### **Django**
```python
# views.py
from django.shortcuts import render
from streamline_file_client import StreamLineFileClient

client = StreamLineFileClient("your-token", "https://your-domain.com")

def upload_profile_picture(request):
    if request.method == 'POST' and request.FILES['avatar']:
        # Save uploaded file temporarily
        uploaded_file = request.FILES['avatar']
        temp_path = f"/tmp/{uploaded_file.name}"
        
        with open(temp_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Upload to file server
        result = client.upload_file(
            user_id=str(request.user.id),
            file_path=temp_path,
            folder="profile_pictures"
        )
        
        # Save URL to user model
        request.user.profile.avatar_url = result['public_url']
        request.user.profile.save()
        
        # Clean up temp file
        os.unlink(temp_path)
        
        return render(request, 'success.html', {'file_url': result['public_url']})
```

### **Flask**
```python
from flask import Flask, request, render_template
from streamline_file_client import StreamLineFileClient

app = Flask(__name__)
client = StreamLineFileClient("your-token", "https://your-domain.com")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            # Save temporarily
            temp_path = f"/tmp/{file.filename}"
            file.save(temp_path)
            
            # Upload to server
            result = client.upload_file(
                user_id=session.get('user_id', 'anonymous'),
                file_path=temp_path,
                folder="uploads"
            )
            
            # Clean up
            os.unlink(temp_path)
            
            return render_template('success.html', file_url=result['public_url'])
```

### **FastAPI**
```python
from fastapi import FastAPI, UploadFile, File
from streamline_file_client import StreamLineFileClient

app = FastAPI()
client = StreamLineFileClient("your-token", "https://your-domain.com")

@app.post("/upload/")
async def upload_file(user_id: str, folder: str, file: UploadFile = File(...)):
    # Save temporarily
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Upload to server
    result = client.upload_file(
        user_id=user_id,
        file_path=temp_path,
        folder=folder
    )
    
    # Clean up
    os.unlink(temp_path)
    
    return {
        "message": "File uploaded successfully",
        "url": result['public_url'],
        "metadata": result['metadata']
    }
```

### **Express.js (Node.js)**
```javascript
// You'll need a Node.js equivalent, but the concept is:
const axios = require('axios');
const FormData = require('form-data');

async function uploadFile(userId, filePath, folder) {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    
    const response = await axios.post(
        `https://your-domain.com/api/upload/${userId}/${folder}`,
        form,
        {
            headers: {
                ...form.getHeaders(),
                'Authorization': 'Bearer your-token'
            }
        }
    );
    
    return response.data;
}
```

---

## 🔧 **Configuration**

### **Environment Variables**
```python
import os

# config.py
FILE_SERVER_URL = os.getenv('FILE_SERVER_URL', 'https://your-domain.com')
FILE_SERVER_TOKEN = os.getenv('FILE_SERVER_TOKEN', 'your-token')

# Usage
client = StreamLineFileClient(FILE_SERVER_TOKEN, FILE_SERVER_URL)
```

### **Settings File**
```python
# settings.py
STREAMLINE_CONFIG = {
    'url': 'https://your-domain.com',
    'token': 'your-token',
    'default_folder': 'uploads',
    'allowed_types': ['jpg', 'png', 'pdf', 'txt']
}
```

---

## 🧪 **Testing Your Connection**

```python
# test_connection.py
from streamline_file_client import StreamLineFileClient

def test_server_connection():
    client = StreamLineFileClient("your-token", "https://your-domain.com")
    
    try:
        # Test with a small text file
        test_file = "/tmp/test.txt"
        with open(test_file, 'w') as f:
            f.write("Test file")
        
        result = client.upload_file("test_user", test_file, "tests")
        print(f"✅ Connection successful!")
        print(f"📁 File URL: {result['public_url']}")
        
        # Clean up
        os.unlink(test_file)
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_server_connection()
```

---

## 📋 **All You Need**

1. **✅ File server is already running** (this repository)
2. **📥 Download client library**: `streamline_file_client.py`
3. **🔗 Use your server URL**: `https://your-domain.com`
4. **🔑 Use your service token**: From your server config
5. **💻 Copy examples above** into your applications

**That's it! Your apps can now upload files to your existing server.** 🎉
