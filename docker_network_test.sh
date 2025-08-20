#!/bin/bash

# Docker Networking Test for Stream-Line File Server
# =================================================
# 
# This script tests if the file server is properly configured for Docker networking

echo "🔍 Docker Networking Test"
echo "========================="

# Check if running in Docker
if [ -f /.dockerenv ] || [ "$DOCKER_CONTAINER" = "1" ]; then
    echo "✅ Running inside Docker container"
    DOCKER_ENV=true
else
    echo "ℹ️  Not running in Docker container"
    DOCKER_ENV=false
fi

echo
echo "📋 Network Configuration Check:"
echo "------------------------------"

# Check if file server is running
if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "✅ File server responding on localhost:8000"
    
    # Test from container perspective
    if [ "$DOCKER_ENV" = true ]; then
        echo "✅ File server accessible from inside container"
    else
        echo "ℹ️  File server running on host"
    fi
    
    # Get health details
    echo
    echo "📊 Server Health:"
    curl -s http://localhost:8000/healthz | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'  Status: {data.get(\"status\", \"unknown\")}')
    print(f'  Free Space: {data.get(\"disk_free_gb\", \"unknown\")} GB')
    print(f'  Writable: {data.get(\"writable\", \"unknown\")}')
except:
    print('  Could not parse health response')
"

else
    echo "❌ File server not responding on localhost:8000"
    
    # Check if it's running on 127.0.0.1 only
    if curl -s http://127.0.0.1:8000/healthz > /dev/null 2>&1; then
        echo "⚠️  File server only accessible on 127.0.0.1"
        echo "   This will prevent nginx from connecting in Docker"
        echo "   Fix: Set BIND_HOST=0.0.0.0 in environment"
    else
        echo "❌ File server not running at all"
    fi
fi

echo
echo "🔧 Docker Networking Requirements:"
echo "---------------------------------"
echo "  • File server must bind to 0.0.0.0:8000 (not 127.0.0.1)"
echo "  • nginx must be able to reach file-server:8000"
echo "  • Health check: curl http://file-server:8000/healthz"

# Test nginx connectivity if in Docker
if [ "$DOCKER_ENV" = true ]; then
    echo
    echo "🌐 nginx Connectivity Test:"
    echo "--------------------------"
    
    # Try to reach the file server as nginx would
    if command -v curl >/dev/null 2>&1; then
        if curl -s http://file-server:8000/healthz > /dev/null 2>&1; then
            echo "✅ nginx can reach file-server:8000"
        else
            echo "❌ nginx cannot reach file-server:8000"
            echo "   Check docker-compose.yml network configuration"
        fi
    else
        echo "ℹ️  curl not available for nginx connectivity test"
    fi
fi

echo
echo "🚀 Quick Fixes:"
echo "--------------"
echo "  1. Set BIND_HOST=0.0.0.0 in .env.docker"
echo "  2. Ensure PORT=8000 matches docker-compose.yml"
echo "  3. Restart containers: docker-compose restart"
echo "  4. Test: curl http://localhost:8000/healthz"
