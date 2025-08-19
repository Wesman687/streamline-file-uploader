#!/usr/bin/env python3
"""
Stream-Line File Server MVP Demo
================================

This MVP demonstrates exactly how your applications should integrate 
with the Stream-Line file server. Run this script to see real examples.

Usage:
    python file_server_mvp.py
"""

import requests
import json
import base64
import os
import tempfile
from datetime import datetime
from typing import Optional, Dict, List

# Configuration
FILE_SERVER_URL = "https://file-server.stream-lineai.com"
SERVICE_TOKEN = "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"

class StreamLineFileClient:
    """
    Stream-Line File Server Client
    
    This is exactly how your applications should interact with the file server.
    Copy this class into your applications and adapt as needed.
    """
    
    def __init__(self, service_token: str, base_url: str = FILE_SERVER_URL):
        self.service_token = service_token
        self.base_url = base_url
        self.headers = {
            "X-Service-Token": self.service_token,
            "Content-Type": "application/json"
        }
    
    def upload_file(self, user_id: str, file_path: str, folder: str = None, 
                   metadata: Dict = None) -> Dict:
        """
        Upload a file to the file server.
        
        Args:
            user_id: The user who owns this file
            file_path: Local path to the file to upload
            folder: Optional folder organization (e.g., "documents", "main/pictures")
            metadata: Optional metadata dictionary
            
        Returns:
            Dict with 'file_key' and 'public_url'
        """
        print(f"📤 Uploading {file_path} for user {user_id}")
        
        # Get file info
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # Determine MIME type
        mime_types = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
            '.pdf': 'application/pdf', '.txt': 'text/plain',
            '.mp4': 'video/mp4', '.mov': 'video/quicktime',
            '.doc': 'application/msword', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        file_ext = os.path.splitext(file_name)[1].lower()
        mime_type = mime_types.get(file_ext, 'application/octet-stream')
        
        # Step 1: Initialize upload
        init_data = {
            "mode": "single",
            "files": [{
                "name": file_name,
                "size": file_size,
                "mime": mime_type
            }],
            "meta": {
                "user_id": user_id,
                **(metadata or {})
            }
        }
        
        if folder:
            init_data["folder"] = folder
            
        print(f"   Initializing upload...")
        response = requests.post(
            f"{self.base_url}/v1/files/init",
            headers=self.headers,
            json=init_data
        )
        response.raise_for_status()
        upload_session = response.json()
        upload_id = upload_session["uploadId"]
        
        # Step 2: Upload file data
        print(f"   Uploading file data...")
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Convert to base64
        file_b64 = base64.b64encode(file_data).decode('utf-8')
        
        complete_data = {
            "uploadId": upload_id,
            "parts": [{"data": file_b64}],
            "meta": {
                "user_id": user_id,
                **(metadata or {})
            }
        }
        
        response = requests.post(
            f"{self.base_url}/v1/files/complete",
            headers=self.headers,
            json=complete_data
        )
        response.raise_for_status()
        result = response.json()
        
        # Construct public URL
        file_key = result["fileKey"]
        # Extract filename from file_key (format: uuid_filename)
        original_filename = '_'.join(file_key.split('_')[1:])
        
        if folder:
            public_url = f"{self.base_url}/storage/{user_id}/{folder}/{original_filename}"
        else:
            public_url = f"{self.base_url}/storage/{user_id}/{original_filename}"
        
        print(f"   ✅ Upload complete!")
        print(f"   📁 File key: {file_key}")
        print(f"   🌐 Public URL: {public_url}")
        
        return {
            "file_key": file_key,
            "public_url": public_url,
            "original_name": file_name,
            "folder": folder
        }
    
    def list_user_files(self, user_id: str, folder: str = None) -> Dict:
        """
        List all files for a user, optionally filtered by folder.
        
        Args:
            user_id: The user whose files to list
            folder: Optional folder filter
            
        Returns:
            Dict with 'files', 'total_count', 'total_size'
        """
        print(f"📋 Listing files for user {user_id}" + (f" in folder '{folder}'" if folder else ""))
        
        params = {"user_id": user_id}
        if folder:
            params["folder"] = folder
        
        response = requests.get(
            f"{self.base_url}/v1/files/all",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"   Found {result['total_count']} files ({result['total_size']} bytes)")
        
        return result
    
    def get_health_status(self) -> Dict:
        """Get file server health status."""
        response = requests.get(f"{self.base_url}/healthz")
        response.raise_for_status()
        return response.json()
    
    def test_file_access(self, public_url: str) -> bool:
        """Test if a file is accessible via its public URL."""
        try:
            response = requests.head(public_url)
            return response.status_code == 200
        except:
            return False


class UserMediaManager:
    """
    Example: User Media Management System
    
    This shows how you might build a media management system
    for your users using the file server.
    """
    
    def __init__(self, file_client: StreamLineFileClient):
        self.client = file_client
    
    def setup_user_media_folders(self, user_id: str):
        """Set up standard folder structure for a new user."""
        print(f"🔧 Setting up media folders for user {user_id}")
        
        # This doesn't actually create folders (they're created on first upload)
        # But it shows the recommended structure
        folders = {
            "profile": "main/pictures",
            "documents": "documents", 
            "videos": "videos",
            "temp": "temp"
        }
        
        print("   Recommended folder structure:")
        for purpose, folder in folders.items():
            print(f"   📁 {purpose}: {folder}")
        
        return folders
    
    def set_profile_picture(self, user_id: str, image_path: str) -> str:
        """Upload and set a user's profile picture."""
        print(f"🖼️ Setting profile picture for user {user_id}")
        
        result = self.client.upload_file(
            user_id=user_id,
            file_path=image_path,
            folder="main/pictures",
            metadata={"type": "profile_picture", "uploaded_at": datetime.now().isoformat()}
        )
        
        # In a real app, you'd save this URL to your user database
        profile_url = result["public_url"]
        print(f"   ✅ Profile picture set: {profile_url}")
        
        return profile_url
    
    def upload_document(self, user_id: str, doc_path: str, doc_type: str = "general") -> Dict:
        """Upload a document to the user's document folder."""
        print(f"📄 Uploading document for user {user_id} (type: {doc_type})")
        
        # Organize by document type
        folder_map = {
            "contract": "documents/contracts",
            "invoice": "documents/invoices",
            "id": "documents/identification",
            "general": "documents"
        }
        
        folder = folder_map.get(doc_type, "documents")
        
        result = self.client.upload_file(
            user_id=user_id,
            file_path=doc_path,
            folder=folder,
            metadata={
                "document_type": doc_type,
                "uploaded_at": datetime.now().isoformat()
            }
        )
        
        print(f"   ✅ Document uploaded to: {folder}")
        return result
    
    def get_user_gallery(self, user_id: str) -> List[Dict]:
        """Get all images in user's gallery."""
        print(f"🖼️ Getting gallery for user {user_id}")
        
        files = self.client.list_user_files(user_id, folder="main/pictures")
        images = [f for f in files["files"] if f["mime"].startswith("image/")]
        
        print(f"   Found {len(images)} images")
        return images
    
    def get_user_documents(self, user_id: str) -> Dict:
        """Get user's documents organized by type."""
        print(f"📋 Getting documents for user {user_id}")
        
        all_docs = self.client.list_user_files(user_id, folder="documents")
        
        # Organize by subfolder
        organized = {}
        for doc in all_docs["files"]:
            folder_parts = doc["folder"].split("/")
            if len(folder_parts) > 1:
                doc_type = folder_parts[1]  # e.g., "contracts", "invoices"
            else:
                doc_type = "general"
            
            if doc_type not in organized:
                organized[doc_type] = []
            organized[doc_type].append(doc)
        
        print(f"   Documents organized into {len(organized)} categories")
        return organized


def create_demo_files():
    """Create some demo files for testing."""
    demo_files = {}
    
    # Create a demo text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a demo document for Stream-Line file server testing.\n")
        f.write(f"Created at: {datetime.now()}\n")
        f.write("This file demonstrates how to upload documents to the file server.")
        demo_files['document'] = f.name
    
    # Create a demo "image" file (just text, but with image extension)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jpg', delete=False) as f:
        f.write("DEMO-IMAGE-DATA")  # In real life, this would be binary image data
        demo_files['image'] = f.name
    
    return demo_files


def run_mvp_demo():
    """
    Run the complete MVP demonstration.
    
    This shows exactly how your applications should work with the file server.
    """
    print("🚀 Stream-Line File Server MVP Demo")
    print("=" * 50)
    
    # Initialize client
    client = StreamLineFileClient(SERVICE_TOKEN)
    media_manager = UserMediaManager(client)
    
    # Test server health
    print("\n1️⃣ Testing Server Health")
    print("-" * 30)
    health = client.get_health_status()
    print(f"   Server status: {health['status']}")
    print(f"   Disk space: {health['disk_free_gb']} GB free")
    print(f"   Storage writable: {health['writable']}")
    
    # Demo user
    demo_user_id = "demo-user-123"
    
    # Set up user folders
    print(f"\n2️⃣ Setting Up User Media Structure")
    print("-" * 30)
    media_manager.setup_user_media_folders(demo_user_id)
    
    # Create demo files
    print(f"\n3️⃣ Creating Demo Files")
    print("-" * 30)
    demo_files = create_demo_files()
    print(f"   Created demo document: {demo_files['document']}")
    print(f"   Created demo image: {demo_files['image']}")
    
    # Upload profile picture
    print(f"\n4️⃣ Uploading Profile Picture")
    print("-" * 30)
    profile_url = media_manager.set_profile_picture(demo_user_id, demo_files['image'])
    
    # Upload document
    print(f"\n5️⃣ Uploading Document")
    print("-" * 30)
    doc_result = media_manager.upload_document(demo_user_id, demo_files['document'], "general")
    
    # List all user files
    print(f"\n6️⃣ Listing User Files")
    print("-" * 30)
    all_files = client.list_user_files(demo_user_id)
    for file in all_files["files"]:
        print(f"   📁 {file['filename']} ({file['size']} bytes) in {file['folder']}")
    
    # Get user gallery
    print(f"\n7️⃣ Getting User Gallery")
    print("-" * 30)
    gallery = media_manager.get_user_gallery(demo_user_id)
    for image in gallery:
        print(f"   🖼️ {image['filename']} - {image['mime']}")
    
    # Get user documents
    print(f"\n8️⃣ Getting User Documents")
    print("-" * 30)
    documents = media_manager.get_user_documents(demo_user_id)
    for doc_type, docs in documents.items():
        print(f"   📄 {doc_type}: {len(docs)} documents")
        for doc in docs:
            print(f"      - {doc['filename']}")
    
    # Test file access
    print(f"\n9️⃣ Testing Direct File Access")
    print("-" * 30)
    test_urls = [profile_url, doc_result["public_url"]]
    for url in test_urls:
        is_accessible = client.test_file_access(url)
        status = "✅ Accessible" if is_accessible else "❌ Not accessible"
        print(f"   {status}: {url}")
    
    # Show integration examples
    print(f"\n🔟 Integration Examples")
    print("-" * 30)
    print("   HTML Examples:")
    print(f'   <img src="{profile_url}" alt="Profile Picture">')
    print(f'   <a href="{doc_result["public_url"]}" download>Download Document</a>')
    print()
    print("   Python Examples:")
    print(f'   profile_picture_url = "{profile_url}"')
    print(f'   document_url = "{doc_result["public_url"]}"')
    print()
    print("   JavaScript/React Examples:")
    print(f'   const profilePic = "{profile_url}";')
    print(f'   const documentLink = "{doc_result["public_url"]}";')
    
    # Cleanup
    print(f"\n🧹 Cleanup")
    print("-" * 30)
    for file_path in demo_files.values():
        os.unlink(file_path)
        print(f"   Deleted temp file: {file_path}")
    
    print(f"\n✅ MVP Demo Complete!")
    print("=" * 50)
    print("This demo shows exactly how your applications should:")
    print("• Upload files with proper organization")
    print("• List and retrieve user files")
    print("• Use direct URLs for file access")
    print("• Handle different file types (documents, images, etc.)")
    print("• Organize files into logical folders")
    print("• Integrate with your existing user management")
    print()
    print("Copy the StreamLineFileClient class into your applications!")


if __name__ == "__main__":
    try:
        run_mvp_demo()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to file server: {e}")
        print("Make sure the file server is running and accessible.")
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
