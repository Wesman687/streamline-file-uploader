"""
Main client for Stream-Line File Uploader
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
from .batch import BatchUploader
from .file_manager import FileManager
from .file_lookup import FileLookup


class StreamlineFileUploader:
    """
    Easy-to-use file uploader for Stream-Line file server
    
    Features:
    - Automatic folder organization
    - Preserve original filenames
    - Built-in error handling
    - Async support
    - Automatic MIME type detection
    - Batch uploads
    - File search and management
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        service_token: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize the file uploader
        
        Args:
            base_url: File server base URL (defaults to env var UPLOAD_BASE_URL)
            service_token: Service token for authentication (defaults to env var AUTH_SERVICE_TOKEN)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("UPLOAD_BASE_URL", "https://file-server.stream-lineai.com")
        self.service_token = service_token or os.getenv("AUTH_SERVICE_TOKEN")
        self.timeout = timeout
        
        if not self.service_token:
            raise AuthenticationError("Service token is required. Set AUTH_SERVICE_TOKEN environment variable or pass service_token parameter.")
        
        self.client = httpx.AsyncClient(timeout=timeout)
        
        # Initialize sub-modules
        self.batch = BatchUploader(self)
        self.file_manager = FileManager(self)
        self.lookup = FileLookup(self.file_manager)
    
    async def upload_file(
        self,
        file_content: Union[bytes, BinaryIO, str, Path],
        filename: str,
        user_email: Optional[str] = None,
        options: Optional[UploadOptions] = None,
        **kwargs
    ) -> UploadResult:
        """
        Upload a single file to the Stream-Line file server
        
        Args:
            file_content: File content as bytes, file object, file path, or string path
            filename: Name of the file (will be preserved if options.preserve_filename=True)
            user_email: User email for the upload (required)
            options: Upload options (folder, mime_type, metadata, etc.)
            **kwargs: Additional options (folder, mime_type, metadata, preserve_filename)
        
        Returns:
            UploadResult with file details
            
        Raises:
            UploadError: If upload fails
            AuthenticationError: If authentication fails
            FileServerError: If file server returns an error
        """
        # Merge options
        if options is None:
            options = UploadOptions()
        
        # Override options with kwargs
        for key, value in kwargs.items():
            if hasattr(options, key):
                setattr(options, key, value)
        
        # Set user email
        if not user_email:
            raise ValidationError("user_email is required")
        
        # Prepare file content
        file_bytes, actual_filename, mime_type = self._prepare_file_content(
            file_content, filename, options
        )
        
        try:
            # Step 1: Initialize upload
            init_response = await self.client.post(
                f"{self.base_url}/v1/files/init",
                headers={
                    "X-Service-Token": self.service_token,
                    "Content-Type": "application/json"
                },
                json={
                    "mode": "single",
                    "files": [{
                        "name": actual_filename,
                        "size": len(file_bytes),
                        "mime": mime_type
                    }],
                    "meta": {
                        "user_id": user_email
                    },
                    "folder": options.folder
                }
            )
            
            if init_response.status_code != 200:
                raise FileServerError(
                    "Failed to initialize upload",
                    init_response.status_code,
                    init_response.text
                )
            
            init_data = init_response.json()
            upload_id = init_data["uploadId"]
            
            # Step 2: Upload file content
            file_b64 = base64.b64encode(file_bytes).decode('utf-8')
            file_hash = hashlib.sha256(file_bytes).hexdigest()
            
            part_response = await self.client.post(
                f"{self.base_url}/v1/files/part",
                headers={
                    "X-Service-Token": self.service_token,
                    "Content-Type": "application/json"
                },
                json={
                    "uploadId": upload_id,
                    "partNumber": 0,
                    "chunkBase64": file_b64
                }
            )
            
            if part_response.status_code != 200:
                raise FileServerError(
                    "Failed to upload file part",
                    part_response.status_code,
                    part_response.text
                )
            
            # Step 3: Complete upload
            complete_response = await self.client.post(
                f"{self.base_url}/v1/files/complete",
                headers={
                    "X-Service-Token": self.service_token,
                    "Content-Type": "application/json"
                },
                json={
                    "uploadId": upload_id,
                    "parts": [{"data": file_b64}],
                    "sha256": file_hash,
                    "meta": {
                        "user_id": user_email,
                        "folder": options.folder,
                        "filename": actual_filename,
                        **(options.metadata or {})
                    }
                }
            )
            
            if complete_response.status_code != 200:
                raise FileServerError(
                    "Failed to complete upload",
                    complete_response.status_code,
                    complete_response.text
                )
            
            complete_data = complete_response.json()
            
            # Build public URL
            public_url = f"{self.base_url}/storage/{user_email}"
            if options.folder:
                public_url += f"/{options.folder}"
            public_url += f"/{actual_filename}"
            
            return UploadResult(
                file_key=complete_data["key"],
                public_url=public_url,
                size=len(file_bytes),
                mime_type=mime_type,
                folder=options.folder,
                filename=actual_filename,
                sha256=file_hash
            )
            
        except httpx.HTTPStatusError as e:
            raise FileServerError(
                f"HTTP error during upload: {e.response.status_code}",
                e.response.status_code,
                e.response.text
            )
        except httpx.RequestError as e:
            raise UploadError(f"Network error during upload: {str(e)}", "network")
        except Exception as e:
            if isinstance(e, (UploadError, FileServerError, AuthenticationError)):
                raise
            raise UploadError(f"Unexpected error during upload: {str(e)}", "unknown")
    
    async def upload_files(
        self,
        files: List[Dict[str, Union[bytes, BinaryIO, str, Path]]],
        user_email: str,
        default_options: Optional[UploadOptions] = None
    ) -> List[UploadResult]:
        """
        Upload multiple files in batch
        
        Args:
            files: List of file dictionaries with keys:
                   - 'content': File content (bytes, file object, path, or string)
                   - 'filename': Name of the file
                   - 'folder': Optional folder path
                   - 'options': Optional UploadOptions for this file
            user_email: User email for the uploads (required)
            default_options: Default options applied to all files
        
        Returns:
            List of UploadResult objects
            
        Raises:
            UploadError: If any upload fails
        """
        if not files:
            return []
        
        results = []
        errors = []
        
        for i, file_info in enumerate(files):
            try:
                # Extract file info
                content = file_info['content']
                filename = file_info['filename']
                folder = file_info.get('folder')
                file_options = file_info.get('options')
                
                # Merge options
                if file_options is None:
                    file_options = UploadOptions()
                if default_options:
                    # Merge default options with file-specific options
                    for key, value in default_options.dict().items():
                        if value is not None and getattr(file_options, key) is None:
                            setattr(file_options, key, value)
                
                # Override folder if specified in file_info
                if folder is not None:
                    file_options.folder = folder
                
                # Upload single file
                result = await self.upload_file(
                    file_content=content,
                    filename=filename,
                    user_email=user_email,
                    options=file_options
                )
                
                results.append(result)
                
            except Exception as e:
                error_msg = f"File {i+1} ({filename}): {str(e)}"
                errors.append(error_msg)
                # Continue with other files
        
        if errors:
            raise UploadError(
                f"Batch upload completed with {len(errors)} errors: {'; '.join(errors)}",
                "batch"
            )
        
        return results
    
    async def list_files(
        self,
        user_email: str,
        folder: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List files for a user, optionally filtered by folder
        
        Args:
            user_email: User email to list files for (required)
            folder: Optional folder to filter by
            limit: Optional limit on number of files returned
        
        Returns:
            List of file dictionaries with metadata
        """
        if not user_email:
            raise ValidationError("user_email is required")
        
        try:
            params = {"user_id": user_email}
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
            
            # Apply limit if specified
            if limit and isinstance(files_data, list):
                files_data = files_data[:limit]
            
            return files_data
            
        except httpx.HTTPStatusError as e:
            raise FileServerError(
                f"HTTP error listing files: {e.response.status_code}",
                e.response.status_code,
                e.response.text
            )
        except httpx.RequestError as e:
            raise UploadError(f"Network error listing files: {str(e)}", "network")
    
    async def search_files(
        self,
        user_email: str,
        filename_pattern: Optional[str] = None,
        mime_type: Optional[str] = None,
        folder: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search files by various criteria
        
        Args:
            user_email: User email to search for (required)
            filename_pattern: Pattern to match in filename
            mime_type: MIME type filter
            folder: Folder to search in
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
        
        Returns:
            List of matching files
        """
        all_files = await self.list_files(user_email=user_email, folder=folder)
        
        if not all_files:
            return []
        
        # Apply filters
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
    
    async def get_file_info(self, file_key: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific file
        
        Args:
            file_key: The file key to get info for
        
        Returns:
            File information dictionary
        """
        try:
            # Try to get file info from the file server
            # This might need to be implemented on the server side
            # For now, we'll search through user files
            
            # Extract user_id from file_key
            parts = file_key.split('/')
            if len(parts) >= 3:
                user_id = parts[1]
                folder = '/'.join(parts[2:-1]) if len(parts) > 3 else ""
                
                # Search for the file
                files = await self.search_files(
                    user_email=user_id,
                    folder=folder,
                    filename_pattern=parts[-1].split('_', 1)[-1] if '_' in parts[-1] else parts[-1]
                )
                
                if files:
                    return files[0]
            
            raise FileServerError(f"File not found: {file_key}", 404)
            
        except Exception as e:
            if isinstance(e, FileServerError):
                raise
            raise UploadError(f"Error getting file info: {str(e)}", "info")
    
    async def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from the server
        
        Args:
            file_key: The file key to delete
        
        Returns:
            True if deletion was successful
        
        Raises:
            FileServerError: If deletion fails
        """
        try:
            # This endpoint needs to be implemented on the file server
            # For now, we'll raise an error indicating it's not implemented
            
            # TODO: Implement when file server supports deletion
            raise FileServerError(
                "File deletion not yet implemented on the file server",
                501
            )
            
        except Exception as e:
            if isinstance(e, FileServerError):
                raise
            raise UploadError(f"Error deleting file: {str(e)}", "delete")
    
    async def get_download_url(self, file_key: str, expires_in: int = 3600) -> str:
        """
        Get a signed download URL for a file
        
        Args:
            file_key: The file key to get download URL for
            expires_in: URL expiration time in seconds (default: 1 hour)
        
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
        except httpx.RequestError as e:
            raise UploadError(f"Network error getting signed URL: {str(e)}", "network")
    
    def _prepare_file_content(
        self, 
        file_content: Union[bytes, BinaryIO, str, Path], 
        filename: str,
        options: UploadOptions
    ) -> tuple[bytes, str, str]:
        """Prepare file content for upload"""
        
        # Handle different input types
        if isinstance(file_content, bytes):
            file_bytes = file_content
        elif isinstance(file_content, (str, Path)):
            # File path
            file_path = Path(file_content)
            if not file_path.exists():
                raise ValidationError(f"File not found: {file_content}")
            file_bytes = file_path.read_bytes()
            # Use actual filename if not provided
            if filename == "unknown":
                filename = file_path.name
        elif hasattr(file_content, 'read'):
            # File-like object
            file_bytes = file_content.read()
        else:
            raise ValidationError(f"Unsupported file content type: {type(file_content)}")
        
        # Determine filename
        actual_filename = filename if options.preserve_filename else "uploaded_file"
        
        # Determine MIME type
        if options.mime_type:
            mime_type = options.mime_type
        else:
            mime_type, _ = mimetypes.guess_type(actual_filename)
            if not mime_type:
                mime_type = "application/octet-stream"
        
        return file_bytes, actual_filename, mime_type
    
    # Convenience methods for batch operations
    async def upload_files(
        self,
        files: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        default_options: Optional[UploadOptions] = None
    ) -> List[UploadResult]:
        """Convenience method for batch uploads"""
        return await self.batch.upload_files(files, user_id, default_options)
    
    async def list_files(
        self,
        user_id: Optional[str] = None,
        folder: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Convenience method for listing files"""
        return await self.file_manager.list_files(user_id, folder, limit)
    
    async def search_files(
        self,
        user_id: Optional[str] = None,
        filename_pattern: Optional[str] = None,
        mime_type: Optional[str] = None,
        folder: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Convenience method for searching files"""
        return await self.file_manager.search_files(
            user_id, filename_pattern, mime_type, folder, min_size, max_size
        )
    
    async def get_download_url(self, file_key: str, expires_in: int = 3600) -> str:
        """Convenience method for getting download URLs"""
        return await self.file_manager.get_download_url(file_key, expires_in)
    
    async def get_file_info(self, file_key: str) -> Dict[str, Any]:
        """Convenience method for getting file info"""
        return await self.file_manager.get_file_info(file_key)
    
    async def get_folder_stats(self, user_email: str, folder: str = "") -> Dict[str, Any]:
        """
        Get statistics for a folder
        
        Args:
            user_email: User email (required)
            folder: Folder path (empty for root)
        
        Returns:
            Dictionary with folder statistics
        """
        return await self.file_manager.get_folder_stats(user_email, folder)
    
    async def delete_file(self, file_key: str) -> Dict[str, Any]:
        """Convenience method for deleting files"""
        return await self.file_manager.delete_file(file_key)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
