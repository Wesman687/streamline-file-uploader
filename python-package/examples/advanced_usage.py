#!/usr/bin/env python3
"""
Advanced usage example for Stream-Line File Uploader
Demonstrates batch uploads, file search, and file management
"""

import os
import asyncio
from pathlib import Path
from streamline_file_uploader import StreamlineFileUploader, UploadOptions

async def main():
    """Demonstrate advanced file upload functionality"""
    
    # Set your configuration
    service_token = os.getenv("AUTH_SERVICE_TOKEN", "your-service-token-here")
    
    print("🚀 Stream-Line File Uploader Advanced Demo")
    print("=" * 50)
    
    # Initialize uploader
    uploader = StreamlineFileUploader(
        service_token=service_token
    )
    
    try:
        # Example 1: Upload with custom options
        print("\n📁 Example 1: Upload with custom options")
        options = UploadOptions(
            folder="veo/videos",
            metadata={
                "category": "demo",
                "tags": ["python", "example"],
                "description": "Demo video upload"
            }
        )
        
        video_content = b"Fake video content for demonstration"
        result1 = await uploader.upload_file(
            file_content=video_content,
            filename="demo_video.mp4",
            options=options,
            user_email="user@example.com"  # Always specify user_email
        )
        
        print(f"✅ Video uploaded successfully!")
        print(f"   File key: {result1.file_key}")
        print(f"   Public URL: {result1.public_url}")
        print(f"   Folder: {result1.folder}")
        print(f"   Metadata: {options.metadata}")
        
        # Example 2: Upload from file path (if file exists)
        print("\n📂 Example 2: Upload from file path")
        test_file_path = Path(__file__)  # This file itself
        
        if test_file_path.exists():
            result2 = await uploader.upload_file(
                file_content=str(test_file_path),
                filename=test_file_path.name,
                folder="examples",
                user_email="user@example.com"  # Always specify user_email
            )
            
            print(f"✅ File uploaded from path!")
            print(f"   File key: {result2.file_key}")
            print(f"   Public URL: {result2.public_url}")
            print(f"   Size: {result2.size} bytes")
        else:
            print("⚠️  Test file not found, skipping path upload example")
        
        # Example 3: Batch upload
        print("\n📦 Example 3: Batch upload")
        files_to_upload = [
            {
                "content": b"Document 1 content",
                "filename": "doc1.txt",
                "folder": "documents"
            },
            {
                "content": b"Document 2 content", 
                "filename": "doc2.txt",
                "folder": "documents"
            }
        ]
        
        batch_results = await uploader.upload_files(
            files=files_to_upload,
            user_email="user@example.com"  # Always specify user_email
        )
        
        print(f"✅ Batch upload completed! {len(batch_results)} files uploaded")
        for i, result in enumerate(batch_results):
            print(f"   File {i+1}: {result.filename} -> {result.file_key}")
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during upload: {e}")
        raise
    
    finally:
        await uploader.close()

if __name__ == "__main__":
    asyncio.run(main())


