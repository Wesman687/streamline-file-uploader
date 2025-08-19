#!/bin/bash

# Stream-Line File Server Integration Deployment Script
# ====================================================
# 
# This script helps you deploy the Stream-Line file client to your projects.
# 
# Usage:
#   ./deploy_to_project.sh /path/to/your/project
#   ./deploy_to_project.sh /path/to/your/django/project
#   ./deploy_to_project.sh /path/to/your/flask/project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if target directory is provided
if [ $# -eq 0 ]; then
    print_error "Please provide target project directory"
    echo "Usage: $0 /path/to/your/project"
    exit 1
fi

TARGET_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Validate target directory
if [ ! -d "$TARGET_DIR" ]; then
    print_error "Target directory does not exist: $TARGET_DIR"
    exit 1
fi

print_info "Deploying Stream-Line File Client to: $TARGET_DIR"
echo

# 1. Copy main client library
print_info "1. Copying main client library..."
cp "$SCRIPT_DIR/streamline_file_client.py" "$TARGET_DIR/"
print_status "streamline_file_client.py copied"

# 2. Create integration examples directory
print_info "2. Creating integration examples..."
mkdir -p "$TARGET_DIR/streamline_integration_examples"
cp -r "$SCRIPT_DIR/integration_examples/"* "$TARGET_DIR/streamline_integration_examples/"
print_status "Integration examples copied"

# 3. Copy documentation
print_info "3. Copying documentation..."
cp "$SCRIPT_DIR/FILE_SERVER_INTEGRATION_GUIDE.md" "$TARGET_DIR/"
cp "$SCRIPT_DIR/INTEGRATION_PACKAGE.md" "$TARGET_DIR/"
print_status "Documentation copied"

# 4. Create environment template
print_info "4. Creating environment template..."
cat > "$TARGET_DIR/.env.streamline" << 'EOF'
# Stream-Line File Server Configuration
# ===================================
# 
# Add these to your environment variables or settings file

# Service token for file uploads
STREAMLINE_FILE_TOKEN=ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340

# File server URL (production)
STREAMLINE_FILE_SERVER_URL=https://file-server.stream-lineai.com

# Optional: Custom upload folders
STREAMLINE_PROFILE_FOLDER=profile_pictures
STREAMLINE_DOCUMENTS_FOLDER=documents
STREAMLINE_MEDIA_FOLDER=media
EOF
print_status "Environment template created (.env.streamline)"

# 5. Create quick start script
print_info "5. Creating quick start script..."
cat > "$TARGET_DIR/streamline_quickstart.py" << 'EOF'
#!/usr/bin/env python3
"""
Stream-Line File Server Quick Start
==================================

Run this script to test your integration and see examples.
"""

import os
import sys

# Add current directory to path so we can import the client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from streamline_file_client import StreamLineFileClient, StreamLineFileManager
    print("✅ Stream-Line client imported successfully!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Make sure streamline_file_client.py is in this directory")
    sys.exit(1)

def main():
    print("🚀 Stream-Line File Server Quick Start")
    print("=" * 40)
    
    # Service token
    service_token = "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
    
    # Initialize client
    client = StreamLineFileClient(service_token)
    manager = StreamLineFileManager(client)
    
    # Test connection
    print("\n1️⃣ Testing Connection...")
    try:
        health = client.get_health_status()
        print(f"✅ Server Status: {health['status']}")
        print(f"💾 Disk Free: {health['disk_free_gb']:.2f} GB")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    print("\n2️⃣ Usage Examples:")
    print("-" * 20)
    
    print("""
# Basic file upload
client = StreamLineFileClient("your-service-token")
result = client.upload_file("user123", "/path/to/file.jpg", "photos")
print(f"File URL: {result['public_url']}")

# High-level operations
manager = StreamLineFileManager(client)
profile_url = manager.upload_profile_picture("user123", "/path/to/avatar.jpg")
doc_result = manager.upload_document("user123", "/path/to/contract.pdf", "contract")

# List user files
files = client.list_user_files("user123")
print(f"User has {files['total_count']} files")

# In your database, store the URLs:
# user.profile_picture_url = profile_url
# Document.objects.create(user=user, file_url=doc_result['public_url'])
""")
    
    print("\n3️⃣ Next Steps:")
    print("-" * 15)
    print("• Check integration examples in: streamline_integration_examples/")
    print("• Read the full guide: FILE_SERVER_INTEGRATION_GUIDE.md")
    print("• Add environment variables from: .env.streamline")
    print("• Start integrating with your application!")
    
    print("\n✅ Ready to integrate! The file server is working perfectly.")

if __name__ == "__main__":
    main()
EOF

chmod +x "$TARGET_DIR/streamline_quickstart.py"
print_status "Quick start script created (streamline_quickstart.py)"

# 6. Detect framework and show specific instructions
print_info "6. Detecting project framework..."

if [ -f "$TARGET_DIR/manage.py" ]; then
    print_status "Django project detected!"
    echo
    print_info "Django Integration Steps:"
    echo "1. Add to your settings.py:"
    echo "   STREAMLINE_SERVICE_TOKEN = os.getenv('STREAMLINE_FILE_TOKEN')"
    echo "2. Check streamline_integration_examples/django_example.py"
    echo "3. Run: python manage.py shell"
    echo "4. Test: from streamline_file_client import StreamLineFileClient"
    
elif [ -f "$TARGET_DIR/app.py" ] || [ -f "$TARGET_DIR/main.py" ]; then
    print_status "Flask/FastAPI project detected!"
    echo
    print_info "Flask/FastAPI Integration Steps:"
    echo "1. pip install requests"
    echo "2. Check streamline_integration_examples/flask_example.py or fastapi_example.py"
    echo "3. Import: from streamline_file_client import StreamLineFileClient"
    
elif [ -f "$TARGET_DIR/requirements.txt" ] || [ -f "$TARGET_DIR/setup.py" ]; then
    print_status "Python project detected!"
    echo
    print_info "Python Integration Steps:"
    echo "1. pip install requests"
    echo "2. Import: from streamline_file_client import StreamLineFileClient"
    echo "3. Check streamline_integration_examples/generic_example.py"
    
else
    print_status "Generic project - integration files copied!"
fi

# 7. Final summary
echo
print_info "7. Deployment Summary"
echo "Files copied to $TARGET_DIR:"
echo "  ✅ streamline_file_client.py (main library)"
echo "  ✅ streamline_integration_examples/ (framework examples)"
echo "  ✅ FILE_SERVER_INTEGRATION_GUIDE.md (full documentation)"
echo "  ✅ .env.streamline (environment template)"
echo "  ✅ streamline_quickstart.py (test script)"

echo
print_status "Deployment complete!"
echo
print_info "Quick test your integration:"
echo "  cd $TARGET_DIR"
echo "  python3 streamline_quickstart.py"
echo
print_info "Service Token (add to your environment):"
echo "  STREAMLINE_FILE_TOKEN=ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
echo
print_status "Your project is ready to use the Stream-Line file server! 🎉"
