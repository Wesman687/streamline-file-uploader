from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UploadMode(str, Enum):
    SINGLE = "single"
    CHUNKED = "chunked"
    BATCH = "batch"


class Disposition(str, Enum):
    INLINE = "inline"
    ATTACHMENT = "attachment"


class FileInfo(BaseModel):
    name: str
    size: int
    mime: str


class InitUploadRequest(BaseModel):
    mode: UploadMode
    files: List[FileInfo]
    folder: Optional[str] = None  # Optional folder path like "main" or "main/pictures"


class InitUploadResponse(BaseModel):
    uploadId: str
    parts: Optional[int] = None


class UploadPartRequest(BaseModel):
    uploadId: str
    partNumber: int
    chunkBase64: str


class CompleteUploadRequest(BaseModel):
    uploadId: str
    sha256: str
    meta: Optional[Dict[str, Any]] = None


class CompleteUploadResponse(BaseModel):
    key: str
    size: int
    mime: str
    sha256: str


class FileMetadata(BaseModel):
    size: int
    mime: str
    sha256: str
    createdAt: datetime


class SignedUrlRequest(BaseModel):
    key: str
    disposition: Disposition = Disposition.INLINE
    ttl: int = 3600


class BatchDownloadRequest(BaseModel):
    keys: List[str]


class BatchDownloadResponse(BaseModel):
    token: str


class FileListItem(BaseModel):
    key: str
    filename: str
    size: int
    mime: str
    created_at: datetime
    folder: Optional[str] = None


class FileListResponse(BaseModel):
    files: List[FileListItem]
    total_count: int
    total_size: int


class HealthResponse(BaseModel):
    status: str
    disk_free_gb: float
    writable: bool


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
