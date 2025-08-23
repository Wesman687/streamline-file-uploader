#!/usr/bin/env python3
"""
COPY THIS FILE INTO YOUR PROJECT!

This is a template showing how to use the Stream-Line File Uploader.
Just copy the package folder and this code, and you're ready to go!
"""

import asyncio
import os
from pathlib import Path

# Copy the streamline_file_uploader folder to your project first!
from streamline_file_uploader import StreamlineFileUploader

async def main():
    """Example of how to use the file uploader in your app"""
    
    # Set your configuration
    service_token = os.getenv("AUTH_SERVICE_TOKEN", "your-service-token-here")
    user_email = os.getenv("DEFAULT_USER_EMAIL", "user@example.com")
    
    print("🚀 File Uploader Example")
    print("=" * 40)
    
    # Initialize uploader
    async with StreamlineFileUploader(
        service_token=service_token,
        default_user_email=user_email
    ) as uploader:
        
        # Example 1: Upload a text file
        print("\n📝 Uploading text file...")
        result = await uploader.upload_file(
            file_content=b"This is a test file!",
            filename="test.txt",
            folder="documents"
        )
        
        print(f"✅ File uploaded!")
        print(f"   URL: {result.public_url}")
        print(f"   Size: {result.size} bytes")
        
        # Example 2: Upload a video
        print("\n🎥 Uploading video...")
        video_result = await uploader.upload_file(
            file_content=b"Fake video content",
            filename="demo.mp4",
            folder="veo/videos"
        )
        
        print(f"✅ Video uploaded!")
        print(f"   URL: {video_result.public_url}")
        
        # Example 3: Find all videos
        print("\n🔍 Finding all videos...")
        videos = await uploader.lookup.find_video_files(folder="veo/videos")
        print(f"📁 Found {len(videos)} videos")
        
        # Example 4: Get download URL
        print("\n🔗 Getting download URL...")
        download_url = await uploader.files.get_download_url(video_result.file_key)
        print(f"Download: {download_url}")
        
        print("\n🎉 All examples completed!")

if __name__ == "__main__":
    asyncio.run(main())

"""
INSTRUCTIONS:

1. Copy the streamline_file_uploader folder to your project
2. Install dependencies: pip install httpx pydantic
3. Set environment variables:
   export AUTH_SERVICE_TOKEN="your-token"
   export DEFAULT_USER_EMAIL="user@example.com"
4. Run this file: python COPY_ME.py

That's it! Your app now has file upload capabilities! 🚀
"""

