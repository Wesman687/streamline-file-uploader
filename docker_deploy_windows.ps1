# Stream-Line File Server - Windows Docker Deployment
# ==================================================
# 
# PowerShell script for Windows Docker deployment
# 
# Usage:
#   1. Open PowerShell as Administrator
#   2. Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#   3. .\docker_deploy_windows.ps1

param(
    [string]$Domain = "localhost"
)

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

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "${Red}❌ $Message${Reset}"
}

Write-Host "${Blue}"
Write-Host "🐳 STREAM-LINE FILE SERVER - WINDOWS DOCKER DEPLOYMENT"
Write-Host "${Reset}"

Write-Host "This script will deploy the Stream-Line file server using Docker on Windows."
Write-Host "Domain: $Domain"
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Warning "This script should be run as Administrator for best results."
    Write-Host "Continue anyway? (y/N): " -NoNewline
    $continue = Read-Host
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "Exiting..."
        exit 1
    }
}

# Check Docker
Write-Step "Checking Docker installation..."
try {
    $dockerVersion = docker --version
    Write-Success "Docker found: $dockerVersion"
} catch {
    Write-Error-Custom "Docker not found. Please install Docker Desktop for Windows first."
    Write-Host "Download from: https://www.docker.com/products/docker-desktop"
    exit 1
}

# Check Docker Compose
Write-Step "Checking Docker Compose..."
try {
    $composeVersion = docker-compose --version
    Write-Success "Docker Compose found: $composeVersion"
} catch {
    Write-Error-Custom "Docker Compose not found. Please ensure Docker Desktop is properly installed."
    exit 1
}

# Check if Docker is running
Write-Step "Checking Docker daemon..."
try {
    docker info | Out-Null
    Write-Success "Docker daemon is running"
} catch {
    Write-Error-Custom "Docker daemon is not running. Please start Docker Desktop."
    exit 1
}

# Create deployment directory
Write-Step "Creating deployment directory..."
$deployDir = "C:\streamline-docker"
if (Test-Path $deployDir) {
    Write-Warning "Directory $deployDir already exists. Contents will be overwritten."
}
New-Item -ItemType Directory -Force -Path $deployDir | Out-Null
Set-Location $deployDir
Write-Success "Created deployment directory: $deployDir"

# Download configuration files
Write-Step "Downloading configuration files..."

try {
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/docker-compose.yml" -OutFile "docker-compose.yml"
    Write-Success "Downloaded docker-compose.yml"
} catch {
    Write-Error-Custom "Failed to download docker-compose.yml"
    exit 1
}

try {
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/Dockerfile" -OutFile "Dockerfile"
    Write-Success "Downloaded Dockerfile"
} catch {
    Write-Error-Custom "Failed to download Dockerfile"
    exit 1
}

try {
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/.env.docker" -OutFile ".env.docker"
    Write-Success "Downloaded .env.docker"
} catch {
    Write-Error-Custom "Failed to download .env.docker"
    exit 1
}

# Create nginx configuration
Write-Step "Creating nginx configuration..."
$nginxConfig = @"
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
        server_name $Domain;
        
        # File server API
        location / {
            proxy_pass http://file-server;
            proxy_set_header Host `$host;
            proxy_set_header X-Real-IP `$remote_addr;
            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto `$scheme;
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
"@

$nginxConfig | Out-File -FilePath "nginx.conf" -Encoding UTF8
Write-Success "Created nginx configuration"

# Create directories
Write-Step "Creating storage and log directories..."
New-Item -ItemType Directory -Force -Path "storage" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "ssl" | Out-Null
Write-Success "Created directories"

# Start services
Write-Step "Building and starting Docker services..."
Write-Host "This may take several minutes on first run..."

try {
    docker-compose up --build -d
    Write-Success "Docker services started"
} catch {
    Write-Error-Custom "Failed to start Docker services"
    Write-Host "Checking logs..."
    docker-compose logs
    exit 1
}

# Wait for services
Write-Step "Waiting for services to start..."
Start-Sleep -Seconds 15

# Test deployment
Write-Step "Testing deployment..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Success "File server is running!"
        
        # Parse health response
        $healthData = $response.Content | ConvertFrom-Json
        Write-Host "  Status: $($healthData.status)"
        Write-Host "  Free Space: $($healthData.disk_free_gb) GB"
        Write-Host "  Writable: $($healthData.writable)"
        
    } else {
        Write-Warning "File server responded with status: $($response.StatusCode)"
    }
} catch {
    Write-Error-Custom "File server is not responding"
    Write-Host "Checking container status..."
    docker-compose ps
    Write-Host ""
    Write-Host "Checking logs..."
    docker-compose logs file-server
    exit 1
}

# Test nginx proxy
Write-Step "Testing nginx proxy..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost/healthz" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Success "nginx proxy is working!"
    } else {
        Write-Warning "nginx proxy responded with status: $($response.StatusCode)"
    }
} catch {
    Write-Warning "nginx proxy is not responding (this is optional for basic functionality)"
}

# Create test script
Write-Step "Creating test script..."
$testScript = @"
# Test the file server deployment
`$response = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing
if (`$response.StatusCode -eq 200) {
    Write-Host "✅ File server is running!" -ForegroundColor Green
    `$health = `$response.Content | ConvertFrom-Json
    Write-Host "Status: `$(`$health.status)"
    Write-Host "Free Space: `$(`$health.disk_free_gb) GB"
} else {
    Write-Host "❌ File server is not responding" -ForegroundColor Red
}
"@

$testScript | Out-File -FilePath "test_deployment.ps1" -Encoding UTF8
Write-Success "Created test script: test_deployment.ps1"

# Final summary
Write-Host ""
Write-Success "🎉 Windows Docker deployment complete!"
Write-Host ""
Write-Host "📋 Access Information:"
Write-Host "  🌐 File Server: http://localhost:8000"
Write-Host "  🌐 nginx Proxy: http://localhost"
Write-Host "  📁 Storage: $deployDir\storage"
Write-Host "  📋 Logs: $deployDir\logs"
Write-Host ""
Write-Host "🔧 Management Commands:"
Write-Host "  • Status:  docker-compose ps"
Write-Host "  • Logs:    docker-compose logs -f file-server"
Write-Host "  • Stop:    docker-compose down"
Write-Host "  • Restart: docker-compose restart"
Write-Host "  • Test:    .\test_deployment.ps1"
Write-Host ""
Write-Host "🚀 Integration:"
Write-Host "  • Service Token: ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
Write-Host "  • Base URL: http://localhost:8000"
Write-Host ""
Write-Host "📝 Next Steps:"
Write-Host "  1. Test the deployment: .\test_deployment.ps1"
Write-Host "  2. Download client library for your applications"
Write-Host "  3. Start integrating with your projects!"

# Save deployment info
$deploymentInfo = @"
Stream-Line File Server - Windows Docker Deployment
=================================================

Deployed: $(Get-Date)
Domain: $Domain
URL: http://localhost:8000
nginx Proxy: http://localhost

Service Token: ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340

Directories:
- Deployment: $deployDir
- Storage: $deployDir\storage
- Logs: $deployDir\logs

Docker Commands:
- Status: docker-compose ps
- Logs: docker-compose logs -f
- Stop: docker-compose down
- Restart: docker-compose restart

Integration:
- Use service token for authentication
- Base URL: http://localhost:8000
- Files accessible at: http://localhost:8000/storage/user_id/folder/filename

Test: .\test_deployment.ps1
"@

$deploymentInfo | Out-File -FilePath "DEPLOYMENT_INFO.txt" -Encoding UTF8
Write-Success "📝 Deployment info saved to DEPLOYMENT_INFO.txt"

Write-Host ""
Write-Success "🐳 Your Windows Docker file server is ready! 🎉"
