#!/bin/bash

# Stream-Line Upload Server Deployment Script
# This script sets up the upload server on the target system

set -e

echo "=== Stream-Line Upload Server Deployment ==="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root. Run as a regular user with sudo privileges."
   exit 1
fi

# Variables
SERVICE_USER="uploadsvc"
INSTALL_DIR="/opt/upload-server"
LOG_DIR="/var/log/upload-server"
DATA_DIR="/data/uploads"
ENV_FILE="/etc/stream-line/upload.env"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "1. Installing system dependencies..."

# Install Python, pip, and other dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx

echo "2. Creating service user and directories..."

# Create service user
sudo useradd -r -s /usr/sbin/nologin $SERVICE_USER || true

# Create directories
sudo mkdir -p $INSTALL_DIR $LOG_DIR $DATA_DIR /etc/stream-line
sudo chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR $LOG_DIR $DATA_DIR

echo "3. Setting up Python environment..."

# Copy application files
sudo cp -r app/ $INSTALL_DIR/
sudo cp requirements.txt $INSTALL_DIR/
sudo chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR

# Create virtual environment
sudo -u $SERVICE_USER python3 -m venv $INSTALL_DIR/.venv
sudo -u $SERVICE_USER $INSTALL_DIR/.venv/bin/pip install --upgrade pip
sudo -u $SERVICE_USER $INSTALL_DIR/.venv/bin/pip install -r $INSTALL_DIR/requirements.txt

echo "4. Setting up configuration..."

# Copy environment template if not exists
if [ ! -f "$ENV_FILE" ]; then
    sudo cp upload.env.template $ENV_FILE
    echo "⚠️  Please edit $ENV_FILE with your configuration!"
    echo "   Required settings:"
    echo "   - AUTH_JWT_PUBLIC_KEY_BASE64"
    echo "   - AUTH_SERVICE_TOKEN"
    echo "   - UPLOAD_SIGNING_KEY"
fi

echo "5. Setting up systemd service..."

# Install systemd service
sudo cp upload-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable upload-server

echo "6. Setting up Nginx..."

# Copy Nginx configuration
sudo cp nginx-file-server.conf /etc/nginx/sites-available/file-server.stream-lineai.com

# Enable site
sudo ln -sf /etc/nginx/sites-available/file-server.stream-lineai.com /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

echo "7. Setting up SSL certificate..."

# Note: This requires DNS to be properly configured
read -p "Is DNS configured for file-server.stream-lineai.com? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo certbot --nginx -d file-server.stream-lineai.com --non-interactive --agree-tos -m admin@stream-lineai.com || true
else
    echo "⚠️  Please configure DNS first, then run: sudo certbot --nginx -d file-server.stream-lineai.com"
fi

echo "8. Final setup..."

# Reload Nginx
sudo systemctl reload nginx

echo "=== Deployment Complete ==="
echo
echo "Next steps:"
echo "1. Edit $ENV_FILE with your configuration"
echo "2. Start the service: sudo systemctl start upload-server"
echo "3. Check status: sudo systemctl status upload-server"
echo "4. Check logs: journalctl -u upload-server -f"
echo
echo "API will be available at: https://file-server.stream-lineai.com"
echo "Documentation: https://file-server.stream-lineai.com/docs"
