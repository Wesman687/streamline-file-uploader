"""
Advanced file lookup and search functionality for Stream-Line File Uploader
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from .exceptions import ValidationError


class FileLookup:
    """Advanced file lookup and search capabilities"""
    
    def __init__(self, file_manager):
        self.file_manager = file_manager
    
    async def find_files_by_name(
        self,
        filename: str,
        user_email: Optional[str] = None,
        folder: Optional[str] = None,
        exact_match: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Find files by filename with flexible matching
        
        Args:
            filename: Filename to search for
            user_email: User email to search in
            folder: Optional folder to limit search
            exact_match: If True, only return exact filename matches
        
        Returns:
            List of matching files
        """
        if exact_match:
            return await self.file_manager.search_files(
                user_email=user_email,
                folder=folder,
                filename_pattern=filename
            )
        else:
            return await self.file_manager.search_files(
                user_email=user_email,
                folder=folder,
                filename_pattern=filename
            )
    
    async def find_files_by_type(
        self,
        mime_type: str,
        user_email: Optional[str] = None,
        folder: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all files of a specific MIME type
        
        Args:
            mime_type: MIME type to search for (e.g., "video/mp4", "image/jpeg")
            user_email: User email to search in
            folder: Optional folder to limit search
        
        Returns:
            List of files with matching MIME type
        """
        return await self.file_manager.search_files(
            user_email=user_email,
            mime_type=mime_type,
            folder=folder
        )
    
    async def find_video_files(
        self,
        user_email: Optional[str] = None,
        folder: Optional[str] = None,
        video_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all video files
        
        Args:
            user_email: User email to search in
            folder: Optional folder to limit search
            video_types: List of video MIME types (defaults to common video types)
        
        Returns:
            List of video files
        """
        if video_types is None:
            video_types = [
                "video/mp4", "video/avi", "video/mov", "video/wmv",
                "video/flv", "video/webm", "video/mkv", "video/m4v"
            ]
        
        all_videos = []
        for video_type in video_types:
            videos = await self.file_manager.search_files(
                user_email=user_email,
                mime_type=video_type,
                folder=folder
            )
            all_videos.extend(videos)
        
        return all_videos
    
    async def find_image_files(
        self,
        user_email: Optional[str] = None,
        folder: Optional[str] = None,
        image_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all image files
        
        Args:
            user_email: User email to search in
            folder: Optional folder to limit search
            image_types: List of image MIME types (defaults to common image types)
        
        Returns:
            List of image files
        """
        if image_types is None:
            image_types = [
                "image/jpeg", "image/png", "image/gif", "image/bmp",
                "image/webp", "image/tiff", "image/svg+xml"
            ]
        
        all_images = []
        for image_type in image_types:
            images = await self.file_manager.search_files(
                user_email=user_email,
                mime_type=image_type,
                folder=folder
            )
            all_images.extend(images)
        
        return all_images
    
    async def find_document_files(
        self,
        user_email: Optional[str] = None,
        folder: Optional[str] = None,
        document_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all document files
        
        Args:
            user_email: User email to search in
            folder: Optional folder to limit search
            document_types: List of document MIME types (defaults to common document types)
        
        Returns:
            List of document files
        """
        if document_types is None:
            document_types = [
                "application/pdf", "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "text/plain", "text/csv"
            ]
        
        all_docs = []
        for doc_type in document_types:
            docs = await self.file_manager.search_files(
                user_email=user_email,
                mime_type=doc_type,
                folder=folder
            )
            all_docs.extend(docs)
        
        return all_docs
    
    async def find_large_files(
        self,
        min_size_mb: float = 100.0,
        user_email: Optional[str] = None,
        folder: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find files larger than a specified size
        
        Args:
            min_size_mb: Minimum file size in MB
            user_email: User email to search in
            folder: Optional folder to limit search
        
        Returns:
            List of large files
        """
        min_size_bytes = int(min_size_mb * 1024 * 1024)
        return await self.file_manager.search_files(
            user_email=user_email,
            folder=folder,
            min_size=min_size_bytes
        )
    
    async def find_recent_files(
        self,
        days: int = 7,
        user_email: Optional[str] = None,
        folder: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find files uploaded within the last N days
        
        Args:
            days: Number of days to look back
            user_email: User email to search in
            folder: Optional folder to limit search
        
        Returns:
            List of recent files
        """
        all_files = await self.file_manager.list_files(
            user_email=user_email,
            folder=folder
        )
        
        if not all_files:
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_files = []
        
        for file_info in all_files:
            # Check if file has timestamp and is recent
            if 'timestamp' in file_info:
                try:
                    file_date = datetime.fromisoformat(file_info['timestamp'].replace('Z', '+00:00'))
                    if file_date > cutoff_date:
                        recent_files.append(file_info)
                except (ValueError, TypeError):
                    continue
        
        return recent_files
    
    async def find_files_by_extension(
        self,
        extension: str,
        user_email: Optional[str] = None,
        folder: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find files by file extension
        
        Args:
            extension: File extension (e.g., "mp4", "pdf", "jpg")
            user_email: User email to search in
            folder: Optional folder to limit search
        
        Returns:
            List of files with matching extension
        """
        # Remove dot if present
        if extension.startswith('.'):
            extension = extension[1:]
        
        all_files = await self.file_manager.list_files(
            user_email=user_email,
            folder=folder
        )
        
        if not all_files:
            return []
        
        matching_files = []
        for file_info in all_files:
            filename = file_info.get('filename', '')
            if filename.lower().endswith(f'.{extension.lower()}'):
                matching_files.append(file_info)
        
        return matching_files
    
    async def get_file_count_by_type(
        self,
        user_email: Optional[str] = None,
        folder: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Get count of files by MIME type
        
        Args:
            user_email: User email to count files for
            folder: Optional folder to limit count
        
        Returns:
            Dictionary mapping MIME types to file counts
        """
        all_files = await self.file_manager.list_files(
            user_email=user_email,
            folder=folder
        )
        
        type_counts = {}
        for file_info in all_files:
            mime_type = file_info.get('mime_type', 'unknown')
            type_counts[mime_type] = type_counts.get(mime_type, 0) + 1
        
        return type_counts
