#!/usr/bin/env python3
"""
Simple example of using Stream-Line File Uploader
"""

import asyncio
import os
from streamline_file_uploader import StreamlineFileUploader

async def main():
    """Simple file upload example"""
    
    # Set your configuration (or use environment variables)
    service_token = os.getenv("AUTH_SERVICE_TOKEN", "your-service-token-here")
    user_email = os.getenv("DEFAULT_USER_EMAIL", "user@example.com")
    
    print("🚀 Stream-Line File Uploader Example")
    print("=" * 40)
    
    # Initialize uploader
    async with StreamlineFileUploader(
        service_token=service_token,
        default_user_email=user_email
    ) as uploader:
        
        # Upload a simple text file
        print("\n📝 Uploading a text file...")
        result = await uploader.upload_file(
            file_content=b"This is a test file uploaded via the Python package!",
            filename="test_document.txt",
            folder="documents/test"
        )
        
        print(f"✅ File uploaded successfully!")
        print(f"   File key: {result.file_key}")
        print(f"   Public URL: {result.public_url}")
        print(f"   Size: {result.size} bytes")
        print(f"   Folder: {result.folder}")
        print(f"   Filename: {result.filename}")
        
        # Upload a video file
        print("\n🎥 Uploading a video file...")
        video_result = await uploader.upload_file(
            file_content=b"Fake video content for demonstration",
            filename="demo_video.mp4",
            folder="veo/videos"
        )
        
        print(f"✅ Video uploaded successfully!")
        print(f"   File key: {video_result.file_key}")
        print(f"   Public URL: {video_result.public_url}")
        print(f"   Folder: {video_result.folder}")
        
        # List files in the veo/videos folder
        print("\n📁 Listing files in veo/videos folder...")
        videos = await uploader.files.list_files(folder="veo/videos")
        print(f"✅ Found {len(videos)} files in veo/videos")
        
        # Get download URL for the video
        print("\n🔗 Getting download URL...")
        download_url = await uploader.files.get_download_url(video_result.file_key)
        print(f"✅ Download URL: {download_url}")
        
        print("\n🎉 Example completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
