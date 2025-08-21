"""
Custom exceptions for Stream-Line File Uploader
"""


class StreamlineFileUploaderError(Exception):
    """Base exception for all Stream-Line File Uploader errors"""
    pass


class AuthenticationError(StreamlineFileUploaderError):
    """Raised when authentication fails"""
    pass


class FileServerError(StreamlineFileUploaderError):
    """Raised when the file server returns an error"""
    
    def __init__(self, message: str, status_code: int, response_text: str = ""):
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(f"{message} (Status: {status_code}) - {response_text}")


class UploadError(StreamlineFileUploaderError):
    """Raised when file upload fails"""
    
    def __init__(self, message: str, stage: str = "unknown"):
        self.stage = stage
        super().__init__(f"Upload failed at {stage}: {message}")


class ValidationError(StreamlineFileUploaderError):
    """Raised when input validation fails"""
    pass


class QuotaExceededError(StreamlineFileUploaderError):
    """Raised when user quota is exceeded"""
    pass
