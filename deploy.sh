#!/bin/bash
# Stream-Line Upload Server Deployment Script
# Run this script to deploy updates from GitHub

set -e  # Exit on any error

echo "🚀 Deploying Stream-Line Upload Server updates..."

# Navigate to project directory
cd /home/ubuntu/file-uploader

# Pull latest changes from GitHub
echo "📥 Pulling latest changes from GitHub..."
git pull origin main

# Check if there are Python dependency changes
if [ requirements.txt -nt services/upload/.venv/pyvenv.cfg ]; then
    echo "📦 Updating Python dependencies..."
    cd services/upload
    source .venv/bin/activate
    pip install -r requirements.txt
    cd ../..
fi

# Restart the service to apply changes
echo "🔄 Restarting upload server service..."
sudo systemctl restart upload-server

# Wait a moment for the service to start
sleep 3

# Check service status
echo "✅ Checking service status..."
if sudo systemctl is-active --quiet upload-server; then
    echo "✅ Upload server is running successfully!"
    
    # Test the health endpoint
    echo "🩺 Testing health endpoint..."
    if curl -sf https://file-server.stream-lineai.com/healthz > /dev/null; then
        echo "✅ Health check passed!"
        echo "🎉 Deployment completed successfully!"
    else
        echo "❌ Health check failed!"
        exit 1
    fi
else
    echo "❌ Upload server failed to start!"
    echo "📋 Service status:"
    sudo systemctl status upload-server
    exit 1
fi

echo ""
echo "📊 Current service status:"
sudo systemctl status upload-server --no-pager -l
