"""
File management functionality for Stream-Line File Uploader
"""

from typing import List, Dict, Any, Optional
import httpx
from .exceptions import FileServerError, ValidationError, UploadError


class FileManager:
    """Handles file operations like listing, searching, and getting download URLs"""
    
    def __init__(self, uploader):
        self.uploader = uploader
    
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
            user_id = self.uploader.default_user_email
        
        if not user_id:
            raise ValidationError("user_email is required")
        
        try:
            params = {"user_id": user_id}
            if folder:
                params["folder"] = folder
            
            response = await self.uploader.client.get(
                f"{self.uploader.base_url}/v1/files/all",
                headers={"X-Service-Token": self.uploader.service_token},
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
            response = await self.uploader.client.post(
                f"{self.uploader.base_url}/v1/files/signed-url",
                headers={
                    "X-Service-Token": self.uploader.service_token,
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
    
    async def delete_file(self, file_key: str) -> Dict[str, Any]:
        """
        Delete a file from the file server
        
        Args:
            file_key: The file key to delete
        
        Returns:
            Dictionary with deletion status
        """
        try:
            response = await self.uploader.client.delete(
                f"{self.uploader.base_url}/v1/files/{file_key}",
                headers={"X-Service-Token": self.uploader.service_token}
            )
            
            if response.status_code != 200:
                raise FileServerError(
                    "Failed to delete file",
                    response.status_code,
                    response.text
                )
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise FileServerError(
                f"HTTP error deleting file: {e.response.status_code}",
                e.response.status_code,
                e.response.text
            )

    async def get_file_info(self, file_key: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific file
        
        Args:
            file_key: The file key to get info for
        
        Returns:
            File information dictionary
        """
        try:
            # Extract user_id from file_key
            parts = file_key.split('/')
            if len(parts) >= 3:
                user_id = parts[1]
                folder = '/'.join(parts[2:-1]) if len(parts) > 3 else ""
                
                # Search for the file
                files = await self.search_files(
                    user_id=user_id,
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
    
    async def get_folder_stats(self, user_id: str, folder: str = "") -> Dict[str, Any]:
        """
        Get statistics for a folder
        
        Args:
            user_id: User ID
            folder: Folder path (empty for root)
        
        Returns:
            Dictionary with folder statistics
        """
        files = await self.list_files(user_id=user_id, folder=folder)
        
        if not files:
            return {
                "folder": folder,
                "file_count": 0,
                "total_size": 0,
                "mime_types": {},
                "last_modified": None
            }
        
        total_size = sum(f.get('file_size', 0) for f in files)
        mime_types = {}
        last_modified = None
        
        for file_info in files:
            mime = file_info.get('mime_type', 'unknown')
            mime_types[mime] = mime_types.get(mime, 0) + 1
            
            # Track last modified (if available)
            if 'timestamp' in file_info:
                if last_modified is None or file_info['timestamp'] > last_modified:
                    last_modified = file_info['timestamp']
        
        return {
            "folder": folder,
            "file_count": len(files),
            "total_size": total_size,
            "mime_types": mime_types,
            "last_modified": last_modified
        }
