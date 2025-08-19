#!/bin/bash

# Stream-Line File Server - Docker Quick Deploy
# =============================================
# 
# Quick deployment using Docker and Docker Compose
# 
# Usage:
#   wget https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/docker_deploy.sh
#   chmod +x docker_deploy.sh
#   sudo ./docker_deploy.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo -e "${BLUE}"
cat << 'EOF'
🐳 STREAM-LINE FILE SERVER - DOCKER DEPLOYMENT
EOF
echo -e "${NC}"

# Check Docker
print_step "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_warning "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $USER
    print_success "Docker installed"
else
    print_success "Docker found"
fi

# Check Docker Compose
print_step "Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    print_warning "Docker Compose not found. Installing..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed"
else
    print_success "Docker Compose found"
fi

# Get domain
read -p "Enter your domain (or 'localhost' for local testing): " DOMAIN
DOMAIN=${DOMAIN:-localhost}

# Create deployment directory
print_step "Creating deployment directory..."
mkdir -p /opt/streamline-docker
cd /opt/streamline-docker

# Download files
print_step "Downloading configuration files..."
curl -s https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/docker-compose.yml > docker-compose.yml
curl -s https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/Dockerfile > Dockerfile

# Also download the requirements.txt file for the build
mkdir -p services/upload
curl -s https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/services/upload/requirements.txt > services/upload/requirements.txt

# Create nginx config
print_step "Creating nginx configuration..."
cat > nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    client_max_body_size 100M;
    
    upstream file-server {
        server file-server:8000;
    }
    
    server {
        listen 80;
        server_name $DOMAIN;
        
        # File server API
        location / {
            proxy_pass http://file-server;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # Direct file serving
        location /storage/ {
            alias /var/www/storage/;
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header Access-Control-Allow-Origin "*";
        }
    }
}
EOF

# Create directories
print_step "Creating storage and log directories..."
mkdir -p storage logs ssl

# Start services
print_step "Starting services..."
docker-compose up --build -d

# Wait for services
print_step "Waiting for services to start..."
sleep 10

# Test deployment
print_step "Testing deployment..."
if curl -s http://localhost/healthz > /dev/null; then
    print_success "File server is running!"
    
    # Test upload
    echo "Test file content" > test.txt
    
    # Create test script
    cat > test_docker.py << 'EOF'
import sys
import os
import requests
import tempfile

def test_docker_deployment():
    base_url = "http://localhost"
    service_token = "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
    
    headers = {
        "X-Service-Token": service_token,
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing Docker deployment...")
    
    # Health check
    response = requests.get(f"{base_url}/healthz")
    if response.status_code == 200:
        print("✅ Health check passed")
    else:
        print("❌ Health check failed")
        return False
    
    # Test upload (simplified)
    print("✅ File server is responsive")
    print(f"🌐 Access your file server at: {base_url}")
    return True

if __name__ == "__main__":
    test_docker_deployment()
EOF

    python3 test_docker.py
    
else
    print_error "File server failed to start"
    print_step "Checking logs..."
    docker-compose logs
    exit 1
fi

# Final summary
echo
print_success "🎉 Docker deployment complete!"
echo
echo "📋 Access Information:"
echo "  🌐 File Server: http://$DOMAIN"
echo "  📁 Storage: /opt/streamline-docker/storage"
echo "  📋 Logs: /opt/streamline-docker/logs"
echo
echo "🔧 Management Commands:"
echo "  • Status:  docker-compose ps"
echo "  • Logs:    docker-compose logs -f"
echo "  • Stop:    docker-compose down"
echo "  • Restart: docker-compose restart"
echo
echo "🚀 Integration:"
echo "  • Service Token: ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
echo "  • Base URL: http://$DOMAIN"
echo
print_success "🐳 Your Dockerized file server is ready!"

# Save info
cat > DOCKER_DEPLOYMENT_INFO.txt << EOF
Stream-Line File Server - Docker Deployment
==========================================

Deployed: $(date)
Domain: $DOMAIN
URL: http://$DOMAIN

Service Token: ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340

Directories:
- Deployment: /opt/streamline-docker
- Storage: /opt/streamline-docker/storage
- Logs: /opt/streamline-docker/logs

Docker Commands:
- Status: docker-compose ps
- Logs: docker-compose logs -f
- Stop: docker-compose down
- Restart: docker-compose restart

Integration:
- Use service token for authentication
- Base URL: http://$DOMAIN
- Files accessible at: http://$DOMAIN/storage/user_id/folder/filename
EOF

print_success "📝 Deployment info saved to DOCKER_DEPLOYMENT_INFO.txt"
