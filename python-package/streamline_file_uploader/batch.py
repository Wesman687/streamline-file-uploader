"""
Batch upload functionality for Stream-Line File Uploader
"""

from typing import List, Dict, Any, Optional
from .models import UploadOptions, UploadResult
from .exceptions import UploadError


class BatchUploader:
    """Handles batch file uploads"""
    
    def __init__(self, uploader):
        self.uploader = uploader
    
    async def upload_files(
        self,
        files: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        default_options: Optional[UploadOptions] = None
    ) -> List[UploadResult]:
        """
        Upload multiple files in batch
        
        Args:
            files: List of file dictionaries with:
                   - 'content': File content (bytes, path, or file object)
                   - 'filename': Name of the file
                   - 'folder': Optional folder path
                   - 'options': Optional UploadOptions for this file
            user_id: User ID for uploads
            default_options: Default options for all files
        
        Returns:
            List of UploadResult objects
        """
        if not files:
            return []
        
        results = []
        errors = []
        
        for i, file_info in enumerate(files):
            try:
                content = file_info['content']
                filename = file_info['filename']
                folder = file_info.get('folder')
                file_options = file_info.get('options')
                
                # Merge options
                if file_options is None:
                    file_options = UploadOptions()
                if default_options:
                    for key, value in default_options.dict().items():
                        if value is not None and getattr(file_options, key) is None:
                            setattr(file_options, key, value)
                
                if folder is not None:
                    file_options.folder = folder
                
                result = await self.uploader.upload_file(
                    file_content=content,
                    filename=filename,
                    user_id=user_id,
                    options=file_options
                )
                
                results.append(result)
                
            except Exception as e:
                error_msg = f"File {i+1} ({filename}): {str(e)}"
                errors.append(error_msg)
        
        if errors:
            raise UploadError(
                f"Batch upload completed with {len(errors)} errors: {'; '.join(errors)}",
                "batch"
            )
        
        return results
