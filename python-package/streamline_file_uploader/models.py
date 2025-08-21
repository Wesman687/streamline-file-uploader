"""
Data models for Stream-Line File Uploader
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class UploadOptions(BaseModel):
    """Options for file uploads"""
    
    folder: Optional[str] = Field(
        default=None,
        description="Folder path to upload to (e.g., 'veo/videos', 'documents')"
    )
    mime_type: Optional[str] = Field(
        default=None,
        description="MIME type of the file (auto-detected if not provided)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata to store with the file"
    )
    preserve_filename: bool = Field(
        default=True,
        description="Whether to preserve the original filename"
    )


class UploadResult(BaseModel):
    """Result of a successful file upload"""
    
    file_key: str = Field(description="Unique identifier for the uploaded file")
    public_url: str = Field(description="Public URL to access the file")
    size: int = Field(description="Size of the uploaded file in bytes")
    mime_type: str = Field(description="MIME type of the uploaded file")
    folder: Optional[str] = Field(description="Folder the file was uploaded to")
    filename: str = Field(description="Name of the uploaded file")
    sha256: str = Field(description="SHA256 hash of the uploaded file")
    
    @property
    def download_url(self) -> str:
        """Get the direct download URL"""
        return self.public_url
    
    @property
    def file_id(self) -> str:
        """Get the file ID from the file key"""
        return self.file_key.split('/')[-1].split('_', 1)[-1]
