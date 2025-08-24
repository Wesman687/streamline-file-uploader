#!/usr/bin/env python3
"""
Basic usage example for Stream-Line File Uploader
"""

import asyncio
import os
from pathlib import Path
from streamline_file_uploader import StreamlineFileUploader, UploadOptions

async def main():
    """Demonstrate basic file upload functionality"""
    
    # Set your configuration
    service_token = os.getenv("AUTH_SERVICE_TOKEN", "your-service-token-here")
    user_id = os.getenv("DEFAULT_USER_ID", "user@example.com")
    
    print("🚀 Stream-Line File Uploader Demo")
    print("=" * 50)
    
    # Initialize uploader
    uploader = StreamlineFileUploader(
        service_token=service_token,
        default_user=user_id
    )
    
    try:
        # Example 1: Upload text content
        print("\n📝 Example 1: Upload text content")
        text_content = b"This is a test file uploaded via the Python package!"
        result1 = await uploader.upload_file(
            file_content=text_content,
            filename="test_document.txt",
            folder="documents/test"
        )
        
        print(f"✅ File uploaded successfully!")
        print(f"   File key: {result1.file_key}")
        print(f"   Public URL: {result1.public_url}")
        print(f"   Size: {result1.size} bytes")
        print(f"   MIME type: {result1.mime_type}")
        print(f"   Folder: {result1.folder}")
        print(f"   Filename: {result1.filename}")
        
        # Example 2: Upload with custom options
        print("\n📁 Example 2: Upload with custom options")
        options = UploadOptions(
            folder="veo/videos",
            metadata={
                "category": "demo",
                "tags": ["python", "example"],
                "description": "Demo video upload"
            }
        )
        
        video_content = b"Fake video content for demonstration"
        result2 = await uploader.upload_file(
            file_content=video_content,
            filename="demo_video.mp4",
            options=options
        )
        
        print(f"✅ Video uploaded successfully!")
        print(f"   File key: {result2.file_key}")
        print(f"   Public URL: {result2.public_url}")
        print(f"   Folder: {result2.folder}")
        print(f"   Metadata: {options.metadata}")
        
        # Example 3: Upload from file path (if file exists)
        print("\n📂 Example 3: Upload from file path")
        test_file_path = Path(__file__)  # This file itself
        
        if test_file_path.exists():
            result3 = await uploader.upload_file(
                file_content=str(test_file_path),
                filename=test_file_path.name,
                folder="examples"
            )
            
            print(f"✅ File uploaded from path!")
            print(f"   File key: {result3.file_key}")
            print(f"   Public URL: {result3.public_url}")
            print(f"   Size: {result3.size} bytes")
        else:
            print("⚠️  Test file not found, skipping path upload example")
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during upload: {e}")
        raise
    
    finally:
        await uploader.close()

if __name__ == "__main__":
    asyncio.run(main())


