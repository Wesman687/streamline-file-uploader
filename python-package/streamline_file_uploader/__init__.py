"""
Stream-Line File Uploader

A simple, powerful file uploader for Stream-Line file server with automatic folder organization.
"""

from .client import StreamlineFileUploader
from .models import UploadResult, UploadOptions
from .exceptions import UploadError, AuthenticationError, FileServerError, ValidationError, QuotaExceededError
from .file_manager import FileManager
from .batch import BatchUploader

__version__ = "1.0.4"
__author__ = "Stream-Line AI"
__email__ = "support@stream-lineai.com"

__all__ = [
    "StreamlineFileUploader",
    "UploadResult", 
    "UploadOptions",
    "UploadError",
    "AuthenticationError",
    "FileServerError",
    "ValidationError",
    "QuotaExceededError",
    "FileManager",
    "BatchUploader",
]


