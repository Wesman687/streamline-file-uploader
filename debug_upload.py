#!/usr/bin/env python3
"""
Debug script to test file upload and see what's actually being sent
"""

import httpx
import asyncio
import base64

async def debug_upload():
    """Debug the upload process step by step"""
    
    # Test configuration
    base_url = "https://file-server.stream-lineai.com"
    service_token = "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
    user_id = "wesman687@gmail.com"
    folder = "veo/videos"
    
    # Test file content
    file_content = b"This is a test file for debugging"
    filename = "debug_test.txt"
    mime_type = "text/plain"
    
    print(f"🔍 Testing upload with:")
    print(f"   Base URL: {base_url}")
    print(f"   User ID: {user_id}")
    print(f"   Folder: {folder}")
    print(f"   Filename: {filename}")
    print(f"   File size: {len(file_content)} bytes")
    print()
    
    async with httpx.AsyncClient() as client:
        # Step 1: Initialize upload
        init_payload = {
            "mode": "single",
            "files": [{
                "name": filename,
                "size": len(file_content),
                "mime": mime_type
            }],
            "folder": folder,
            "meta": {
                "user_id": user_id
            }
        }
        
        print(f"📤 INIT PAYLOAD:")
        print(f"   {init_payload}")
        print()
        
        try:
            init_response = await client.post(
                f"{base_url}/v1/files/init",
                headers={
                    "X-Service-Token": service_token,
                    "Content-Type": "application/json"
                },
                json=init_payload
            )
            
            print(f"📥 INIT RESPONSE STATUS: {init_response.status_code}")
            print(f"📥 INIT RESPONSE HEADERS: {dict(init_response.headers)}")
            print(f"📥 INIT RESPONSE BODY: {init_response.text}")
            print()
            
            if init_response.status_code != 200:
                print(f"❌ INIT FAILED: {init_response.status_code}")
                return
            
            init_data = init_response.json()
            upload_id = init_data.get("uploadId")
            print(f"✅ UPLOAD ID: {upload_id}")
            print()
            
            # Step 2: Upload file data
            file_b64 = base64.b64encode(file_content).decode('utf-8')
            
            part_payload = {
                "uploadId": upload_id,
                "partNumber": 0,  # ✅ Fixed: partNumber instead of partIndex
                "chunkBase64": file_b64  # ✅ Fixed: chunkBase64 instead of data
            }
            
            print(f"📤 PART PAYLOAD:")
            print(f"   uploadId: {upload_id}")
            print(f"   partNumber: 0")
            print(f"   chunkBase64: {file_b64[:50]}... (truncated)")
            print()
            
            part_response = await client.post(
                f"{base_url}/v1/files/part",
                headers={
                    "X-Service-Token": service_token,
                    "Content-Type": "application/json"
                },
                json=part_payload
            )
            
            print(f"📥 PART RESPONSE STATUS: {part_response.status_code}")
            print(f"📥 PART RESPONSE: {part_response.text}")
            print()
            
            if part_response.status_code != 200:
                print(f"❌ PART UPLOAD FAILED: {part_response.status_code}")
                return
            
            # Step 3: Complete upload
            import hashlib
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            complete_payload = {
                "uploadId": upload_id,
                "parts": [{"data": file_b64}],
                "meta": {
                    "user_id": user_id,
                    "folder": folder,  # ✅ ADD THIS: Include folder in meta
                    "filename": filename  # ✅ ADD THIS: Include filename in meta
                },
                "sha256": file_hash
            }
            
            print(f"📤 COMPLETE PAYLOAD:")
            print(f"   uploadId: {upload_id}")
            print(f"   parts: [{{data: ...}}]")
            print(f"   meta: {{user_id: {user_id}, folder: {folder}, filename: {filename}}}")
            print(f"   sha256: {file_hash}")
            print()
            
            complete_response = await client.post(
                f"{base_url}/v1/files/complete",
                headers={
                    "X-Service-Token": service_token,
                    "Content-Type": "application/json"
                },
                json=complete_payload
            )
            
            print(f"📥 COMPLETE RESPONSE STATUS: {complete_response.status_code}")
            print(f"📥 COMPLETE RESPONSE: {complete_response.text}")
            print()
            
            if complete_response.status_code != 200:
                print(f"❌ COMPLETE FAILED: {complete_response.status_code}")
                return
            
            complete_data = complete_response.json()
            file_key = complete_data.get("fileKey")
            print(f"✅ UPLOAD SUCCESSFUL!")
            print(f"   File Key: {file_key}")
            print()
            
            # Check if file was created in the right folder
            print(f"🔍 Checking if file was created in {folder}...")
            
            list_response = await client.get(
                f"{base_url}/v1/files/all",
                headers={
                    "X-Service-Token": service_token
                },
                params={
                    "user_id": user_id,
                    "folder": folder
                }
            )
            
            print(f"📥 LIST RESPONSE STATUS: {list_response.status_code}")
            print(f"📥 LIST RESPONSE: {list_response.text}")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_upload())
