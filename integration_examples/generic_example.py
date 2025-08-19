"""
Generic Python Integration Example
=================================

This example shows how to use the Stream-Line file server client
in any Python application or script.
"""

import os
from pathlib import Path

# Import the Stream-Line client (copy streamline_file_client.py to your project)
from streamline_file_client import StreamLineFileClient, StreamLineFileManager

# Configuration
SERVICE_TOKEN = "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"

def main():
    """
    Example usage of the Stream-Line file client in a generic Python application.
    """
    print("🚀 Stream-Line File Server Integration Example")
    print("=" * 50)
    
    # Initialize clients
    client = StreamLineFileClient(SERVICE_TOKEN)
    manager = StreamLineFileManager(client)
    
    # Test user
    user_id = "example-user-123"
    
    # 1. Health Check
    print("\n1️⃣ Health Check")
    print("-" * 20)
    try:
        health = client.get_health_status()
        print(f"✅ Server Status: {health['status']}")
        print(f"💾 Disk Free: {health['disk_free_gb']:.2f} GB")
        print(f"📝 Writable: {health['writable']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # 2. Create sample files for testing
    print("\n2️⃣ Creating Sample Files")
    print("-" * 25)
    
    # Create a sample image file
    sample_image = create_sample_image()
    print(f"📸 Created sample image: {sample_image}")
    
    # Create a sample document
    sample_doc = create_sample_document()
    print(f"📄 Created sample document: {sample_doc}")
    
    # 3. Upload Profile Picture
    print("\n3️⃣ Uploading Profile Picture")
    print("-" * 30)
    try:
        profile_url = manager.upload_profile_picture(user_id, sample_image)
        print(f"✅ Profile picture uploaded!")
        print(f"🌐 URL: {profile_url}")
        
        # Test if accessible
        if client.test_file_access(profile_url):
            print("✅ File is accessible")
        else:
            print("❌ File is not accessible")
            
    except Exception as e:
        print(f"❌ Profile upload failed: {e}")
    
    # 4. Upload Document
    print("\n4️⃣ Uploading Document")
    print("-" * 22)
    try:
        doc_result = manager.upload_document(user_id, sample_doc, "contract")
        print(f"✅ Document uploaded!")
        print(f"🌐 URL: {doc_result['public_url']}")
        print(f"📊 Size: {doc_result['size']} bytes")
        print(f"📝 Type: {doc_result['mime']}")
        
    except Exception as e:
        print(f"❌ Document upload failed: {e}")
    
    # 5. List User Files
    print("\n5️⃣ Listing User Files")
    print("-" * 22)
    try:
        files = client.list_user_files(user_id)
        print(f"📋 Found {files['total_count']} files ({files['total_size']} bytes)")
        
        for file_info in files['files']:
            print(f"   📁 {file_info['filename']} ({file_info['size']} bytes)")
            
    except Exception as e:
        print(f"❌ File listing failed: {e}")
    
    # 6. Get Profile Picture
    print("\n6️⃣ Getting Profile Picture")
    print("-" * 27)
    try:
        current_profile = manager.get_user_profile_picture(user_id)
        if current_profile:
            print(f"✅ Current profile picture: {current_profile}")
        else:
            print("ℹ️ No profile picture found")
    except Exception as e:
        print(f"❌ Profile retrieval failed: {e}")
    
    # 7. Get Documents
    print("\n7️⃣ Getting User Documents")
    print("-" * 26)
    try:
        documents = manager.get_user_documents(user_id)
        print(f"📋 Found {len(documents)} documents")
        
        for doc in documents:
            print(f"   📄 {doc['filename']} - {doc['mime']}")
            
        # Get contracts specifically
        contracts = manager.get_user_documents(user_id, "contract")
        print(f"📄 Found {len(contracts)} contracts")
        
    except Exception as e:
        print(f"❌ Document retrieval failed: {e}")
    
    # 8. Integration Examples
    print("\n8️⃣ Integration Examples")
    print("-" * 25)
    print("Here's how you would use these URLs in your applications:")
    print()
    
    if 'profile_url' in locals():
        print("🌐 HTML Image Tag:")
        print(f'   <img src="{profile_url}" alt="Profile Picture">')
        print()
        
        print("🐍 Python/Django Template:")
        print(f'   {{{{ user.profile_picture_url }}}}')
        print()
        
        print("⚛️ React Component:")
        print(f'   <img src={{userProfileUrl}} alt="Profile" />')
        print()
    
    if 'doc_result' in locals():
        print("📄 Document Download Link:")
        print(f'   <a href="{doc_result["public_url"]}" download>Download Contract</a>')
        print()
    
    # 9. Database Integration Example
    print("\n9️⃣ Database Integration Pattern")
    print("-" * 32)
    print("In your application, store the URLs in your database:")
    print()
    print("SQL Example:")
    print("CREATE TABLE user_profiles (")
    print("    user_id VARCHAR(50) PRIMARY KEY,")
    print("    profile_picture_url VARCHAR(500),")
    print("    updated_at TIMESTAMP")
    print(");")
    print()
    print("UPDATE user_profiles SET ")
    print(f"    profile_picture_url = '{profile_url if 'profile_url' in locals() else 'URL_HERE'}',")
    print("    updated_at = NOW()")
    print(f"WHERE user_id = '{user_id}';")
    print()
    
    # 10. Cleanup
    print("\n🧹 Cleanup")
    print("-" * 10)
    try:
        os.unlink(sample_image)
        os.unlink(sample_doc)
        print("✅ Cleaned up temporary files")
    except:
        print("ℹ️ Cleanup completed")
    
    print("\n✅ Integration Example Complete!")
    print("=" * 35)
    print("Copy streamline_file_client.py to your project and start using it!")


def create_sample_image():
    """Create a simple sample image file."""
    import tempfile
    
    # Create a simple text file as a "fake" image for demo
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jpg', delete=False) as f:
        f.write("FAKE_IMAGE_DATA_FOR_DEMO")
        return f.name


def create_sample_document():
    """Create a sample document file."""
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""Sample Contract Document
======================

This is a sample contract document for testing the Stream-Line file server integration.

Contract Details:
- Party A: Example Company
- Party B: Sample User
- Date: 2025-08-19
- Terms: Example terms and conditions

This document demonstrates how files are uploaded and managed using the Stream-Line file server.
""")
        return f.name


class ApplicationFileManager:
    """
    Example of how you might integrate file management into your application.
    """
    
    def __init__(self, service_token: str, database_connection=None):
        self.client = StreamLineFileClient(service_token)
        self.manager = StreamLineFileManager(self.client)
        self.db = database_connection  # Your database connection
    
    def set_user_profile_picture(self, user_id: str, image_path: str):
        """
        Set a user's profile picture and update the database.
        """
        try:
            # Upload to file server
            profile_url = self.manager.upload_profile_picture(user_id, image_path)
            
            # Update database (pseudo-code)
            # self.db.execute(
            #     "UPDATE users SET profile_picture_url = %s WHERE id = %s",
            #     (profile_url, user_id)
            # )
            
            return profile_url
            
        except Exception as e:
            print(f"Profile picture update failed: {e}")
            raise
    
    def upload_user_document(self, user_id: str, doc_path: str, doc_type: str):
        """
        Upload a document and store metadata in database.
        """
        try:
            # Upload to file server
            result = self.manager.upload_document(user_id, doc_path, doc_type)
            
            # Store in database (pseudo-code)
            # self.db.execute("""
            #     INSERT INTO user_documents 
            #     (user_id, file_key, public_url, original_name, document_type, file_size)
            #     VALUES (%s, %s, %s, %s, %s, %s)
            # """, (
            #     user_id, result['file_key'], result['public_url'],
            #     result['original_name'], doc_type, result['size']
            # ))
            
            return result
            
        except Exception as e:
            print(f"Document upload failed: {e}")
            raise
    
    def get_user_files(self, user_id: str):
        """
        Get user files from database (faster than API calls).
        """
        # In a real application, you'd query your database
        # return self.db.execute(
        #     "SELECT * FROM user_documents WHERE user_id = %s ORDER BY uploaded_at DESC",
        #     (user_id,)
        # ).fetchall()
        
        # Fallback to API
        return self.client.list_user_files(user_id)


def batch_file_operations():
    """
    Example of batch operations for processing multiple files.
    """
    client = StreamLineFileClient(SERVICE_TOKEN)
    manager = StreamLineFileManager(client)
    
    # Process multiple files for multiple users
    users_and_files = [
        ("user1", ["/path/to/file1.jpg", "/path/to/file2.pdf"]),
        ("user2", ["/path/to/file3.png", "/path/to/file4.docx"]),
    ]
    
    for user_id, file_paths in users_and_files:
        print(f"Processing files for {user_id}...")
        
        for file_path in file_paths:
            if not Path(file_path).exists():
                print(f"  ⚠️ Skipping {file_path} (not found)")
                continue
                
            try:
                # Determine file type and upload accordingly
                if file_path.lower().endswith(('.jpg', '.png', '.gif')):
                    result = manager.upload_media(user_id, file_path, "photos")
                elif file_path.lower().endswith(('.pdf', '.doc', '.docx')):
                    result = manager.upload_document(user_id, file_path, "general")
                else:
                    result = client.upload_file(user_id, file_path, "misc")
                
                print(f"  ✅ Uploaded {Path(file_path).name} -> {result['public_url']}")
                
            except Exception as e:
                print(f"  ❌ Failed to upload {file_path}: {e}")


if __name__ == "__main__":
    main()
