#!/bin/bash

# Quick Docker Fix for Stream-Line Fi# Create .env file with all required configuration
echo "Creating .env.docker file..."
cat > .env.docker << 'EOF'
# Stream-Line File Server - Docker Configuration
AUTH_SERVICE_TOKEN=ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340
UPLOAD_SIGNING_KEY=docker-production-signing-key-2025
UPLOAD_ROOT=/app
MAX_BODY_MB=5120
PER_USER_QUOTA_GB=500
LOG_DIR=/app/services/upload/logs
PORT=10000
BIND_HOST=0.0.0.0
PYTHONPATH=/app/services/upload
EOF==========================================
# 
# Run this in your docker-compose directory to fix the Python path issue

echo "🔧 Fixing Docker deployment..."

# Stop current containers
echo "Stopping containers..."
docker-compose down

# Update docker-compose.yml to remove version and add PYTHONPATH
echo "Updating docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
services:
  file-server:
    build: .
    ports:
      - "10000:10000"
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/services/upload/logs
    env_file:
      - .env.docker
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:10000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./storage:/var/www/storage:ro
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - file-server
    restart: unless-stopped
EOF

# Create .env file with all required configuration
echo "Creating .env.docker file..."
cat > .env.docker << 'EOF'
# Create .env file with all required configuration
echo "Creating .env.docker file..."
cat > .env.docker << 'EOF'
# Stream-Line File Server - Docker Configuration
AUTH_SERVICE_TOKEN=ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340
UPLOAD_SIGNING_KEY=docker-production-signing-key-2025
UPLOAD_ROOT=/app
MAX_BODY_MB=5120
PER_USER_QUOTA_GB=500
LOG_DIR=/app/services/upload/logs
PORT=8000
BIND_HOST=0.0.0.0
PYTHONPATH=/app/services/upload
EOF
EOF

# Update Dockerfile to fix Python path
echo "Updating Dockerfile..."
cat > Dockerfile << 'EOF'
# Stream-Line File Server - Docker Deployment
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -s /bin/bash streamline

# Set working directory
WORKDIR /app

# Clone repository
RUN git clone https://github.com/Wesman687/streamline-file-uploader.git .

# Install Python dependencies
WORKDIR /app/services/upload
RUN pip install -r requirements.txt

# Create storage and logs directories
RUN mkdir -p /app/storage /app/services/upload/logs
RUN chown -R streamline:streamline /app

# Switch to app user
USER streamline

# Set Python path so imports work correctly
ENV PYTHONPATH=/app/services/upload

# Set application environment variables
ENV LOG_DIR=/app/services/upload/logs
ENV UPLOAD_ROOT=/app
ENV AUTH_SERVICE_TOKEN=ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340
ENV UPLOAD_SIGNING_KEY=production-signing-key-for-docker

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Start the server from the correct directory
WORKDIR /app/services/upload
CMD ["python", "app/main.py"]
EOF

# Rebuild and start
echo "Rebuilding containers..."
docker-compose build --no-cache

echo "Starting containers..."
docker-compose up -d

# Wait and test
echo "Waiting for services to start..."
sleep 15

echo "Testing deployment..."
if curl -s http://localhost:8000/healthz > /dev/null; then
    echo "✅ File server is running!"
    echo "🌐 Access at: http://localhost:8000"
    echo "📋 Health: http://localhost:8000/healthz"
    echo "📖 Docs: http://localhost:8000/docs"
else
    echo "❌ Service still not responding. Check logs:"
    echo "docker-compose logs file-server"
fi

echo "🔧 Fix complete!"
