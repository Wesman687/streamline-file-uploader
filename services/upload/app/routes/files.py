import base64
import os
from typing import Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.security import HTTPAuthorizationCredentials

from app.models import (
    InitUploadRequest, InitUploadResponse, UploadPartRequest,
    CompleteUploadRequest, CompleteUploadResponse, FileMetadata,
    SignedUrlRequest, BatchDownloadRequest, BatchDownloadResponse,
    HealthResponse, ErrorResponse, Disposition, FileListResponse, FileListItem
)
from app.security.jwt import get_current_user, get_auth_user_or_service, bearer_scheme
from app.core.storage import storage_manager
from app.core.signer import url_signer
from app.core.zipper import zip_streamer
from app.utils import decode_base64_chunk, guess_mime_type, validate_filename, get_range_from_header

router = APIRouter(prefix="/v1/files")


@router.post("/init", response_model=InitUploadResponse)
async def init_upload(
    request: InitUploadRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Initialize a file upload session."""
    user_id = user["user_id"]
    
    # Check user quota
    used_bytes, quota_bytes = storage_manager.check_user_quota(user_id)
    
    # Calculate total size of new files
    total_new_size = sum(file_info.size for file_info in request.files)
    
    if used_bytes + total_new_size > quota_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Upload would exceed quota. Used: {used_bytes}, Quota: {quota_bytes}, Requested: {total_new_size}"
        )
    
    # Validate filenames
    for file_info in request.files:
        if not validate_filename(file_info.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename: {file_info.name}"
            )
    
    upload_id = str(uuid4())
    
    if request.mode == "chunked":
        # Create upload session for chunked upload
        session_metadata = [file_info.dict() for file_info in request.files]
        if request.folder:
            session_metadata.append({"folder": request.folder})
        
        await storage_manager.create_upload_session(
            upload_id,
            session_metadata
        )
        
        # For chunked uploads, estimate number of parts (assuming 1MB chunks)
        chunk_size = 1024 * 1024  # 1MB
        max_file_size = max(file_info.size for file_info in request.files)
        parts = (max_file_size + chunk_size - 1) // chunk_size
        
        return InitUploadResponse(uploadId=upload_id, parts=parts)
    
    return InitUploadResponse(uploadId=upload_id)


@router.post("/part")
async def upload_part(
    request: UploadPartRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Upload a chunk for chunked upload."""
    try:
        chunk_data = decode_base64_chunk(request.chunkBase64)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    try:
        await storage_manager.store_chunk(
            request.uploadId,
            request.partNumber,
            chunk_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return {"status": "success", "partNumber": request.partNumber}


@router.post("/complete", response_model=CompleteUploadResponse)
async def complete_upload(
    request: CompleteUploadRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Complete an upload and finalize the file."""
    user_id = user["user_id"]
    
    # Generate file key with folder support
    filename = request.meta.get("filename", "uploaded_file") if request.meta else "uploaded_file"
    folder = request.meta.get("folder", "") if request.meta else ""
    file_key = storage_manager.generate_file_key(user_id, filename, folder)
    
    try:
        # Assemble chunks into final file
        file_path, calculated_sha256 = await storage_manager.assemble_chunks(
            request.uploadId,
            file_key
        )
        
        # Verify SHA256 if provided
        if request.sha256 and request.sha256 != calculated_sha256:
            # Clean up the file
            await storage_manager.delete_file(file_key)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SHA256 mismatch"
            )
        
        # Store metadata
        file_size = file_path.stat().st_size
        mime_type = guess_mime_type(filename)
        
        metadata = {
            "original_name": filename,
            "mime": mime_type,
            "sha256": calculated_sha256,
            "user_id": user_id,
            **(request.meta or {})
        }
        
        await storage_manager.store_file_metadata(file_key, metadata)
        
        return CompleteUploadResponse(
            key=file_key,
            size=file_size,
            mime=mime_type,
            sha256=calculated_sha256
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/signed-url")
async def get_signed_url(
    key: str,
    disposition: Disposition = Disposition.INLINE,
    ttl: int = 3600,
    user_or_service: Optional[Dict[str, Any]] = Depends(get_auth_user_or_service)
):
    """Generate a signed URL for file access."""
    # Check if file exists
    metadata = await storage_manager.get_file_metadata(key)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # If user authentication (not service), check ownership
    if user_or_service is not None:
        file_user_id = metadata.get("user_id")
        if file_user_id and file_user_id != user_or_service["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Generate signed URL
    signed_url = url_signer.sign_url(key, ttl)
    
    return {
        "url": signed_url,
        "expires_in": ttl,
        "disposition": disposition
    }


@router.get("/all", response_model=FileListResponse)
async def list_all_files(
    folder: Optional[str] = None,
    user_id: Optional[str] = None,
    user_or_service: Optional[Dict[str, Any]] = Depends(get_auth_user_or_service)
):
    """List all files for the authenticated user, optionally filtered by folder."""
    # Determine the user_id to use
    if user_or_service is None:
        # Service authentication - use provided user_id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service authentication requires user_id parameter"
            )
        effective_user_id = user_id
    else:
        # User authentication - use authenticated user's ID
        effective_user_id = user_or_service["user_id"]
        # Ignore any provided user_id parameter for security
    
    # Get all files for the user
    files_data = await storage_manager.list_user_files(effective_user_id, folder)
    
    # Convert to response format
    files = [
        FileListItem(
            key=file_data["key"],
            filename=file_data["filename"],
            size=file_data["size"],
            mime=file_data["mime"],
            created_at=file_data["created_at"],
            folder=file_data["folder"]
        )
        for file_data in files_data
    ]
    
    total_size = sum(file_data["size"] for file_data in files_data)
    
    return FileListResponse(
        files=files,
        total_count=len(files),
        total_size=total_size
    )


@router.get("/metadata/{key}", response_model=FileMetadata)
async def get_file_metadata(
    key: str,
    user_or_service: Optional[Dict[str, Any]] = Depends(get_auth_user_or_service)
):
    """Get file metadata."""
    metadata = await storage_manager.get_file_metadata(key)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # If user authentication (not service), check ownership
    if user_or_service is not None:
        file_user_id = metadata.get("user_id")
        if file_user_id and file_user_id != user_or_service["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return FileMetadata(
        size=metadata["size"],
        mime=metadata["mime"],
        sha256=metadata["sha256"],
        createdAt=metadata["createdAt"]
    )


@router.post("/batch-download", response_model=BatchDownloadResponse)
async def create_batch_download(
    request: BatchDownloadRequest,
    user_or_service: Optional[Dict[str, Any]] = Depends(get_auth_user_or_service)
):
    """Create a batch download token."""
    # Verify all files exist and user has access
    for key in request.keys:
        metadata = await storage_manager.get_file_metadata(key)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {key}"
            )
        
        # If user authentication (not service), check ownership
        if user_or_service is not None:
            file_user_id = metadata.get("user_id")
            if file_user_id and file_user_id != user_or_service["user_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: {key}"
                )
    
    token = zip_streamer.generate_batch_token(request.keys)
    
    return BatchDownloadResponse(token=token)


@router.get("/batch-download/{token}")
async def download_batch(token: str):
    """Download files as a ZIP archive."""
    try:
        keys = zip_streamer.get_batch_keys(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    # Generate filename
    filename = zip_streamer.get_zip_filename(keys)
    
    # Estimate content length
    estimated_size = await zip_streamer.get_zip_size_estimate(keys)
    
    # Stream the ZIP file
    return StreamingResponse(
        zip_streamer.stream_zip(keys),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(estimated_size)
        }
    )


@router.delete("/{key}")
async def delete_file(
    key: str,
    user_or_service: Optional[Dict[str, Any]] = Depends(get_auth_user_or_service)
):
    """Delete a file."""
    metadata = await storage_manager.get_file_metadata(key)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # If user authentication (not service), check ownership
    if user_or_service is not None:
        file_user_id = metadata.get("user_id")
        if file_user_id and file_user_id != user_or_service["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    deleted = await storage_manager.delete_file(key)
    
    if deleted:
        return {"status": "deleted", "key": key}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )


@router.get("/get/{encoded_key}")
async def serve_file(
    encoded_key: str,
    request: Request,
    exp: int,
    sig: str
):
    """Serve a file via signed URL."""
    try:
        # Decode the file key
        key = url_signer.decode_key_from_url(encoded_key)
        
        # Verify signature
        if not url_signer.verify_signature(key, exp, sig):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired signature"
            )
        
        # Check if file exists
        file_path = storage_manager.get_file_path(key)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Get metadata
        metadata = await storage_manager.get_file_metadata(key)
        mime_type = metadata.get("mime", "application/octet-stream") if metadata else "application/octet-stream"
        
        # Handle range requests
        range_header = request.headers.get("range")
        file_size = file_path.stat().st_size
        
        if range_header:
            range_spec = get_range_from_header(range_header, file_size)
            if range_spec:
                start, end = range_spec
                
                def iter_range():
                    with open(file_path, 'rb') as f:
                        f.seek(start)
                        remaining = end - start + 1
                        while remaining > 0:
                            chunk_size = min(8192, remaining)
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            remaining -= len(chunk)
                            yield chunk
                
                headers = {
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(end - start + 1)
                }
                
                return StreamingResponse(
                    iter_range(),
                    status_code=206,
                    media_type=mime_type,
                    headers=headers
                )
        
        # Return full file
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size)
        }
        
        return FileResponse(
            file_path,
            media_type=mime_type,
            headers=headers
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    disk_usage = storage_manager.get_disk_usage()
    writable = storage_manager.is_writable()
    
    status_code = "healthy" if writable and disk_usage["free_gb"] > 1 else "unhealthy"
    
    return HealthResponse(
        status=status_code,
        disk_free_gb=disk_usage["free_gb"],
        writable=writable
    )
