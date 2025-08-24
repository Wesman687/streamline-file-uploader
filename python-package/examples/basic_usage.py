#!/usr/bin/env python3
"""
Basic usage example for Stream-Line File Uploader
"""

import os
import asyncio
from pathlib import Path
from streamline_file_uploader import StreamlineFileUploader

async def main():
    # Load environment variables
    base_url = os.getenv("UPLOAD_BASE_URL", "https://file-server.stream-lineai.com")
    service_token = os.getenv("AUTH_SERVICE_TOKEN")
    
    if not service_token:
        print("Error: AUTH_SERVICE_TOKEN environment variable is required")
        return
    
    # Initialize uploader
    uploader = StreamlineFileUploader(
        base_url=base_url,
        service_token=service_token
    )
    
    try:
        # Upload a file (user_email is always required)
        result = await uploader.upload_file(
            file_content=b"Hello, World! This is a test file.",
            filename="hello.txt",
            folder="documents",
            user_email="user@example.com"  # Always specify user_email
        )
        
        print(f"✅ File uploaded successfully!")
        print(f"📁 File key: {result.file_key}")
        print(f"🔗 Public URL: {result.public_url}")
        print(f"📏 Size: {result.size} bytes")
        print(f"📂 Folder: {result.folder}")
        print(f"📄 Filename: {result.filename}")
        print(f"🔒 SHA256: {result.sha256}")
        
        # List files for the user
        files = await uploader.list_files(user_email="user@example.com")
        print(f"\n📋 User has {len(files)} files")
        
        # Get folder statistics
        stats = await uploader.get_folder_stats(user_email="user@example.com", folder="documents")
        print(f"📊 Documents folder: {stats['file_count']} files, {stats['total_size']} bytes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await uploader.close()

if __name__ == "__main__":
    asyncio.run(main())


