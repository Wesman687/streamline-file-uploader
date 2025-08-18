#!/usr/bin/env python3
"""
Sample client for Stream-Line Upload Server
Demonstrates how to use the upload API
"""

import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Optional

import httpx


class UploadClient:
    def __init__(self, base_url: str, service_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.service_token = service_token
        
    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.service_token:
            headers["X-Service-Token"] = self.service_token
        return headers
    
    async def upload_file_single(self, file_path: Path, folder: str = None) -> dict:
        """Upload a single file in one request."""
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        # Read file content
        file_content = file_path.read_bytes()
        file_size = len(file_content)
        
        # Calculate SHA256
        sha256_hash = hashlib.sha256(file_content).hexdigest()
        
        # Encode content as base64
        content_b64 = base64.b64encode(file_content).decode('ascii')
        
        async with httpx.AsyncClient() as client:
            # Initialize upload
            init_request = {
                "mode": "single",
                "files": [{
                    "name": file_path.name,
                    "size": file_size,
                    "mime": "application/octet-stream"
                }]
            }
            
            if folder:
                init_request["folder"] = folder
            
            response = await client.post(
                f"{self.base_url}/v1/files/init",
                json=init_request,
                headers=self._get_headers()
            )
            response.raise_for_status()
            init_result = response.json()
            
            upload_id = init_result["uploadId"]
            
            # Upload content as single "part"
            part_request = {
                "uploadId": upload_id,
                "partNumber": 1,
                "chunkBase64": content_b64
            }
            
            response = await client.post(
                f"{self.base_url}/v1/files/part",
                json=part_request,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            # Complete upload
            complete_request = {
                "uploadId": upload_id,
                "sha256": sha256_hash,
                "meta": {
                    "filename": file_path.name,
                    "original_name": file_path.name,
                    "folder": folder
                }
            }
            
            response = await client.post(
                f"{self.base_url}/v1/files/complete",
                json=complete_request,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            return response.json()
    
    async def upload_file_chunked(self, file_path: Path, chunk_size: int = 1024 * 1024) -> dict:
        """Upload a file in chunks."""
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        file_size = file_path.stat().st_size
        
        async with httpx.AsyncClient() as client:
            # Initialize chunked upload
            init_request = {
                "mode": "chunked",
                "files": [{
                    "name": file_path.name,
                    "size": file_size,
                    "mime": "application/octet-stream"
                }]
            }
            
            response = await client.post(
                f"{self.base_url}/v1/files/init",
                json=init_request,
                headers=self._get_headers()
            )
            response.raise_for_status()
            init_result = response.json()
            
            upload_id = init_result["uploadId"]
            
            # Upload chunks
            sha256_hash = hashlib.sha256()
            part_number = 1
            
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    sha256_hash.update(chunk)
                    chunk_b64 = base64.b64encode(chunk).decode('ascii')
                    
                    part_request = {
                        "uploadId": upload_id,
                        "partNumber": part_number,
                        "chunkBase64": chunk_b64
                    }
                    
                    response = await client.post(
                        f"{self.base_url}/v1/files/part",
                        json=part_request,
                        headers=self._get_headers()
                    )
                    response.raise_for_status()
                    
                    print(f"Uploaded part {part_number}")
                    part_number += 1
            
            # Complete upload
            complete_request = {
                "uploadId": upload_id,
                "sha256": sha256_hash.hexdigest(),
                "meta": {
                    "filename": file_path.name,
                    "original_name": file_path.name
                }
            }
            
            response = await client.post(
                f"{self.base_url}/v1/files/complete",
                json=complete_request,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            return response.json()
    
    async def get_signed_url(self, file_key: str, ttl: int = 3600) -> dict:
        """Get a signed URL for file access."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/files/signed-url",
                params={"key": file_key, "ttl": ttl},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def get_file_metadata(self, file_key: str) -> dict:
        """Get file metadata."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/files/metadata/{file_key}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def create_batch_download(self, file_keys: list) -> dict:
        """Create a batch download token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/files/batch-download",
                json={"keys": file_keys},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def download_batch(self, token: str, output_path: Path):
        """Download batch as ZIP file."""
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "GET",
                f"{self.base_url}/v1/files/batch-download/{token}"
            ) as response:
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
    
    async def list_all_files(self, user_id: str = None, folder: str = None) -> dict:
        """List all files for a user."""
        async with httpx.AsyncClient() as client:
            params = {}
            if user_id:
                params["user_id"] = user_id
            if folder:
                params["folder"] = folder
            
            response = await client.get(
                f"{self.base_url}/v1/files/all",
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def health_check(self) -> dict:
        """Check server health."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/healthz")
            response.raise_for_status()
            return response.json()


async def demo():
    """Demonstrate upload client usage."""
    # Configure client
    client = UploadClient(
        base_url="https://file-server.stream-lineai.com",
        service_token="ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
    )
    
    print("=== Upload Server Client Demo ===")
    
    # Create a test file
    test_file = Path("test_upload.txt")
    test_file.write_text("Hello, this is a test file for the Upload Server!\n" * 100)
    
    try:
        # Health check
        print("1. Health check...")
        health = await client.health_check()
        print(f"   Server status: {health}")
        
        # Upload file to a specific folder
        print("2. Uploading file to 'main/test' folder...")
        upload_result = await client.upload_file_single(test_file, folder="main/test")
        print(f"   Upload result: {upload_result}")
        
        file_key = upload_result["key"]
        
        # List all files
        print("3. Listing all files...")
        file_list = await client.list_all_files(user_id="test-user")
        print(f"   Found {file_list['total_count']} files, total size: {file_list['total_size']} bytes")
        for file_info in file_list['files']:
            print(f"   - {file_info['filename']} ({file_info['size']} bytes) in folder: {file_info['folder']}")
        
        # Get metadata
        print("4. Getting file metadata...")
        metadata = await client.get_file_metadata(file_key)
        print(f"   Metadata: {metadata}")
        
        # Get signed URL
        print("5. Getting signed URL...")
        signed_url = await client.get_signed_url(file_key)
        print(f"   Signed URL: {signed_url['url']}")
        
        # Create batch download
        print("6. Creating batch download...")
        batch = await client.create_batch_download([file_key])
        print(f"   Batch token: {batch['token']}")
        
        # Download batch
        print("7. Downloading batch...")
        zip_file = Path("download.zip")
        await client.download_batch(batch["token"], zip_file)
        print(f"   Downloaded ZIP: {zip_file} ({zip_file.stat().st_size} bytes)")
        
        print("✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
        zip_file = Path("download.zip")
        if zip_file.exists():
            zip_file.unlink()


if __name__ == "__main__":
    asyncio.run(demo())
