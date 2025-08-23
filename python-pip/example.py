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
    
    print("🚀 Stream-Line File Uploader Example")
    print("=" * 40)
    
    # Initialize uploader (NO default user - you'll pass user_email for each upload)
    async with StreamlineFileUploader(
        service_token=service_token
    ) as uploader:
        
        # Upload a simple text file for user1
        print("\n📝 Uploading a text file for user1...")
        result = await uploader.upload_file(
            file_content=b"This is a test file uploaded via the Python package!",
            filename="test_document.txt",
            folder="documents/test",
            user_email="user1@example.com"  # ← REQUIRED: Pass the actual user
        )
        
        print(f"✅ File uploaded successfully for user1!")
        print(f"   File key: {result.file_key}")
        print(f"   Public URL: {result.public_url}")
        print(f"   Size: {result.size} bytes")
        print(f"   Folder: {result.folder}")
        print(f"   Filename: {result.filename}")
        
        # Upload a video file for user2
        print("\n🎥 Uploading a video file for user2...")
        video_result = await uploader.upload_file(
            file_content=b"Fake video content for demonstration",
            filename="demo_video.mp4",
            folder="veo/videos",
            user_email="user2@example.com"  # ← REQUIRED: Pass the actual user
        )
        
        print(f"✅ Video uploaded successfully for user2!")
        print(f"   File key: {video_result.file_key}")
        print(f"   Public URL: {video_result.public_url}")
        print(f"   Folder: {video_result.folder}")
        
        # List files in the veo/videos folder for user2
        print("\n📁 Listing files in veo/videos folder for user2...")
        videos = await uploader.files.list_files(
            folder="veo/videos",
            user_email="user2@example.com"  # ← REQUIRED: Pass the actual user
        )
        print(f"✅ Found {len(videos)} files in veo/videos for user2")
        
        # Get download URL for the video
        print("\n🔗 Getting download URL...")
        download_url = await uploader.files.get_download_url(video_result.file_key)
        print(f"✅ Download URL: {download_url}")
        
        print("\n🎉 Example completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
