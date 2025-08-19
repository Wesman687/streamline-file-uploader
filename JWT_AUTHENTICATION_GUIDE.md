# 🔐 JWT Authentication for Stream-Line Services

## **How Your Other Programs Get JWT Tokens**

### **Option 1: Service Token Authentication (Recommended for Server-to-Server)**

For **backend services** that don't need user context, use the **service token** directly:

```python
import requests

# Configuration
SERVICE_TOKEN = "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
UPLOAD_SERVER = "https://file-server.stream-lineai.com"

def list_user_files(user_id: str, folder: str = None):
    """List files for a user using service authentication."""
    headers = {"X-Service-Token": SERVICE_TOKEN}
    params = {"user_id": user_id}
    if folder:
        params["folder"] = folder
    
    response = requests.get(f"{UPLOAD_SERVER}/v1/files/all", headers=headers, params=params)
    return response.json()

# Usage
files = list_user_files("user123", "main/pictures")
```

### **Option 2: JWT Token Generation (For User Context)**

When you need **user-specific** JWTs (e.g., for frontend applications), use the JWT generation endpoint:

```python
import requests
import jwt
from datetime import datetime, timedelta

class StreamLineAuthClient:
    def __init__(self, service_token: str, upload_server_url: str):
        self.service_token = service_token
        self.upload_server = upload_server_url
        self.session = requests.Session()
        self.session.headers.update({"X-Service-Token": service_token})
    
    def generate_user_token(self, user_id: str, expires_hours: int = 1) -> dict:
        """Generate a JWT token for a user."""
        response = self.session.post(
            f"{self.upload_server}/v1/files/generate-token",
            params={"user_id": user_id, "expires_hours": expires_hours}
        )
        response.raise_for_status()
        return response.json()
    
    def verify_token(self, token: str) -> dict:
        """Verify a JWT token using the JWKS endpoint."""
        # Get public key from JWKS
        jwks_response = requests.get(f"{self.upload_server}/.well-known/jwks.json")
        jwks = jwks_response.json()
        
        # For production, you'd implement full JWKS verification
        # This is a simplified example
        try:
            # Decode without verification first to get header
            unverified = jwt.decode(token, options={"verify_signature": False})
            return unverified
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")

# Usage Example
auth_client = StreamLineAuthClient(
    service_token="ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340",
    upload_server_url="https://file-server.stream-lineai.com"
)

# Generate token for a user
token_data = auth_client.generate_user_token("user123", expires_hours=2)
user_jwt = token_data["token"]

# Now use this JWT to make authenticated requests
headers = {"Authorization": f"Bearer {user_jwt}"}
response = requests.get(
    "https://file-server.stream-lineai.com/v1/files/all",
    headers=headers
)
```

### **Option 3: Complete Client Library**

Here's a comprehensive client library for your other services:

```python
"""
Stream-Line Upload Server Client Library
Use this in your other Python services to interact with the upload server.
"""

import requests
import jwt
import json
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class UploadServerClient:
    def __init__(self, base_url: str, service_token: str):
        self.base_url = base_url.rstrip('/')
        self.service_token = service_token
        self.session = requests.Session()
        self.session.headers.update({
            "X-Service-Token": service_token,
            "User-Agent": "StreamLine-Service-Client/1.0"
        })
    
    # Service Token Methods (Server-to-Server)
    def list_user_files(self, user_id: str, folder: Optional[str] = None) -> Dict:
        """List all files for a user."""
        params = {"user_id": user_id}
        if folder:
            params["folder"] = folder
        
        response = self.session.get(f"{self.base_url}/v1/files/all", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_file_metadata(self, file_key: str) -> Dict:
        """Get metadata for a specific file."""
        response = self.session.get(f"{self.base_url}/v1/files/metadata/{file_key}")
        response.raise_for_status()
        return response.json()
    
    def delete_file(self, file_key: str) -> bool:
        """Delete a file."""
        response = self.session.delete(f"{self.base_url}/v1/files/{file_key}")
        response.raise_for_status()
        return response.status_code == 200
    
    # JWT Token Management
    def generate_user_token(self, user_id: str, expires_hours: int = 1) -> Dict:
        """Generate a JWT token for a user."""
        response = self.session.post(
            f"{self.base_url}/v1/files/generate-token",
            params={"user_id": user_id, "expires_hours": expires_hours}
        )
        response.raise_for_status()
        return response.json()
    
    def create_user_session(self, user_id: str, expires_hours: int = 1) -> "UserSession":
        """Create a user session with JWT authentication."""
        token_data = self.generate_user_token(user_id, expires_hours)
        return UserSession(self.base_url, token_data["token"], user_id)
    
    # Health and Status
    def health_check(self) -> Dict:
        """Check server health."""
        response = requests.get(f"{self.base_url}/healthz")
        response.raise_for_status()
        return response.json()
    
    def get_jwks(self) -> Dict:
        """Get JSON Web Key Set for token verification."""
        response = requests.get(f"{self.base_url}/.well-known/jwks.json")
        response.raise_for_status()
        return response.json()

class UserSession:
    """User session with JWT authentication for user-specific operations."""
    
    def __init__(self, base_url: str, jwt_token: str, user_id: str):
        self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self.user_id = user_id
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {jwt_token}",
            "User-Agent": "StreamLine-User-Client/1.0"
        })
    
    def list_my_files(self, folder: Optional[str] = None) -> Dict:
        """List files for the authenticated user."""
        params = {}
        if folder:
            params["folder"] = folder
        
        response = self.session.get(f"{self.base_url}/v1/files/all", params=params)
        response.raise_for_status()
        return response.json()
    
    def init_upload(self, filename: str, file_size: int, folder: Optional[str] = None, 
                   mime_type: Optional[str] = None) -> Dict:
        """Initialize a file upload."""
        payload = {
            "mode": "single",
            "files": [{
                "name": filename,
                "size": file_size,
                "mime": mime_type or "application/octet-stream"
            }]
        }
        if folder:
            payload["folder"] = folder
        
        response = self.session.post(f"{self.base_url}/v1/files/init", json=payload)
        response.raise_for_status()
        return response.json()
    
    def complete_upload(self, upload_id: str, filename: str, folder: Optional[str] = None) -> Dict:
        """Complete a file upload."""
        payload = {
            "uploadId": upload_id,
            "meta": {"filename": filename}
        }
        if folder:
            payload["meta"]["folder"] = folder
        
        response = self.session.post(f"{self.base_url}/v1/files/complete", json=payload)
        response.raise_for_status()
        return response.json()

# Example Usage
if __name__ == "__main__":
    # Initialize client
    client = UploadServerClient(
        base_url="https://file-server.stream-lineai.com",
        service_token="ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
    )
    
    # Server-to-server operations
    print("Health:", client.health_check())
    print("User files:", client.list_user_files("test-user"))
    
    # User-specific operations
    user_session = client.create_user_session("test-user", expires_hours=2)
    print("User's files:", user_session.list_my_files())
    
    # Generate token for frontend
    token_data = client.generate_user_token("frontend-user", expires_hours=1)
    print("Frontend token:", token_data["token"])
```

## **Integration Examples**

### **Django/Flask Web App**

```python
# In your Django/Flask app
from your_auth_client import UploadServerClient

# Initialize once in your app
upload_client = UploadServerClient(
    base_url="https://file-server.stream-lineai.com",
    service_token=settings.UPLOAD_SERVICE_TOKEN
)

# In your views
def user_files_view(request):
    user_id = request.user.id
    files = upload_client.list_user_files(user_id, folder="main/pictures")
    return JsonResponse(files)

def generate_upload_token(request):
    user_id = request.user.id
    token_data = upload_client.generate_user_token(user_id, expires_hours=1)
    return JsonResponse(token_data)
```

### **Node.js/Express App**

```javascript
const axios = require('axios');

class UploadServerClient {
    constructor(baseUrl, serviceToken) {
        this.baseUrl = baseUrl;
        this.serviceToken = serviceToken;
        this.client = axios.create({
            baseURL: baseUrl,
            headers: {
                'X-Service-Token': serviceToken
            }
        });
    }
    
    async listUserFiles(userId, folder = null) {
        const params = { user_id: userId };
        if (folder) params.folder = folder;
        
        const response = await this.client.get('/v1/files/all', { params });
        return response.data;
    }
    
    async generateUserToken(userId, expiresHours = 1) {
        const response = await this.client.post('/v1/files/generate-token', null, {
            params: { user_id: userId, expires_hours: expiresHours }
        });
        return response.data;
    }
}

// Usage
const uploadClient = new UploadServerClient(
    'https://file-server.stream-lineai.com',
    'ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340'
);

app.get('/api/user/:userId/files', async (req, res) => {
    try {
        const files = await uploadClient.listUserFiles(req.params.userId);
        res.json(files);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});
```

## **Security Best Practices**

1. **Service Token Security**:
   - Store service token in environment variables
   - Never expose service token to frontend
   - Rotate service token periodically

2. **JWT Usage**:
   - Use short expiration times (1-2 hours)
   - Generate tokens on-demand, don't store them
   - Verify tokens using JWKS endpoint

3. **Network Security**:
   - Always use HTTPS
   - Consider IP whitelisting for service tokens
   - Monitor authentication logs

## **Testing Your Integration**

```bash
# Test service token authentication
curl -H "X-Service-Token: your-service-token" \
     "https://file-server.stream-lineai.com/v1/files/all?user_id=test-user"

# Test JWT generation
curl -X POST -H "X-Service-Token: your-service-token" \
     "https://file-server.stream-lineai.com/v1/files/generate-token?user_id=test-user&expires_hours=1"

# Test JWT usage
JWT_TOKEN="your-generated-jwt"
curl -H "Authorization: Bearer $JWT_TOKEN" \
     "https://file-server.stream-lineai.com/v1/files/all"
```

This gives you **multiple ways** to authenticate your other services with the upload server! 🔐
