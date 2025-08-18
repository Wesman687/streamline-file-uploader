# Stream-Line Upload Server Deployment Guide

## Quick Deployment Steps

### 1. Clone Repository
```bash
git clone git@github.com:Wesman687/file-uploader.git
cd file-uploader/services/upload
```

### 2. Setup Environment
```bash
# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy and configure environment
cp env.template production.env
# Edit production.env with your actual values
```

### 3. Generate JWT Keys
```bash
# Create directories
sudo mkdir -p /etc/stream-line/keys

# Generate RSA key pair
openssl genrsa -out jwt_private.pem 2048
openssl rsa -in jwt_private.pem -pubout -out jwt_public.pem

# Install keys
sudo mv jwt_private.pem /etc/stream-line/keys/
sudo mv jwt_public.pem /etc/stream-line/keys/
sudo chown root:root /etc/stream-line/keys/jwt_private.pem
sudo chown ubuntu:ubuntu /etc/stream-line/keys/jwt_public.pem
sudo chmod 600 /etc/stream-line/keys/jwt_private.pem
sudo chmod 644 /etc/stream-line/keys/jwt_public.pem
sudo chmod 755 /etc/stream-line/keys/
```

### 4. Generate Secure Tokens
```bash
# Generate service token
openssl rand -hex 32

# Generate signing key  
openssl rand -hex 32

# Add these to your production.env file
```

### 5. Setup Storage
```bash
sudo mkdir -p /data/uploads/storage
sudo chown ubuntu:ubuntu /data/uploads
sudo chmod 755 /data/uploads
```

### 6. Install System Configuration
```bash
# Copy environment config
sudo cp production.env /etc/stream-line/upload.env

# Install systemd service
sudo cp upload-server.service /etc/systemd/system/
sudo systemctl enable upload-server
sudo systemctl start upload-server
```

### 7. Setup Nginx & SSL
```bash
# Create nginx config (adjust domain name)
sudo tee /etc/nginx/sites-available/file-server.domain.com > /dev/null << 'EOF'
server {
  listen 80;
  server_name file-server.domain.com;
  
  location /.well-known/acme-challenge/ { 
    root /var/www/html; 
  }
  
  client_max_body_size 5G;
  client_body_timeout 300s;
  proxy_read_timeout 300s;
  proxy_send_timeout 300s;
  
  location / {
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_request_buffering off;
    proxy_buffering off;
    proxy_pass http://127.0.0.1:5070;
  }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/file-server.domain.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d file-server.domain.com --non-interactive --agree-tos -m your-email@domain.com
```

### 8. Verify Deployment
```bash
# Check service status
sudo systemctl status upload-server

# Test endpoints
curl https://file-server.domain.com/healthz
curl https://file-server.domain.com/.well-known/jwks.json

# View logs
sudo journalctl -u upload-server -f
```

## Environment Variables Reference

See `env.template` for all required environment variables.

Key variables to customize:
- `PUBLIC_BASE_URL` - Your domain
- `AUTH_JWT_ISSUER` - Your JWT issuer
- `AUTH_JWT_AUDIENCE` - Your app name
- `AUTH_SERVICE_TOKEN` - Random 64-char hex
- `UPLOAD_SIGNING_KEY` - Random 64-char hex
- `JWKS_KID` - Your key identifier

## Security Notes

- Never commit actual `.env` files with secrets
- Use strong random tokens (openssl rand -hex 32)
- Protect private keys (600 permissions, root ownership)
- Use HTTPS in production
- Configure proper CORS if needed
