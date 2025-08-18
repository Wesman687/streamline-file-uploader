import base64
import mimetypes
from typing import Optional


def decode_base64_chunk(chunk_base64: str) -> bytes:
    """Decode base64 chunk data."""
    try:
        return base64.b64decode(chunk_base64)
    except Exception as e:
        raise ValueError(f"Invalid base64 data: {e}")


def guess_mime_type(filename: str) -> str:
    """Guess MIME type from filename."""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def validate_filename(filename: str) -> bool:
    """Validate filename for safety."""
    if not filename or filename.strip() == "":
        return False
    
    # Check for directory traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        return False
    
    # Check for system files
    forbidden_names = ["CON", "PRN", "AUX", "NUL"] + [f"COM{i}" for i in range(1, 10)] + [f"LPT{i}" for i in range(1, 10)]
    if filename.upper() in forbidden_names:
        return False
    
    return True


def get_range_from_header(range_header: str, file_size: int) -> Optional[tuple]:
    """Parse HTTP Range header and return (start, end) tuple."""
    if not range_header.startswith("bytes="):
        return None
    
    range_spec = range_header[6:]  # Remove "bytes="
    
    try:
        if "-" not in range_spec:
            return None
        
        start_str, end_str = range_spec.split("-", 1)
        
        if start_str == "":
            # Suffix range like "-500"
            if end_str == "":
                return None
            suffix_length = int(end_str)
            start = max(0, file_size - suffix_length)
            end = file_size - 1
        elif end_str == "":
            # Prefix range like "500-"
            start = int(start_str)
            end = file_size - 1
        else:
            # Full range like "500-999"
            start = int(start_str)
            end = int(end_str)
        
        # Validate range
        if start < 0 or end >= file_size or start > end:
            return None
        
        return (start, end)
    
    except (ValueError, IndexError):
        return None
