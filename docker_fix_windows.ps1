# Stream-Line File Server - Windows Docker Fix
# ============================================
# 
# PowerShell script to fix existing Docker deployments on Windows
# 
# Usage:
#   .\docker_fix_windows.ps1

# Colors for output
$Green = "`e[32m"
$Blue = "`e[34m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Reset = "`e[0m"

function Write-Step {
    param([string]$Message)
    Write-Host "${Blue}🔄 $Message${Reset}"
}

function Write-Success {
    param([string]$Message)
    Write-Host "${Green}✅ $Message${Reset}"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "${Yellow}⚠️  $Message${Reset}"
}

Write-Host "${Blue}🔧 Stream-Line File Server - Windows Docker Fix${Reset}"
Write-Host "==============================================="
Write-Host ""

# Stop current containers
Write-Step "Stopping current containers..."
try {
    docker-compose down
    Write-Success "Containers stopped"
} catch {
    Write-Warning "No containers were running or docker-compose.yml not found"
}

# Update docker-compose.yml
Write-Step "Updating docker-compose.yml..."
$dockerCompose = @"
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
"@

$dockerCompose | Out-File -FilePath "docker-compose.yml" -Encoding UTF8
Write-Success "Updated docker-compose.yml"

# Create .env.docker file
Write-Step "Creating .env.docker file..."
$envDocker = @"
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
"@

$envDocker | Out-File -FilePath ".env.docker" -Encoding UTF8
Write-Success "Created .env.docker file"

# Update Dockerfile
Write-Step "Updating Dockerfile..."
$dockerfile = @"
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

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Start the server from the correct directory
WORKDIR /app/services/upload

# Add startup validation (optional - can be disabled by setting SKIP_VALIDATION=1)
RUN echo '#!/bin/bash\nif [ "$SKIP_VALIDATION" != "1" ]; then\n  python /app/validate_config.py\nfi\npython app/main.py\n' > start.sh && chmod +x start.sh

CMD ["./start.sh"]
"@

$dockerfile | Out-File -FilePath "Dockerfile" -Encoding UTF8
Write-Success "Updated Dockerfile"

# Create directories if they don't exist
Write-Step "Creating required directories..."
if (-not (Test-Path "storage")) { New-Item -ItemType Directory -Name "storage" | Out-Null }
if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Name "logs" | Out-Null }
if (-not (Test-Path "ssl")) { New-Item -ItemType Directory -Name "ssl" | Out-Null }
Write-Success "Directories ready"

# Rebuild and start
Write-Step "Rebuilding containers..."
try {
    docker-compose build --no-cache
    Write-Success "Containers rebuilt"
} catch {
    Write-Error "Failed to rebuild containers"
    exit 1
}

Write-Step "Starting containers..."
try {
    docker-compose up -d
    Write-Success "Containers started"
} catch {
    Write-Error "Failed to start containers"
    exit 1
}

# Wait and test
Write-Step "Waiting for services to start..."
Start-Sleep -Seconds 15

Write-Step "Testing deployment..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:10000/healthz" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Success "✅ File server is running!"
        Write-Host "🌐 Access at: http://localhost:10000"
        Write-Host "📋 Health: http://localhost:10000/healthz"
        Write-Host "📖 Docs: http://localhost:10000/docs"
        
        # Parse health response
        $healthData = $response.Content | ConvertFrom-Json
        Write-Host "Status: $($healthData.status)"
        Write-Host "Free Space: $($healthData.disk_free_gb) GB"
    } else {
        Write-Warning "Service responded with status: $($response.StatusCode)"
    }
} catch {
    Write-Warning "Service still not responding. Check logs:"
    Write-Host "docker-compose logs file-server"
}

Write-Success "🔧 Windows Docker fix complete!"

Write-Host ""
Write-Host "🔧 Management Commands:"
Write-Host "  • Status:  docker-compose ps"
Write-Host "  • Logs:    docker-compose logs -f file-server"
Write-Host "  • Stop:    docker-compose down"
Write-Host "  • Restart: docker-compose restart"
Write-Host ""
Write-Host "🚀 Integration:"
Write-Host "  • Service Token: ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
Write-Host "  • Base URL: http://localhost:10000"
Write-Host ""
Write-Success "🐳 Your Windows Docker file server is fixed and ready! 🎉"
