#!/bin/bash

# Development runner script for Upload Server
# This script sets up a minimal development environment

set -e

echo "=== Stream-Line Upload Server - Development Mode ==="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Set development environment variables
export AUTH_JWT_PUBLIC_KEY_BASE64="dGVzdC1rZXktZm9yLWRldmVsb3BtZW50"  # "test-key-for-development" in base64
export AUTH_SERVICE_TOKEN="dev-service-token-change-in-production"
export UPLOAD_SIGNING_KEY="dev-signing-key-change-in-production"
export UPLOAD_ROOT="./dev-uploads"
export PUBLIC_BASE_URL="http://localhost:5070"
export PORT="5070"
export BIND_HOST="127.0.0.1"

# Create uploads directory
mkdir -p ./dev-uploads

echo "Environment configured for development"
echo "Upload directory: ./dev-uploads"
echo "Server will run on: http://localhost:5070"
echo ""

# Run the server
echo "Starting development server..."
python app/main.py
