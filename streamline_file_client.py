"""
Stream-Line File Server Client Library
=====================================

A Python client library for integrating with the Stream-Line file server.
Use this in your Django, Flask, FastAPI, or any Python application.

Installation:
    pip install requests

Usage:
    from streamline_file_client import StreamLineFileClient
    
    client = StreamLineFileClient("your-service-token")
    result = client.upload_file("user123", "/path/to/file.jpg", "profile_pictures")
    print(f"File available at: {result['public_url']}")
"""

import requests
import json
import base64
import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Union
from pathlib import Path


class StreamLineFileClient:
    """
    Stream-Line File Server Client
    
    A production-ready client for uploading, downloading, and managing files
    with the Stream-Line file server.
    
    Example:
        client = StreamLineFileClient("your-service-token")
        
        # Upload a file
        result = client.upload_file("user123", "/path/to/image.jpg", "profile_pictures")
        
        # Get user's files
        files = client.list_user_files("user123", folder="documents")
        
        # The files are immediately accessible via direct URLs:
        # https://file-server.stream-lineai.com/storage/user123/profile_pictures/image.jpg
    """
    
    def __init__(self, service_token: str, base_url: str = "https://file-server.stream-lineai.com"):
        """
        Initialize the file client.
        
        Args:
            service_token: Your service authentication token
            base_url: File server URL (default: production server)
        """
        self.service_token = service_token
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "X-Service-Token": self.service_token,
            "Content-Type": "application/json"
        }
    
    def upload_file(self, user_id: str, file_path: Union[str, Path], folder: str = None, 
                   metadata: Dict = None) -> Dict:
        """
        Upload a file to the file server.
        
        Args:
            user_id: The user who owns this file
            file_path: Local path to the file to upload
            folder: Optional folder organization (e.g., "documents", "profile_pictures")
            metadata: Optional metadata dictionary
            
        Returns:
            Dict with 'file_key', 'public_url', 'original_name', 'folder'
            
        Example:
            result = client.upload_file("user123", "/tmp/photo.jpg", "profile_pictures")
            # File immediately accessible at result['public_url']
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get file info
        file_name = file_path.name
        file_size = file_path.stat().st_size
        
        # Determine MIME type
        mime_types = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif',
            '.pdf': 'application/pdf', '.txt': 'text/plain', '.csv': 'text/csv',
            '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.avi': 'video/x-msvideo',
            '.mp3': 'audio/mpeg', '.wav': 'audio/wav',
            '.doc': 'application/msword', 
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.zip': 'application/zip'
        }
        file_ext = file_path.suffix.lower()
        mime_type = mime_types.get(file_ext, 'application/octet-stream')
        
        # Step 1: Initialize upload
        init_data = {
            "mode": "single",
            "files": [{
                "name": file_name,
                "size": file_size,
                "mime": mime_type
            }],
            "meta": {
                "user_id": user_id,
                "filename": file_name,
                **(metadata or {})
            }
        }
        
        if folder:
            init_data["folder"] = folder
            
        response = requests.post(
            f"{self.base_url}/v1/files/init",
            headers=self.headers,
            json=init_data
        )
        response.raise_for_status()
        upload_session = response.json()
        upload_id = upload_session["uploadId"]
        
        # Step 2: Upload file data
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Calculate SHA256 for verification
        sha256_hash = hashlib.sha256(file_data).hexdigest()
        
        # Convert to base64 for part upload
        file_b64 = base64.b64encode(file_data).decode('utf-8')
        
        # Upload as single part
        part_data = {
            "uploadId": upload_id,
            "partNumber": 1,
            "chunkBase64": file_b64
        }
        
        response = requests.post(
            f"{self.base_url}/v1/files/part",
            headers=self.headers,
            json=part_data
        )
        response.raise_for_status()
        
        # Step 3: Complete upload
        complete_data = {
            "uploadId": upload_id,
            "sha256": sha256_hash,
            "meta": {
                "user_id": user_id,
                "filename": file_name,
                **(metadata or {})
            }
        }
        
        response = requests.post(
            f"{self.base_url}/v1/files/complete",
            headers=self.headers,
            json=complete_data
        )
        response.raise_for_status()
        result = response.json()
        
        # Construct public URL
        file_key = result["key"]
        # Extract filename from file_key (format: uuid_filename)
        original_filename = '_'.join(file_key.split('_')[1:]) if '_' in file_key else file_name
        
        if folder:
            public_url = f"{self.base_url}/storage/{user_id}/{folder}/{original_filename}"
        else:
            public_url = f"{self.base_url}/storage/{user_id}/{original_filename}"
        
        return {
            "file_key": file_key,
            "public_url": public_url,
            "original_name": file_name,
            "folder": folder,
            "size": result["size"],
            "mime": result["mime"],
            "sha256": result["sha256"]
        }
    
    def list_user_files(self, user_id: str, folder: str = None) -> Dict:
        """
        List all files for a user, optionally filtered by folder.
        
        Args:
            user_id: The user whose files to list
            folder: Optional folder filter
            
        Returns:
            Dict with 'files', 'total_count', 'total_size'
        """
        params = {"user_id": user_id}
        if folder:
            params["folder"] = folder
        
        response = requests.get(
            f"{self.base_url}/v1/files/all",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def delete_file(self, file_key: str) -> bool:
        """
        Delete a file by its key.
        
        Args:
            file_key: The file key to delete
            
        Returns:
            True if successful
        """
        response = requests.delete(
            f"{self.base_url}/v1/files/{file_key}",
            headers=self.headers
        )
        response.raise_for_status()
        return True
    
    def get_health_status(self) -> Dict:
        """Get file server health status."""
        response = requests.get(f"{self.base_url}/healthz")
        response.raise_for_status()
        return response.json()
    
    def test_file_access(self, public_url: str) -> bool:
        """Test if a file is accessible via its public URL."""
        try:
            response = requests.head(public_url, timeout=10)
            return response.status_code == 200
        except:
            return False


class StreamLineFileManager:
    """
    High-level file management for common use cases.
    
    Provides convenient methods for typical application needs like
    profile pictures, document storage, and media management.
    """
    
    def __init__(self, client: StreamLineFileClient):
        self.client = client
    
    def upload_profile_picture(self, user_id: str, image_path: Union[str, Path]) -> str:
        """
        Upload a user's profile picture.
        
        Args:
            user_id: User ID
            image_path: Path to image file
            
        Returns:
            Direct URL to the profile picture
        """
        result = self.client.upload_file(
            user_id=user_id,
            file_path=image_path,
            folder="profile_pictures",
            metadata={"type": "profile_picture", "uploaded_at": datetime.now().isoformat()}
        )
        return result["public_url"]
    
    def upload_document(self, user_id: str, doc_path: Union[str, Path], 
                       doc_type: str = "general") -> Dict:
        """
        Upload a document to organized folders.
        
        Args:
            user_id: User ID
            doc_path: Path to document
            doc_type: Type of document (contract, invoice, receipt, etc.)
            
        Returns:
            Upload result with public_url
        """
        # Organize by document type
        folder_map = {
            "contract": "documents/contracts",
            "invoice": "documents/invoices", 
            "receipt": "documents/receipts",
            "id": "documents/identification",
            "general": "documents"
        }
        
        folder = folder_map.get(doc_type, "documents")
        
        return self.client.upload_file(
            user_id=user_id,
            file_path=doc_path,
            folder=folder,
            metadata={
                "document_type": doc_type,
                "uploaded_at": datetime.now().isoformat()
            }
        )
    
    def upload_media(self, user_id: str, media_path: Union[str, Path], 
                    media_type: str = "general") -> Dict:
        """
        Upload media files (images, videos, audio).
        
        Args:
            user_id: User ID
            media_path: Path to media file
            media_type: Type of media (photos, videos, audio)
            
        Returns:
            Upload result with public_url
        """
        folder_map = {
            "photos": "media/photos",
            "videos": "media/videos",
            "audio": "media/audio",
            "general": "media"
        }
        
        folder = folder_map.get(media_type, "media")
        
        return self.client.upload_file(
            user_id=user_id,
            file_path=media_path,
            folder=folder,
            metadata={
                "media_type": media_type,
                "uploaded_at": datetime.now().isoformat()
            }
        )
    
    def get_user_profile_picture(self, user_id: str) -> Optional[str]:
        """
        Get user's current profile picture URL.
        
        Args:
            user_id: User ID
            
        Returns:
            Profile picture URL or None if not found
        """
        files = self.client.list_user_files(user_id, folder="profile_pictures")
        
        # Get the most recent profile picture
        profile_pics = [f for f in files["files"] if f["mime"].startswith("image/")]
        if profile_pics:
            # Sort by creation date, get most recent
            latest = max(profile_pics, key=lambda x: x["created_at"])
            return f"{self.client.base_url}/storage/{user_id}/profile_pictures/{latest['filename']}"
        
        return None
    
    def get_user_documents(self, user_id: str, doc_type: str = None) -> List[Dict]:
        """
        Get user's documents, optionally filtered by type.
        
        Args:
            user_id: User ID
            doc_type: Optional document type filter
            
        Returns:
            List of document information
        """
        if doc_type:
            folder_map = {
                "contract": "documents/contracts",
                "invoice": "documents/invoices",
                "receipt": "documents/receipts", 
                "id": "documents/identification"
            }
            folder = folder_map.get(doc_type, "documents")
        else:
            folder = "documents"
        
        files = self.client.list_user_files(user_id, folder=folder)
        return files["files"]
    
    def get_user_media(self, user_id: str, media_type: str = None) -> List[Dict]:
        """
        Get user's media files.
        
        Args:
            user_id: User ID  
            media_type: Optional media type filter (photos, videos, audio)
            
        Returns:
            List of media files
        """
        if media_type:
            folder = f"media/{media_type}"
        else:
            folder = "media"
        
        files = self.client.list_user_files(user_id, folder=folder)
        return files["files"]


# Convenience function for quick setup
def create_file_client(service_token: str) -> StreamLineFileClient:
    """
    Create a file client with the production server.
    
    Args:
        service_token: Your service token
        
    Returns:
        Configured StreamLineFileClient
    """
    return StreamLineFileClient(service_token)


def create_file_manager(service_token: str) -> StreamLineFileManager:
    """
    Create a high-level file manager.
    
    Args:
        service_token: Your service token
        
    Returns:
        Configured StreamLineFileManager
    """
    client = StreamLineFileClient(service_token)
    return StreamLineFileManager(client)


# Production service token (you should use environment variables in production)
PRODUCTION_SERVICE_TOKEN = "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"


if __name__ == "__main__":
    # Example usage
    print("Stream-Line File Client Library")
    print("==============================")
    print()
    print("Usage examples:")
    print()
    print("# Basic client")
    print("from streamline_file_client import StreamLineFileClient")
    print("client = StreamLineFileClient('your-service-token')")
    print("result = client.upload_file('user123', '/path/to/file.jpg', 'photos')")
    print("print(f'File URL: {result[\"public_url\"]}')")
    print()
    print("# High-level manager")
    print("from streamline_file_client import StreamLineFileManager")
    print("manager = StreamLineFileManager(client)")
    print("profile_url = manager.upload_profile_picture('user123', '/path/to/avatar.jpg')")
    print("docs = manager.get_user_documents('user123', 'contract')")
