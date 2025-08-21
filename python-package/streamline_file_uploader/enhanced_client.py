"""
Enhanced client for Stream-Line File Uploader with batch operations and file management
"""

import os
import hashlib
import base64
import mimetypes
from typing import Optional, Union, BinaryIO, List, Dict, Any
from pathlib import Path

import httpx

from .models import UploadOptions, UploadResult
from .exceptions import (
    AuthenticationError, 
    FileServerError, 
    UploadError, 
    ValidationError
)


class EnhancedStreamlineFileUploader:
    """
    Enhanced file uploader with batch operations, file search, and management
    
    Features:
    - Single file uploads
    - Batch file uploads
    - File search and filtering
    - File listing and management
    - Download URL generation
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        service_token: Optional[str] = None,
        default_user: Optional[str] = None,
        timeout: float = 30.0
    ):
        """Initialize the enhanced uploader"""
        self.base_url = base_url or os.getenv("UPLOAD_BASE_URL", "https://file-server.stream-lineai.com")
        self.service_token = service_token or os.getenv("AUTH_SERVICE_TOKEN")
        self.default_user = default_user or os.getenv("DEFAULT_USER_ID")
        self.timeout = timeout
        
        if not self.service_token:
            raise AuthenticationError("Service token is required")
        
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def upload_file(
        self,
        file_content: Union[bytes, BinaryIO, str, Path],
        filename: str,
        user_id: Optional[str] = None,
        options: Optional[UploadOptions] = None,
        **kwargs
    ) -> UploadResult:
        """Upload a single file"""
        # Implementation from original client
        pass
    
    async def upload_files_batch(
        self,
        files: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        default_options: Optional[UploadOptions] = None
    ) -> List[UploadResult]:
        """
        Upload multiple files in batch
        
        Args:
            files: List of file dictionaries with:
                   - 'content': File content (bytes, path, or file object)
                   - 'filename': Name of the file
                   - 'folder': Optional folder path
                   - 'options': Optional UploadOptions for this file
            user_id: User ID for uploads
            default_options: Default options for all files
        
        Returns:
            List of UploadResult objects
        """
        if not files:
            return []
        
        results = []
        errors = []
        
        for i, file_info in enumerate(files):
            try:
                content = file_info['content']
                filename = file_info['filename']
                folder = file_info.get('folder')
                file_options = file_info.get('options')
                
                # Merge options
                if file_options is None:
                    file_options = UploadOptions()
                if default_options:
                    for key, value in default_options.dict().items():
                        if value is not None and getattr(file_options, key) is None:
                            setattr(file_options, key, value)
                
                if folder is not None:
                    file_options.folder = folder
                
                result = await self.upload_file(
                    file_content=content,
                    filename=filename,
                    user_id=user_id,
                    options=file_options
                )
                
                results.append(result)
                
            except Exception as e:
                error_msg = f"File {i+1} ({filename}): {str(e)}"
                errors.append(error_msg)
        
        if errors:
            raise UploadError(
                f"Batch upload completed with {len(errors)} errors: {'; '.join(errors)}",
                "batch"
            )
        
        return results
    
    async def list_files(
        self,
        user_id: Optional[str] = None,
        folder: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List files for a user, optionally filtered by folder
        
        Args:
            user_id: User ID to list files for
            folder: Optional folder to filter by
            limit: Optional limit on number of files
        
        Returns:
            List of file dictionaries
        """
        if user_id is None:
            user_id = self.default_user
        
        if not user_id:
            raise ValidationError("user_id is required")
        
        try:
            params = {"user_id": user_id}
            if folder:
                params["folder"] = folder
            
            response = await self.client.get(
                f"{self.base_url}/v1/files/all",
                headers={"X-Service-Token": self.service_token},
                params=params
            )
            
            if response.status_code != 200:
                raise FileServerError(
                    "Failed to list files",
                    response.status_code,
                    response.text
                )
            
            files_data = response.json()
            
            if limit and isinstance(files_data, list):
                files_data = files_data[:limit]
            
            return files_data
            
        except httpx.HTTPStatusError as e:
            raise FileServerError(
                f"HTTP error listing files: {e.response.status_code}",
                e.response.status_code,
                e.response.text
            )
    
    async def search_files(
        self,
        user_id: Optional[str] = None,
        filename_pattern: Optional[str] = None,
        mime_type: Optional[str] = None,
        folder: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search files by various criteria
        
        Args:
            user_id: User ID to search for
            filename_pattern: Pattern to match in filename
            mime_type: MIME type filter
            folder: Folder to search in
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
        
        Returns:
            List of matching files
        """
        all_files = await self.list_files(user_id=user_id, folder=folder)
        
        if not all_files:
            return []
        
        filtered_files = []
        
        for file_info in all_files:
            # Filename pattern filter
            if filename_pattern and filename_pattern.lower() not in file_info.get('filename', '').lower():
                continue
            
            # MIME type filter
            if mime_type and file_info.get('mime_type') != mime_type:
                continue
            
            # Size filters
            file_size = file_info.get('file_size', 0)
            if min_size and file_size < min_size:
                continue
            if max_size and file_size > max_size:
                continue
            
            filtered_files.append(file_info)
        
        return filtered_files
    
    async def get_download_url(self, file_key: str, expires_in: int = 3600) -> str:
        """
        Get a signed download URL for a file
        
        Args:
            file_key: The file key
            expires_in: URL expiration time in seconds
        
        Returns:
            Signed download URL
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/files/signed-url",
                headers={
                    "X-Service-Token": self.service_token,
                    "Content-Type": "application/json"
                },
                json={
                    "file_key": file_key,
                    "expires_in": expires_in
                }
            )
            
            if response.status_code != 200:
                raise FileServerError(
                    "Failed to get signed URL",
                    response.status_code,
                    response.text
                )
            
            data = response.json()
            return data.get("signed_url", "")
            
        except httpx.HTTPStatusError as e:
            raise FileServerError(
                f"HTTP error getting signed URL: {e.response.status_code}",
                e.response.status_code,
                e.response.text
            )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
