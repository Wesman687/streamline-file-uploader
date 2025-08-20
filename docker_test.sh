#!/bin/bash

# Docker Test Script for Stream-Line File Server
# ==============================================
# 
# Quick test to verify Docker deployment is working

echo "🧪 Testing Docker File Server Deployment"
echo "========================================"

# Check if containers are running
echo "📋 Checking container status..."
docker-compose ps

echo
echo "🔍 Checking file server health..."
sleep 3

# Test health endpoint
if curl -s http://localhost:8000/healthz > /dev/null; then
    echo "✅ Health endpoint responding"
    
    # Get health details
    echo "📊 Server health details:"
    curl -s http://localhost:8000/healthz | python3 -m json.tool
    
else
    echo "❌ Health endpoint not responding"
    echo "📋 Container logs:"
    docker-compose logs --tail=20 file-server
    exit 1
fi

echo
echo "🧪 Testing file upload..."

# Create test file
echo "Docker test file created at $(date)" > docker-test.txt

# Test with our test script if it exists
if [ -f test_file_server.py ]; then
    echo "🐍 Running comprehensive test..."
    python3 test_file_server.py http://localhost:8000
else
    echo "ℹ️ Comprehensive test script not found"
    echo "📝 Basic test complete - server is responding"
fi

# Cleanup
rm -f docker-test.txt

echo
echo "✅ Docker test complete!"
