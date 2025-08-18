import os
import hashlib
import json
import shutil
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from uuid import uuid4


class StorageManager:
    def __init__(self):
        self.upload_root = Path(os.getenv("UPLOAD_ROOT", "/data/uploads"))
        self.parts_dir = self.upload_root / ".parts"
        self.max_body_mb = int(os.getenv("MAX_BODY_MB", "5120"))
        self.per_user_quota_gb = int(os.getenv("PER_USER_QUOTA_GB", "500"))
        
        # Ensure directories exist
        self.upload_root.mkdir(parents=True, exist_ok=True)
        self.parts_dir.mkdir(parents=True, exist_ok=True)

    def get_user_directory(self, user_id: str, folder: str = "") -> Path:
        """Get the user's upload directory with optional folder structure."""
        user_dir = self.upload_root / "storage" / user_id
        
        if folder:
            # Sanitize folder path and add it
            folder_parts = [self._sanitize_folder_part(part) for part in folder.split('/') if part.strip()]
            for part in folder_parts:
                user_dir = user_dir / part
        
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def get_file_path(self, key: str) -> Path:
        """Get the full file path from a key."""
        return self.upload_root / key

    def generate_file_key(self, user_id: str, filename: str, folder: str = "") -> str:
        """Generate a unique file key."""
        base_path = f"storage/{user_id}"
        
        if folder:
            # Sanitize folder path
            folder_parts = [self._sanitize_folder_part(part) for part in folder.split('/') if part.strip()]
            if folder_parts:
                base_path = f"{base_path}/{'/'.join(folder_parts)}"
        
        unique_id = str(uuid4())[:8]
        safe_filename = self._sanitize_filename(filename)
        return f"{base_path}/{unique_id}_{safe_filename}"

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # Limit length and remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        return filename or "unnamed_file"

    def _sanitize_folder_part(self, folder_part: str) -> str:
        """Sanitize a single folder part for safe storage."""
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            folder_part = folder_part.replace(char, '_')
        
        # Remove leading/trailing dots and spaces
        folder_part = folder_part.strip('. ')
        
        # Prevent directory traversal
        if folder_part in ['', '.', '..']:
            folder_part = 'invalid'
        
        # Limit length
        if len(folder_part) > 100:
            folder_part = folder_part[:100]
        
        return folder_part or "default"

    async def create_upload_session(self, upload_id: str, files_info: list) -> Path:
        """Create a directory for upload session parts."""
        session_dir = self.parts_dir / upload_id
        session_dir.mkdir(exist_ok=True)
        
        # Store session metadata
        metadata = {
            "upload_id": upload_id,
            "files": files_info,
            "created_at": datetime.utcnow().isoformat()
        }
        
        async with aiofiles.open(session_dir / "metadata.json", 'w') as f:
            await f.write(json.dumps(metadata, indent=2))
        
        return session_dir

    async def store_chunk(self, upload_id: str, part_number: int, chunk_data: bytes) -> Path:
        """Store a chunk for chunked upload."""
        session_dir = self.parts_dir / upload_id
        if not session_dir.exists():
            raise ValueError(f"Upload session {upload_id} not found")
        
        part_path = session_dir / f"part_{part_number:06d}"
        
        async with aiofiles.open(part_path, 'wb') as f:
            await f.write(chunk_data)
        
        return part_path

    async def assemble_chunks(self, upload_id: str, final_key: str) -> Tuple[Path, str]:
        """Assemble chunks into final file and return path and SHA256."""
        session_dir = self.parts_dir / upload_id
        if not session_dir.exists():
            raise ValueError(f"Upload session {upload_id} not found")
        
        # Get all part files
        part_files = sorted([
            f for f in session_dir.iterdir() 
            if f.name.startswith("part_") and f.is_file()
        ])
        
        if not part_files:
            raise ValueError("No parts found for upload session")
        
        # Create final file path
        final_path = self.get_file_path(final_key)
        final_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Assemble chunks and calculate SHA256
        sha256_hash = hashlib.sha256()
        
        async with aiofiles.open(final_path, 'wb') as final_file:
            for part_file in part_files:
                async with aiofiles.open(part_file, 'rb') as part:
                    while True:
                        chunk = await part.read(8192)
                        if not chunk:
                            break
                        await final_file.write(chunk)
                        sha256_hash.update(chunk)
        
        # Clean up session directory
        shutil.rmtree(session_dir)
        
        return final_path, sha256_hash.hexdigest()

    async def store_single_file(self, key: str, file_data: bytes) -> Tuple[Path, str]:
        """Store a single file and return path and SHA256."""
        file_path = self.get_file_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate SHA256
        sha256_hash = hashlib.sha256(file_data).hexdigest()
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_data)
        
        return file_path, sha256_hash

    async def get_file_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get file metadata."""
        file_path = self.get_file_path(key)
        
        if not file_path.exists():
            return None
        
        stat = file_path.stat()
        
        # Try to read stored metadata
        metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
        metadata = {}
        
        if metadata_path.exists():
            try:
                async with aiofiles.open(metadata_path, 'r') as f:
                    content = await f.read()
                    metadata = json.loads(content)
            except (json.JSONDecodeError, OSError):
                pass
        
        return {
            "size": stat.st_size,
            "mime": metadata.get("mime", "application/octet-stream"),
            "sha256": metadata.get("sha256", ""),
            "createdAt": datetime.fromtimestamp(stat.st_ctime),
            **metadata
        }

    async def store_file_metadata(self, key: str, metadata: Dict[str, Any]):
        """Store file metadata."""
        file_path = self.get_file_path(key)
        metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
        
        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(json.dumps(metadata, indent=2, default=str))

    async def delete_file(self, key: str) -> bool:
        """Delete a file and its metadata."""
        file_path = self.get_file_path(key)
        metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
        
        deleted = False
        
        if file_path.exists():
            file_path.unlink()
            deleted = True
        
        if metadata_path.exists():
            metadata_path.unlink()
        
        return deleted

    def check_user_quota(self, user_id: str) -> Tuple[int, int]:
        """Check user's current usage against quota. Returns (used_bytes, quota_bytes)."""
        user_base_dir = self.upload_root / "storage" / user_id
        quota_bytes = self.per_user_quota_gb * 1024 * 1024 * 1024
        
        if not user_base_dir.exists():
            return 0, quota_bytes
        
        used_bytes = 0
        for file_path in user_base_dir.rglob("*"):
            if file_path.is_file() and not file_path.suffix == '.meta':
                used_bytes += file_path.stat().st_size
        
        return used_bytes, quota_bytes

    def get_disk_usage(self) -> Dict[str, float]:
        """Get disk usage information."""
        usage = shutil.disk_usage(self.upload_root)
        return {
            "total_gb": usage.total / (1024**3),
            "used_gb": usage.used / (1024**3),
            "free_gb": usage.free / (1024**3)
        }

    async def list_user_files(self, user_id: str, folder: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all files for a user, optionally filtered by folder."""
        user_base_dir = self.upload_root / "storage" / user_id
        
        if not user_base_dir.exists():
            return []
        
        files = []
        search_dir = user_base_dir
        
        # If folder specified, search within that folder
        if folder:
            folder_parts = [self._sanitize_folder_part(part) for part in folder.split('/') if part.strip()]
            for part in folder_parts:
                search_dir = search_dir / part
            
            if not search_dir.exists():
                return []
        
        # Find all files recursively
        for file_path in search_dir.rglob("*"):
            if file_path.is_file() and not file_path.suffix == '.meta':
                # Calculate relative path from user directory
                relative_path = file_path.relative_to(self.upload_root)
                key = str(relative_path)
                
                # Get file stats
                stat = file_path.stat()
                
                # Try to get metadata
                metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
                metadata = {}
                if metadata_path.exists():
                    try:
                        async with aiofiles.open(metadata_path, 'r') as f:
                            content = await f.read()
                            metadata = json.loads(content)
                    except (json.JSONDecodeError, OSError):
                        pass
                
                # Extract folder from key
                key_parts = key.split('/')
                file_folder = None
                if len(key_parts) > 3:  # storage/user_id/folder/file
                    file_folder = '/'.join(key_parts[2:-1])
                
                # Extract filename (remove UUID prefix)
                filename = file_path.name
                if '_' in filename:
                    # Remove UUID prefix
                    filename = '_'.join(filename.split('_')[1:])
                
                files.append({
                    "key": key,
                    "filename": metadata.get("original_name", filename),
                    "size": stat.st_size,
                    "mime": metadata.get("mime", "application/octet-stream"),
                    "created_at": datetime.fromtimestamp(stat.st_ctime),
                    "folder": file_folder
                })
        
        # Sort by creation time (newest first)
        files.sort(key=lambda x: x["created_at"], reverse=True)
        return files

    def is_writable(self) -> bool:
        """Check if the upload directory is writable."""
        try:
            test_file = self.upload_root / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except (OSError, PermissionError):
            return False


# Global instance
storage_manager = StorageManager()
