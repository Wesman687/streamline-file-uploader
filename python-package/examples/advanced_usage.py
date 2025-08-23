#!/usr/bin/env python3
"""
Advanced usage example for Stream-Line File Uploader
Demonstrates batch uploads, file search, and file management
"""

import asyncio
import os
from pathlib import Path
from streamline_file_uploader import StreamlineFileUploader, UploadOptions

async def main():
    """Demonstrate advanced file uploader functionality"""
    
    # Set your configuration
    service_token = os.getenv("AUTH_SERVICE_TOKEN", "your-service-token-here")
    user_id = os.getenv("DEFAULT_USER_ID", "user@example.com")
    
    print("🚀 Advanced Stream-Line File Uploader Demo")
    print("=" * 60)
    
    # Initialize uploader
    uploader = StreamlineFileUploader(
        service_token=service_token,
        default_user=user_id
    )
    
    try:
        # Example 1: Batch upload multiple files
        print("\n📦 Example 1: Batch Upload Multiple Files")
        
        files_to_upload = [
            {
                'content': b"This is document 1 content",
                'filename': 'document1.txt',
                'folder': 'documents/2024'
            },
            {
                'content': b"This is document 2 content", 
                'filename': 'document2.txt',
                'folder': 'documents/2024'
            },
            {
                'content': b"This is a video file content",
                'filename': 'demo_video.mp4',
                'folder': 'veo/videos'
            }
        ]
        
        # Use batch upload
        batch_results = await uploader.batch.upload_files(
            files=files_to_upload,
            user_id=user_id
        )
        
        print(f"✅ Batch upload completed! {len(batch_results)} files uploaded")
        for i, result in enumerate(batch_results):
            print(f"   File {i+1}: {result.filename} -> {result.folder}")
        
        # Example 2: List all files
        print("\n📋 Example 2: List All Files")
        all_files = await uploader.files.list_files(user_id=user_id)
        print(f"✅ Found {len(all_files)} total files")
        
        # Example 3: List files in specific folder
        print("\n📁 Example 3: List Files in Documents Folder")
        doc_files = await uploader.files.list_files(
            user_id=user_id, 
            folder="documents/2024"
        )
        print(f"✅ Found {len(doc_files)} files in documents/2024")
        for file_info in doc_files:
            print(f"   - {file_info.get('filename', 'Unknown')} ({file_info.get('file_size', 0)} bytes)")
        
        # Example 4: Search files by criteria
        print("\n🔍 Example 4: Search Files by Criteria")
        
        # Search for text files
        text_files = await uploader.files.search_files(
            user_id=user_id,
            mime_type="text/plain"
        )
        print(f"✅ Found {len(text_files)} text files")
        
        # Search for large files (>50 bytes)
        large_files = await uploader.files.search_files(
            user_id=user_id,
            min_size=50
        )
        print(f"✅ Found {len(large_files)} files larger than 50 bytes")
        
        # Search by filename pattern
        doc_files_search = await uploader.files.search_files(
            user_id=user_id,
            filename_pattern="document"
        )
        print(f"✅ Found {len(doc_files_search)} files with 'document' in name")
        
        # Example 5: Get folder statistics
        print("\n📊 Example 5: Get Folder Statistics")
        
        # Root folder stats
        root_stats = await uploader.files.get_folder_stats(user_id=user_id)
        print(f"✅ Root folder stats:")
        print(f"   - File count: {root_stats['file_count']}")
        print(f"   - Total size: {root_stats['total_size']} bytes")
        print(f"   - MIME types: {root_stats['mime_types']}")
        
        # Documents folder stats
        docs_stats = await uploader.files.get_folder_stats(user_id=user_id, folder="documents/2024")
        print(f"✅ Documents folder stats:")
        print(f"   - File count: {docs_stats['file_count']}")
        print(f"   - Total size: {docs_stats['total_size']} bytes")
        
        # Example 6: Get download URLs
        print("\n🔗 Example 6: Get Download URLs")
        
        if batch_results:
            first_file = batch_results[0]
            download_url = await uploader.files.get_download_url(first_file.file_key)
            print(f"✅ Download URL for {first_file.filename}:")
            print(f"   {download_url}")
        
        # Example 7: Get file information
        print("\nℹ️  Example 7: Get File Information")
        
        if batch_results:
            first_file = batch_results[0]
            file_info = await uploader.files.get_file_info(first_file.file_key)
            print(f"✅ File info for {first_file.filename}:")
            print(f"   - File key: {file_info.get('file_key', 'N/A')}")
            print(f"   - Size: {file_info.get('file_size', 'N/A')} bytes")
            print(f"   - MIME type: {file_info.get('mime_type', 'N/A')}")
            print(f"   - Folder: {file_info.get('folder', 'N/A')}")
        
        print("\n🎉 All advanced examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during advanced demo: {e}")
        raise
    
    finally:
        await uploader.close()

if __name__ == "__main__":
    asyncio.run(main())

