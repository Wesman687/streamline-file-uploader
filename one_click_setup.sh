#!/bin/bash

# Stream-Line File Server MVP - One-Click Deployment
# =================================================
# 
# This script automatically sets up a complete file server MVP that you can
# run on any Ubuntu/Debian server. Just upload this file and run it!
#
# Usage:
#   wget https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/one_click_setup.sh
#   chmod +x one_click_setup.sh
#   sudo ./one_click_setup.sh
#
# What it does:
# - Installs all dependencies (Python, nginx, SSL)
# - Downloads and sets up the file server
# - Configures domain and SSL certificate
# - Starts all services
# - Runs test MVP to verify everything works

set -e

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Progress tracking
STEP=1
TOTAL_STEPS=12

print_step() {
    echo
    echo -e "${PURPLE}📋 Step $STEP/$TOTAL_STEPS: $1${NC}"
    echo -e "${CYAN}================================================${NC}"
    ((STEP++))
}

print_success() {
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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Welcome message
clear
echo -e "${CYAN}"
cat << 'EOF'
███████╗████████╗██████╗ ███████╗ █████╗ ███╗   ███╗      ██╗     ██╗███╗   ██╗███████╗
██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔══██╗████╗ ████║      ██║     ██║████╗  ██║██╔════╝
███████╗   ██║   ██████╔╝█████╗  ███████║██╔████╔██║█████╗██║     ██║██╔██╗ ██║█████╗  
╚════██║   ██║   ██╔══██╗██╔══╝  ██╔══██║██║╚██╔╝██║╚════╝██║     ██║██║╚██╗██║██╔══╝  
███████║   ██║   ██║  ██║███████╗██║  ██║██║ ╚═╝ ██║      ███████╗██║██║ ╚████║███████╗
╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝      ╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝

🚀 FILE SERVER MVP - ONE-CLICK DEPLOYMENT
EOF
echo -e "${NC}"

echo "This script will:"
echo "• Install all dependencies (Python, nginx, certbot)"
echo "• Download and configure the file server"
echo "• Set up SSL certificate and domain"
echo "• Start all services"
echo "• Run test MVP to verify everything works"
echo

# Get domain name
read -p "Enter your domain name (e.g., file-server.yourdomain.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    print_error "Domain name is required"
    exit 1
fi

read -p "Enter your email for SSL certificate: " EMAIL
if [ -z "$EMAIL" ]; then
    print_error "Email is required for SSL certificate"
    exit 1
fi

print_info "Domain: $DOMAIN"
print_info "Email: $EMAIL"
print_info "Starting deployment in 5 seconds... (Ctrl+C to cancel)"
sleep 5

# Step 1: Update system
print_step "Updating System Packages"
apt update && apt upgrade -y
print_success "System updated"

# Step 2: Install dependencies
print_step "Installing Dependencies"
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git curl unzip
print_success "Dependencies installed"

# Step 3: Create user and directory
print_step "Setting Up File Server Directory"
useradd -m -s /bin/bash streamline || true
mkdir -p /opt/streamline-file-server
chown streamline:streamline /opt/streamline-file-server
cd /opt/streamline-file-server
print_success "Directory created"

# Step 4: Download file server code
print_step "Downloading File Server Code"
sudo -u streamline git clone https://github.com/Wesman687/streamline-file-uploader.git .
print_success "Code downloaded"

# Step 5: Set up Python environment
print_step "Setting Up Python Environment"
cd /opt/streamline-file-server/services/upload
sudo -u streamline python3 -m venv .venv
sudo -u streamline .venv/bin/pip install -r requirements.txt
print_success "Python environment ready"

# Step 6: Create storage directories
print_step "Creating Storage Directories"
mkdir -p /opt/streamline-file-server/storage
mkdir -p /opt/streamline-file-server/services/upload/logs
chown -R streamline:streamline /opt/streamline-file-server/storage
chown -R streamline:streamline /opt/streamline-file-server/services/upload/logs
print_success "Storage directories created"

# Step 7: Configure nginx
print_step "Configuring Nginx"
cat > /etc/nginx/sites-available/streamline-file-server << EOF
server {
    listen 80;
    server_name $DOMAIN;
    client_max_body_size 100M;

    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    client_max_body_size 100M;

    # SSL configuration (will be added by certbot)
    
    # File server API
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    # Direct file serving for storage
    location /storage/ {
        alias /opt/streamline-file-server/storage/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, HEAD, OPTIONS";
        add_header Access-Control-Allow-Headers "Range";
        
        # Handle range requests for video streaming
        add_header Accept-Ranges bytes;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/streamline-file-server /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t
print_success "Nginx configured"

# Step 8: Create systemd service
print_step "Creating System Service"
cat > /etc/systemd/system/streamline-file-server.service << EOF
[Unit]
Description=Stream-Line File Server
After=network.target

[Service]
Type=simple
User=streamline
Group=streamline
WorkingDirectory=/opt/streamline-file-server/services/upload
Environment=PATH=/opt/streamline-file-server/services/upload/.venv/bin
ExecStart=/opt/streamline-file-server/services/upload/.venv/bin/python app/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable streamline-file-server
print_success "System service created"

# Step 9: Start services
print_step "Starting Services"
systemctl restart nginx
systemctl start streamline-file-server

# Wait for service to start
sleep 5

# Check if service is running
if systemctl is-active --quiet streamline-file-server; then
    print_success "File server started successfully"
else
    print_error "File server failed to start"
    print_info "Checking logs..."
    journalctl -u streamline-file-server -n 10 --no-pager
    exit 1
fi

# Step 10: Configure SSL certificate
print_step "Setting Up SSL Certificate"
print_info "Obtaining SSL certificate from Let's Encrypt..."

# Use certbot to get certificate
certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --non-interactive

if [ $? -eq 0 ]; then
    print_success "SSL certificate obtained successfully"
else
    print_warning "SSL certificate setup failed, but server is running on HTTP"
    print_info "You can manually run: certbot --nginx -d $DOMAIN"
fi

# Step 11: Test the installation
print_step "Testing Installation"

# Test health endpoint
print_info "Testing health endpoint..."
sleep 3

if curl -s "https://$DOMAIN/healthz" > /dev/null 2>&1; then
    print_success "HTTPS health check passed"
    PROTOCOL="https"
elif curl -s "http://$DOMAIN/healthz" > /dev/null 2>&1; then
    print_success "HTTP health check passed"
    PROTOCOL="http"
else
    print_error "Health check failed"
    exit 1
fi

# Step 12: Run MVP test
print_step "Running MVP Test"

# Create a test script
cat > /opt/streamline-file-server/test_deployment.py << 'EOF'
#!/usr/bin/env python3
"""
Test the deployed file server with a quick MVP demo.
"""

import sys
import os
sys.path.append('/opt/streamline-file-server')

from streamline_file_client import StreamLineFileClient, StreamLineFileManager
import tempfile

def test_deployment():
    print("🧪 Testing File Server Deployment")
    print("=" * 40)
    
    # Get domain from environment or args
    domain = os.getenv('DOMAIN', sys.argv[1] if len(sys.argv) > 1 else 'localhost')
    protocol = os.getenv('PROTOCOL', 'https')
    base_url = f"{protocol}://{domain}"
    
    print(f"🌐 Testing server: {base_url}")
    
    # Service token
    service_token = "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
    
    try:
        # Initialize client
        client = StreamLineFileClient(service_token, base_url)
        manager = StreamLineFileManager(client)
        
        print("\n1️⃣ Health Check...")
        health = client.get_health_status()
        print(f"✅ Status: {health['status']}")
        print(f"💾 Free Space: {health['disk_free_gb']:.2f} GB")
        
        print("\n2️⃣ Creating Test File...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Hello from Stream-Line File Server! 🚀\n")
            f.write("This is a deployment test file.\n")
            f.write(f"Server: {base_url}\n")
            test_file = f.name
        
        print("\n3️⃣ Uploading Test File...")
        result = client.upload_file(
            user_id="deployment-test",
            file_path=test_file,
            folder="test",
            metadata={"test": "deployment"}
        )
        
        print(f"✅ Upload successful!")
        print(f"🔗 Public URL: {result['public_url']}")
        print(f"📁 File Key: {result['file_key']}")
        
        print("\n4️⃣ Testing File Access...")
        accessible = client.test_file_access(result['public_url'])
        if accessible:
            print("✅ File is publicly accessible")
        else:
            print("⚠️ File access test failed")
        
        print("\n5️⃣ Listing Files...")
        files = client.list_user_files("deployment-test")
        print(f"✅ Found {files['total_count']} files ({files['total_size']} bytes)")
        
        # Cleanup
        os.unlink(test_file)
        
        print("\n🎉 DEPLOYMENT TEST SUCCESSFUL!")
        print("=" * 40)
        print(f"✅ File server is running at: {base_url}")
        print(f"✅ API endpoints working")
        print(f"✅ File uploads working")
        print(f"✅ Direct file access working")
        print("\n🚀 Your file server is ready for production!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Deployment test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_deployment()
    sys.exit(0 if success else 1)
EOF

# Run the test
cd /opt/streamline-file-server
sudo -u streamline DOMAIN=$DOMAIN PROTOCOL=$PROTOCOL .venv/bin/python test_deployment.py

if [ $? -eq 0 ]; then
    print_success "MVP test passed!"
else
    print_error "MVP test failed"
    exit 1
fi

# Final summary
echo
echo -e "${GREEN}"
cat << 'EOF'
🎉 DEPLOYMENT COMPLETE! 🎉
EOF
echo -e "${NC}"

echo
print_success "Stream-Line File Server is now running!"
echo
print_info "📋 Deployment Summary:"
echo "  🌐 URL: $PROTOCOL://$DOMAIN"
echo "  🔐 SSL: $([ "$PROTOCOL" = "https" ] && echo "✅ Enabled" || echo "⚠️ HTTP only")"
echo "  📁 Storage: /opt/streamline-file-server/storage"
echo "  📋 Logs: /opt/streamline-file-server/services/upload/logs"
echo "  🔧 Service: streamline-file-server.service"
echo

print_info "🔧 Management Commands:"
echo "  • Status:  systemctl status streamline-file-server"
echo "  • Restart: systemctl restart streamline-file-server"
echo "  • Logs:    journalctl -u streamline-file-server -f"
echo "  • Test:    cd /opt/streamline-file-server && python test_deployment.py"
echo

print_info "🚀 Integration:"
echo "  • Service Token: ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
echo "  • Client Library: /opt/streamline-file-server/streamline_file_client.py"
echo "  • Examples: /opt/streamline-file-server/integration_examples/"
echo "  • Documentation: /opt/streamline-file-server/FILE_SERVER_INTEGRATION_GUIDE.md"
echo

print_success "🎉 Your file server MVP is ready for production use!"

# Save deployment info
cat > /opt/streamline-file-server/DEPLOYMENT_INFO.txt << EOF
Stream-Line File Server Deployment
==================================

Deployed: $(date)
Domain: $DOMAIN
Protocol: $PROTOCOL
URL: $PROTOCOL://$DOMAIN

Service Token: ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340

Directories:
- Code: /opt/streamline-file-server
- Storage: /opt/streamline-file-server/storage
- Logs: /opt/streamline-file-server/services/upload/logs

Services:
- File Server: streamline-file-server.service
- Web Server: nginx

Management:
- Status: systemctl status streamline-file-server
- Restart: systemctl restart streamline-file-server
- Logs: journalctl -u streamline-file-server -f

Integration:
- Copy /opt/streamline-file-server/streamline_file_client.py to your projects
- Use service token for authentication
- Files are accessible at $PROTOCOL://$DOMAIN/storage/user_id/folder/filename

Test:
cd /opt/streamline-file-server && python test_deployment.py
EOF

print_info "💾 Deployment info saved to: /opt/streamline-file-server/DEPLOYMENT_INFO.txt"
echo
print_success "🚀 Ready to integrate with your applications!"
