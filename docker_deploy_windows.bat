@echo off
REM Stream-Line File Server - Windows Docker Deployment (Batch)
REM ===========================================================
REM 
REM Batch script for Windows Docker deployment using CMD
REM 
REM Usage:
REM   1. Open Command Prompt as Administrator
REM   2. docker_deploy_windows.bat

setlocal EnableDelayedExpansion

echo.
echo 🐳 STREAM-LINE FILE SERVER - WINDOWS DOCKER DEPLOYMENT
echo ========================================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  Warning: Not running as Administrator. Some operations may fail.
    echo Continue anyway? [Y/N]:
    set /p continue=
    if /i "!continue!" neq "Y" (
        echo Exiting...
        exit /b 1
    )
)

REM Check Docker
echo 🔄 Checking Docker installation...
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Docker not found. Please install Docker Desktop for Windows first.
    echo Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo ✅ Docker found

REM Check Docker Compose
echo 🔄 Checking Docker Compose...
docker-compose --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Docker Compose not found. Please ensure Docker Desktop is properly installed.
    pause
    exit /b 1
)
echo ✅ Docker Compose found

REM Check if Docker is running
echo 🔄 Checking Docker daemon...
docker info >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Docker daemon is not running. Please start Docker Desktop.
    pause
    exit /b 1
)
echo ✅ Docker daemon is running

REM Create deployment directory
echo 🔄 Creating deployment directory...
set "DEPLOY_DIR=C:\streamline-docker"
if exist "%DEPLOY_DIR%" (
    echo ⚠️  Directory %DEPLOY_DIR% already exists. Contents will be overwritten.
)
if not exist "%DEPLOY_DIR%" mkdir "%DEPLOY_DIR%"
cd /d "%DEPLOY_DIR%"
echo ✅ Created deployment directory: %DEPLOY_DIR%

REM Download configuration files using PowerShell
echo 🔄 Downloading configuration files...

powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/docker-compose.yml' -OutFile 'docker-compose.yml'"
if %errorLevel% neq 0 (
    echo ❌ Failed to download docker-compose.yml
    pause
    exit /b 1
)
echo ✅ Downloaded docker-compose.yml

powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/Dockerfile' -OutFile 'Dockerfile'"
if %errorLevel% neq 0 (
    echo ❌ Failed to download Dockerfile
    pause
    exit /b 1
)
echo ✅ Downloaded Dockerfile

powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/.env.docker' -OutFile '.env.docker'"
if %errorLevel% neq 0 (
    echo ❌ Failed to download .env.docker
    pause
    exit /b 1
)
echo ✅ Downloaded .env.docker

REM Create nginx configuration
echo 🔄 Creating nginx configuration...
(
echo events {
echo     worker_connections 1024;
echo }
echo.
echo http {
echo     include /etc/nginx/mime.types;
echo     default_type application/octet-stream;
echo.    
echo     client_max_body_size 100M;
echo.    
echo     upstream file-server {
echo         server file-server:8000;
echo     }
echo.    
echo     server {
echo         listen 80;
echo         server_name localhost;
echo.        
echo         # File server API
echo         location / {
echo             proxy_pass http://file-server;
echo             proxy_set_header Host $host;
echo             proxy_set_header X-Real-IP $remote_addr;
echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
echo             proxy_set_header X-Forwarded-Proto $scheme;
echo         }
echo.        
echo         # Direct file serving
echo         location /storage/ {
echo             alias /var/www/storage/;
echo             expires 1y;
echo             add_header Cache-Control "public, immutable";
echo             add_header Access-Control-Allow-Origin "*";
echo         }
echo     }
echo }
) > nginx.conf
echo ✅ Created nginx configuration

REM Create directories
echo 🔄 Creating storage and log directories...
if not exist "storage" mkdir "storage"
if not exist "logs" mkdir "logs"
if not exist "ssl" mkdir "ssl"
echo ✅ Created directories

REM Start services
echo 🔄 Building and starting Docker services...
echo This may take several minutes on first run...
docker-compose up --build -d
if %errorLevel% neq 0 (
    echo ❌ Failed to start Docker services
    echo Checking logs...
    docker-compose logs
    pause
    exit /b 1
)
echo ✅ Docker services started

REM Wait for services
echo 🔄 Waiting for services to start...
timeout /t 15 /nobreak >nul

REM Test deployment
echo 🔄 Testing deployment...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/healthz' -UseBasicParsing; if ($response.StatusCode -eq 200) { Write-Host '✅ File server is running!' -ForegroundColor Green } else { Write-Host '⚠️ File server responded with status:' $response.StatusCode -ForegroundColor Yellow } } catch { Write-Host '❌ File server is not responding' -ForegroundColor Red; exit 1 }"

if %errorLevel% neq 0 (
    echo Checking container status...
    docker-compose ps
    echo.
    echo Checking logs...
    docker-compose logs file-server
    pause
    exit /b 1
)

REM Create test batch file
echo 🔄 Creating test script...
(
echo @echo off
echo echo Testing file server deployment...
echo powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/healthz' -UseBasicParsing; if ($response.StatusCode -eq 200) { Write-Host '✅ File server is running!' -ForegroundColor Green; $health = $response.Content | ConvertFrom-Json; Write-Host 'Status:' $health.status; Write-Host 'Free Space:' $health.disk_free_gb 'GB' } else { Write-Host '❌ File server is not responding' -ForegroundColor Red } } catch { Write-Host '❌ File server test failed' -ForegroundColor Red }"
echo pause
) > test_deployment.bat
echo ✅ Created test script: test_deployment.bat

REM Create PowerShell management script
echo 🔄 Creating management script...
(
echo # Stream-Line File Server Management Script
echo function Show-Status { docker-compose ps }
echo function Show-Logs { docker-compose logs -f file-server }
echo function Stop-Server { docker-compose down }
echo function Start-Server { docker-compose up -d }
echo function Restart-Server { docker-compose restart }
echo function Test-Server { 
echo     try {
echo         $response = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing
echo         if ($response.StatusCode -eq 200) {
echo             Write-Host "✅ File server is running!" -ForegroundColor Green
echo             $health = $response.Content ^| ConvertFrom-Json
echo             Write-Host "Status: $($health.status)"
echo             Write-Host "Free Space: $($health.disk_free_gb) GB"
echo         }
echo     } catch {
echo         Write-Host "❌ File server is not responding" -ForegroundColor Red
echo     }
echo }
echo.
echo Write-Host "Stream-Line File Server Management Commands:" -ForegroundColor Blue
echo Write-Host "  Show-Status    - Show container status"
echo Write-Host "  Show-Logs      - Show live logs"
echo Write-Host "  Stop-Server    - Stop all services"
echo Write-Host "  Start-Server   - Start all services" 
echo Write-Host "  Restart-Server - Restart all services"
echo Write-Host "  Test-Server    - Test server health"
) > manage.ps1
echo ✅ Created management script: manage.ps1

REM Final summary
echo.
echo ✅ 🎉 Windows Docker deployment complete!
echo.
echo 📋 Access Information:
echo   🌐 File Server: http://localhost:8000
echo   🌐 nginx Proxy: http://localhost
echo   📁 Storage: %DEPLOY_DIR%\storage
echo   📋 Logs: %DEPLOY_DIR%\logs
echo.
echo 🔧 Management Commands:
echo   • Status:  docker-compose ps
echo   • Logs:    docker-compose logs -f file-server
echo   • Stop:    docker-compose down
echo   • Restart: docker-compose restart
echo   • Test:    test_deployment.bat
echo   • Manage:  powershell -ExecutionPolicy Bypass -File manage.ps1
echo.
echo 🚀 Integration:
echo   • Service Token: ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340
echo   • Base URL: http://localhost:8000
echo.
echo 📝 Next Steps:
echo   1. Test the deployment: test_deployment.bat
echo   2. Download client library for your applications
echo   3. Start integrating with your projects!

REM Save deployment info
(
echo Stream-Line File Server - Windows Docker Deployment
echo =================================================
echo.
echo Deployed: %date% %time%
echo Domain: localhost
echo URL: http://localhost:8000
echo nginx Proxy: http://localhost
echo.
echo Service Token: ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340
echo.
echo Directories:
echo - Deployment: %DEPLOY_DIR%
echo - Storage: %DEPLOY_DIR%\storage
echo - Logs: %DEPLOY_DIR%\logs
echo.
echo Docker Commands:
echo - Status: docker-compose ps
echo - Logs: docker-compose logs -f
echo - Stop: docker-compose down
echo - Restart: docker-compose restart
echo.
echo Integration:
echo - Use service token for authentication
echo - Base URL: http://localhost:8000
echo - Files accessible at: http://localhost:8000/storage/user_id/folder/filename
echo.
echo Test: test_deployment.bat
echo Manage: powershell -ExecutionPolicy Bypass -File manage.ps1
) > DEPLOYMENT_INFO.txt
echo ✅ 📝 Deployment info saved to DEPLOYMENT_INFO.txt

echo.
echo ✅ 🐳 Your Windows Docker file server is ready! 🎉
echo.
pause
