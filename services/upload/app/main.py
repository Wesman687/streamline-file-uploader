import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
from cryptography.hazmat.primitives import serialization
import base64

from app.routes.files import router as files_router
from app.core.storage import storage_manager
from app.utils import get_range_from_header
from app.logging_config import server_logger, error_logger
from app.middleware.access_logging import AccessLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    server_logger.info("Starting Upload Server...")
    server_logger.info("Upload Server started successfully!")
    yield
    # Shutdown
    server_logger.info("Upload Server shutting down...")


app = FastAPI(
    title="Stream-Line Upload Server",
    description="File upload and management service for Stream-Line customers",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(AccessLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(files_router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    error_logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    server_logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred"
        }
    )


# Include routers
app.include_router(files_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Stream-Line Upload Server",
        "version": "1.0.0",
        "status": "running"
    }


# Instructions endpoint
@app.get("/instructions")
async def get_instructions(request: Request):
    """Get integration instructions for developers."""
    base_url = "https://file-server.stream-lineai.com"  # Your production domain
    
    return {
        "service": "Stream-Line Upload Server",
        "version": "1.0.0",
        "description": "File upload and management service for Stream-Line AI applications",
        "server": "file-server.stream-lineai.com",
        "base_url": base_url,
        
        "🔑 authentication": {
            "service_token": "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340",
            "method": "Bearer Token",
            "header": "Authorization: Bearer ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
        },
        
        "🌐 endpoints": {
            "health": f"{base_url}/healthz",
            "instructions": f"{base_url}/instructions",
            "api_docs": f"{base_url}/docs",
            "upload": f"{base_url}/api/files/upload/{{user_id}}/{{folder}}",
            "file_access": f"{base_url}/storage/{{user_id}}/{{folder}}/{{filename}}",
            "file_list": f"{base_url}/api/files/{{user_id}}/list"
        },
        
        "🚀 quick_start": {
            "1_download_client": f"curl -o streamline_file_client.py {base_url.replace('file-server', 'raw.githubusercontent.com/Wesman687/streamline-file-uploader/main')}/streamline_file_client.py",
            
            "2_python_usage": f'''
from streamline_file_client import StreamLineFileClient

# Initialize client
client = StreamLineFileClient(
    service_token="ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340",
    base_url="{base_url}"
)

# Upload file
result = client.upload_file("user123", "/path/to/file.jpg", "profile_pics")
print(f"File URL: {{result['public_url']}}")
# Result: {base_url}/storage/user123/profile_pics/filename.jpg

# List files
files = client.list_files("user123")
print(f"User has {{len(files)}} files")
''',
            
            "3_direct_curl": f'''
# Upload with curl
curl -X POST "{base_url}/api/files/upload/user123/uploads" \\
  -H "Authorization: Bearer ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340" \\
  -F "file=@/path/to/your/file.jpg"
            
# Health check
curl {base_url}/healthz
''',
            
            "4_javascript": f'''
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('{base_url}/api/files/upload/user123/uploads', {{
    method: 'POST',
    headers: {{
        'Authorization': 'Bearer ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340'
    }},
    body: formData
}});

const result = await response.json();
console.log('File URL:', result.public_url);
// Display: <img src="{{result.public_url}}" alt="Uploaded" />
'''
        },
        
        "📁 file_organization": {
            "pattern": "storage/{user_id}/{folder}/{filename}",
            "examples": [
                f"{base_url}/storage/user123/profile_pics/avatar.jpg",
                f"{base_url}/storage/user123/documents/contract.pdf",
                f"{base_url}/storage/app1_user456/uploads/screenshot.png",
                f"{base_url}/storage/customer789/invoices/invoice_2025.pdf"
            ],
            "note": "Files are immediately accessible via direct URLs after upload"
        },
        
        "🔧 framework_integration": {
            "django": f'''
# settings.py
FILE_SERVER_URL = "{base_url}"
FILE_SERVER_TOKEN = "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"

# views.py
from streamline_file_client import StreamLineFileClient

def upload_file(request):
    client = StreamLineFileClient(settings.FILE_SERVER_TOKEN, settings.FILE_SERVER_URL)
    result = client.upload_file(request.user.id, request.FILES['file'], 'uploads')
    return JsonResponse({{'url': result['public_url']}})
''',
            
            "flask": f'''
from streamline_file_client import StreamLineFileClient

app.config['FILE_SERVER_URL'] = '{base_url}'
app.config['FILE_SERVER_TOKEN'] = 'ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340'

@app.route('/upload', methods=['POST'])
def upload():
    client = StreamLineFileClient(app.config['FILE_SERVER_TOKEN'], app.config['FILE_SERVER_URL'])
    result = client.upload_file(session['user_id'], request.files['file'], 'uploads')
    return {{'url': result['public_url']}}
''',
            
            "nodejs_express": f'''
const FILE_SERVER_URL = '{base_url}';
const SERVICE_TOKEN = 'ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340';

app.post('/upload', upload.single('file'), async (req, res) => {{
    const formData = new FormData();
    formData.append('file', req.file.buffer, req.file.originalname);
    
    const response = await axios.post(`${{FILE_SERVER_URL}}/api/files/upload/${{req.user.id}}/uploads`, formData, {{
        headers: {{
            'Authorization': `Bearer ${{SERVICE_TOKEN}}`,
            ...formData.getHeaders()
        }}
    }});
    
    res.json({{url: response.data.public_url}});
}});
'''
        },
        
        "🧪 testing": {
            "health_check": f"curl {base_url}/healthz",
            "test_upload": f'curl -X POST "{base_url}/api/files/upload/test_user/test_folder" -H "Authorization: Bearer ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340" -F "file=@test.jpg"',
            "test_access": f"curl {base_url}/storage/test_user/test_folder/test.jpg"
        },
        
        "📖 documentation": {
            "interactive_api": f"{base_url}/docs",
            "openapi_spec": f"{base_url}/openapi.json",
            "this_endpoint": f"{base_url}/instructions"
        },
        
        "💡 tips": [
            "Use descriptive folder names for better organization",
            "User IDs can be anything (user123, app1_user456, customer789, etc.)",
            "Files are immediately accessible after upload",
            "Use the /healthz endpoint to check server status",
            f"Visit {base_url}/docs for interactive API testing",
            "All uploads require the service token in Authorization header"
        ]
    }


# Direct file serving from storage paths
@app.get("/storage/{user_id}/{file_path:path}")
@app.head("/storage/{user_id}/{file_path:path}")
async def serve_storage_file(user_id: str, file_path: str, request: Request):
    """Serve files directly from storage paths."""
    import json
    import time
    from app.logging_config import activity_logger
    
    # Get client info
    client_ip = request.client.host if request.client else "unknown"
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    elif "x-real-ip" in request.headers:
        client_ip = request.headers["x-real-ip"]
    
    user_agent = request.headers.get("user-agent", "")
    
    try:
        # Construct the full file key
        full_key = f"storage/{user_id}/{file_path}"
        
        # Log the file access
        log_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "action": "file_download",
            "user_id": user_id,
            "client_ip": client_ip,
            "file_key": full_key,
            "details": {
                "user_agent": user_agent,
                "method": request.method,
                "file_path": file_path
            }
        }
        activity_logger.info(json.dumps(log_data))
        
        # Get the actual file path
        actual_file_path = storage_manager.get_file_path(full_key)
        
        # Check if file exists
        if not actual_file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        # Get file metadata
        metadata = await storage_manager.get_file_metadata(full_key)
        mime_type = metadata.get("mime", "application/octet-stream") if metadata else "application/octet-stream"
        
        # Handle range requests for video/audio streaming
        range_header = request.headers.get("range")
        file_size = actual_file_path.stat().st_size
        
        if range_header:
            range_spec = get_range_from_header(range_header, file_size)
            if range_spec:
                start, end = range_spec
                
                def iter_range():
                    with open(actual_file_path, 'rb') as f:
                        f.seek(start)
                        remaining = end - start + 1
                        while remaining > 0:
                            chunk_size = min(8192, remaining)
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            remaining -= len(chunk)
                            yield chunk
                
                from fastapi.responses import StreamingResponse
                headers = {
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(end - start + 1),
                    "Content-Type": mime_type
                }
                
                return StreamingResponse(
                    iter_range(),
                    status_code=206,
                    headers=headers
                )
        
        # Return full file
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": mime_type
        }
        
        return FileResponse(
            actual_file_path,
            headers=headers
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error serving file: {str(e)}"
        )


@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    try:
        # Check if storage is writable
        writable = storage_manager.is_writable()
        
        # Check available disk space
        import shutil
        total, used, free = shutil.disk_usage(storage_manager.upload_root)
        free_gb = free / (1024**3)
        
        return {
            "status": "healthy",
            "disk_free_gb": round(free_gb, 2),
            "writable": writable
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


# JWKS endpoint for JWT public key discovery
@app.get("/.well-known/jwks.json")
async def jwks():
    """JSON Web Key Set endpoint for JWT public key discovery."""
    try:
        # Load public key
        public_key_path = os.getenv("JWT_PUBLIC_KEY_PATH")
        if not public_key_path or not Path(public_key_path).exists():
            raise HTTPException(
                status_code=503,
                detail="JWT public key not available"
            )
        
        # Read public key
        with open(public_key_path, 'rb') as f:
            public_key = serialization.load_pem_public_key(f.read())
        
        # Convert to JWK format
        public_numbers = public_key.public_numbers()
        
        # Get the key ID
        kid = os.getenv("JWKS_KID", "streamline-rsa-1")
        
        # Convert RSA numbers to base64url format
        def int_to_base64url(num):
            # Convert to bytes
            byte_length = (num.bit_length() + 7) // 8
            bytes_val = num.to_bytes(byte_length, 'big')
            # Base64url encode
            return base64.urlsafe_b64encode(bytes_val).decode('ascii').rstrip('=')
        
        jwk = {
            "kty": "RSA",
            "use": "sig",
            "kid": kid,
            "alg": "RS256",
            "n": int_to_base64url(public_numbers.n),
            "e": int_to_base64url(public_numbers.e)
        }
        
        return {"keys": [jwk]}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating JWKS: {str(e)}"
        )


# Health check (also available at /v1/files/healthz)
@app.get("/healthz")
async def health():
    """Simple health check."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "10000"))
    # Default to 0.0.0.0 for Docker compatibility, allow override for security
    host = os.getenv("BIND_HOST", "0.0.0.0")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,  # Production mode, no auto-reload
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
