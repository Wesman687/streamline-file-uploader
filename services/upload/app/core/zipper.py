import asyncio
import zipfile
import tempfile
import os
from typing import List, AsyncGenerator
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta

from app.core.storage import storage_manager


class ZipStreamer:
    def __init__(self):
        self.batch_tokens = {}  # In-memory store for batch tokens
        self.token_ttl = 3600  # 1 hour TTL for batch tokens

    def generate_batch_token(self, keys: List[str]) -> str:
        """Generate a batch download token."""
        token = str(uuid4())
        expires_at = datetime.utcnow() + timedelta(seconds=self.token_ttl)
        
        self.batch_tokens[token] = {
            "keys": keys,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        }
        
        # Clean up expired tokens
        self._cleanup_expired_tokens()
        
        return token

    def _cleanup_expired_tokens(self):
        """Remove expired tokens from memory."""
        now = datetime.utcnow()
        expired_tokens = [
            token for token, data in self.batch_tokens.items()
            if data["expires_at"] < now
        ]
        
        for token in expired_tokens:
            del self.batch_tokens[token]

    def get_batch_keys(self, token: str) -> List[str]:
        """Get keys associated with a batch token."""
        self._cleanup_expired_tokens()
        
        if token not in self.batch_tokens:
            raise ValueError("Invalid or expired batch token")
        
        return self.batch_tokens[token]["keys"]

    async def stream_zip(self, keys: List[str]) -> AsyncGenerator[bytes, None]:
        """Stream a ZIP file containing the specified files."""
        # Create a temporary file for the ZIP
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Create ZIP file
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for key in keys:
                    file_path = storage_manager.get_file_path(key)
                    
                    if file_path.exists():
                        # Get original filename from metadata or use key
                        metadata = await storage_manager.get_file_metadata(key)
                        if metadata and "original_name" in metadata:
                            archive_name = metadata["original_name"]
                        else:
                            archive_name = Path(key).name
                        
                        # Ensure unique names in archive
                        counter = 1
                        original_archive_name = archive_name
                        while archive_name in [info.filename for info in zip_file.infolist()]:
                            name, ext = os.path.splitext(original_archive_name)
                            archive_name = f"{name}_{counter}{ext}"
                            counter += 1
                        
                        zip_file.write(file_path, archive_name)

            # Stream the ZIP file
            chunk_size = 8192
            with open(temp_path, 'rb') as zip_file:
                while True:
                    chunk = zip_file.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except OSError:
                pass  # File might already be deleted

    def get_zip_filename(self, keys: List[str]) -> str:
        """Generate a filename for the ZIP download."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        if len(keys) == 1:
            # Single file - use its name
            key = keys[0]
            original_name = Path(key).stem
            return f"{original_name}_{timestamp}.zip"
        else:
            # Multiple files
            return f"batch_download_{timestamp}.zip"

    async def get_zip_size_estimate(self, keys: List[str]) -> int:
        """Get an estimate of the ZIP file size."""
        total_size = 0
        
        for key in keys:
            metadata = await storage_manager.get_file_metadata(key)
            if metadata:
                # ZIP compression typically reduces size by 10-30%, but we'll be conservative
                total_size += metadata["size"]
        
        # Add some overhead for ZIP structure (conservative estimate)
        zip_overhead = len(keys) * 1024  # 1KB per file for ZIP metadata
        
        return total_size + zip_overhead


# Global instance
zip_streamer = ZipStreamer()
