#!/usr/bin/env python3
"""
Find Upload Folder - Stream-Line File Server
==========================================

This script helps you find where your uploaded files are stored.
"""

import os
import json
import requests
from pathlib import Path

def check_server_config(base_url):
    """Check server configuration to find upload paths."""
    try:
        # Try to get server health/config info
        response = requests.get(f"{base_url}/healthz", timeout=5)
        if response.status_code == 200:
            print(f"✅ Server responding at: {base_url}")
            return True
        else:
            print(f"⚠️  Server at {base_url} responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to {base_url}: {e}")
        return False

def find_storage_directories():
    """Find potential storage directories."""
    potential_locations = [
        # Windows Docker
        Path("C:/streamline-docker/storage"),
        # Current directory (any Docker)
        Path("./storage"),
        Path("../storage"),
        # Linux production
        Path("/home/ubuntu/file-uploader/storage"),
        Path("/opt/streamline-file-server/storage"),
        # Alternative locations
        Path("/data/uploads/storage"),
        Path("/app/storage"),
    ]
    
    found_locations = []
    
    for location in potential_locations:
        if location.exists() and location.is_dir():
            # Check if it has files
            files = list(location.rglob("*"))
            file_count = len([f for f in files if f.is_file()])
            found_locations.append({
                'path': str(location.absolute()),
                'files': file_count,
                'size_mb': sum(f.stat().st_size for f in files if f.is_file()) / (1024*1024)
            })
    
    return found_locations

def check_environment_variables():
    """Check environment variables for upload paths."""
    upload_root = os.getenv("UPLOAD_ROOT")
    if upload_root:
        storage_path = Path(upload_root) / "storage"
        return str(storage_path.absolute()) if storage_path.exists() else None
    return None

def main():
    """Main function."""
    print("🔍 Finding Stream-Line File Server Upload Folders")
    print("=" * 50)
    
    # Check common server URLs
    common_urls = [
        "http://localhost:10000",
        "http://localhost:8000", 
        "http://localhost:5000",
        "http://127.0.0.1:10000",
    ]
    
    print("\n📡 Checking for running servers...")
    active_servers = []
    for url in common_urls:
        if check_server_config(url):
            active_servers.append(url)
    
    if active_servers:
        print(f"\n✅ Found {len(active_servers)} active server(s):")
        for server in active_servers:
            print(f"  • {server}")
    else:
        print("\n⚠️  No active servers found on common ports")
    
    # Check environment variables
    print("\n🔧 Checking environment configuration...")
    env_path = check_environment_variables()
    if env_path:
        print(f"✅ UPLOAD_ROOT environment variable points to: {env_path}")
    else:
        print("ℹ️  No UPLOAD_ROOT environment variable set")
    
    # Find storage directories
    print("\n📁 Searching for storage directories...")
    storage_locations = find_storage_directories()
    
    if storage_locations:
        print(f"\n✅ Found {len(storage_locations)} storage location(s):")
        for i, location in enumerate(storage_locations, 1):
            print(f"\n{i}. {location['path']}")
            print(f"   Files: {location['files']}")
            print(f"   Size: {location['size_mb']:.2f} MB")
            
            # Show sample files
            storage_path = Path(location['path'])
            sample_files = list(storage_path.rglob("*"))[:5]
            if sample_files:
                print("   Sample files:")
                for file in sample_files:
                    if file.is_file():
                        rel_path = file.relative_to(storage_path)
                        print(f"     📄 {rel_path}")
    else:
        print("\n❌ No storage directories found")
    
    # Show file structure explanation
    print("\n📋 File Structure Explanation:")
    print("Files are organized as:")
    print("  storage/")
    print("  ├── {user_id}/")
    print("  │   ├── {folder_name}/")
    print("  │   │   └── {filename}")
    print("  │   └── uploads/")
    print("  │       └── {filename}")
    print("  └── {another_user}/")
    print("      └── {folder}/")
    print("          └── {filename}")
    
    # Show access URLs
    if active_servers:
        print(f"\n🌐 File Access URLs (using {active_servers[0]}):")
        print("Files can be accessed directly via:")
        print(f"  {active_servers[0]}/storage/{{user_id}}/{{folder}}/{{filename}}")
        print("\nExample:")
        print(f"  {active_servers[0]}/storage/user123/profile_pictures/avatar.jpg")
        print(f"  {active_servers[0]}/storage/user123/documents/contract.pdf")
    
    # Provide next steps
    print("\n🚀 Next Steps:")
    if storage_locations:
        print("1. Navigate to one of the storage locations above")
        print("2. Look for your user_id folder")
        print("3. Files are organized by folder within each user directory")
    else:
        print("1. Check if the file server is running")
        print("2. Verify your deployment completed successfully")
        print("3. Check Docker containers: docker-compose ps")
    
    if active_servers:
        print(f"4. Test upload: curl -X POST {active_servers[0]}/upload/test_user/test_folder -F 'file=@your_file.txt'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Search cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
