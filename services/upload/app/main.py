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
from app.middleware.logging import LoggingMiddleware
from app.core.logging import app_logger, error_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Startup
    app_logger.info("Starting Upload Server...")
    
    # Ensure storage directory exists
    storage_manager.upload_root.mkdir(parents=True, exist_ok=True)
    
    # Log startup completion
    app_logger.info("Upload Server started successfully!")
    
    yield
    
    # Shutdown
    app_logger.info("Upload Server shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Stream-Line Upload Server",
    description="Production file upload and management service",
    version="1.0.0",
    lifespan=lifespan
)

# Add logging middleware (first, to catch all requests)
app.add_middleware(LoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create FastAPI app
app = FastAPI(
    title="Stream-Line Upload Server",
    description="File upload and management service for Stream-Line customers",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    print(f"Unhandled exception: {type(exc).__name__}: {exc}")
    
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


# Direct file serving from storage paths
@app.get("/storage/{user_id}/{file_path:path}")
@app.head("/storage/{user_id}/{file_path:path}")
async def serve_storage_file(user_id: str, file_path: str, request: Request):
    """Serve files directly from storage paths."""
    from app.core.logging import log_download
    
    # Get client info
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    try:
        # Construct the full file key
        full_key = f"storage/{user_id}/{file_path}"
        
        # Log the file access
        log_download(user_id, full_key, client_ip, user_agent)
        
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
    
    port = int(os.getenv("PORT", "5070"))
    host = os.getenv("BIND_HOST", "127.0.0.1")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,  # Production mode, no auto-reload
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
