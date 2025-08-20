# 🐳 Stream-Line File Server - Windows Docker Deployment

## 🚀 **Quick Start for Windows**

### **Requirements**
- Windows 10/11 (64-bit)
- Docker Desktop for Windows ([Download here](https://www.docker.com/products/docker-desktop))
- PowerShell or Command Prompt (Administrator recommended)

---

## 📦 **Three Deployment Options**

### 1. **PowerShell Deployment** (Recommended)
```powershell
# Open PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Download and run deployment script
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/docker_deploy_windows.ps1" -OutFile "docker_deploy_windows.ps1"
.\docker_deploy_windows.ps1
```

### 2. **Command Prompt Deployment**
```cmd
# Open Command Prompt as Administrator
curl -o docker_deploy_windows.bat https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/docker_deploy_windows.bat
docker_deploy_windows.bat
```

### 3. **Fix Existing Deployment**
```powershell
# If you have issues with existing deployment
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/docker_fix_windows.ps1" -OutFile "docker_fix_windows.ps1"
.\docker_fix_windows.ps1
```

---

## 📋 **What Gets Installed**

### **Default Location**: `C:\streamline-docker`

### **Services**:
- **File Server**: http://localhost:8000
- **nginx Proxy**: http://localhost (optional)

### **Files Created**:
- `docker-compose.yml` - Container orchestration
- `Dockerfile` - File server container
- `.env.docker` - Environment configuration
- `nginx.conf` - Web server configuration
- `test_deployment.bat` - Quick test script
- `test_deployment.ps1` - PowerShell test script
- `manage.ps1` - Management commands
- `DEPLOYMENT_INFO.txt` - Deployment details

---

## 🔧 **Management Commands**

### **PowerShell Management**
```powershell
# Load management functions
.\manage.ps1

# Available commands:
Show-Status      # Show container status
Show-Logs        # Show live logs
Stop-Server      # Stop all services
Start-Server     # Start all services
Restart-Server   # Restart all services
Test-Server      # Test server health
```

### **Docker Commands**
```cmd
# Check status
docker-compose ps

# View logs
docker-compose logs -f file-server

# Stop services
docker-compose down

# Start services
docker-compose up -d

# Restart services
docker-compose restart
```

---

## 🧪 **Testing Your Deployment**

### **Quick Test**
```cmd
test_deployment.bat
```

### **PowerShell Test**
```powershell
.\test_deployment.ps1
```

### **Manual Test**
Open browser and visit:
- **File Server**: http://localhost:8000/healthz
- **nginx Proxy**: http://localhost/healthz

---

## 🚀 **Integration with Your Applications**

### **Service Token**
```
ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340
```

### **Python Client Library**
```powershell
# Download client library
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/streamline_file_client.py" -OutFile "streamline_file_client.py"
```

### **Usage Example**
```python
from streamline_file_client import StreamLineFileClient

# Initialize client
client = StreamLineFileClient("ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340")

# Upload file
result = client.upload_file("user123", "C:\\path\\to\\file.jpg", "profile_pictures")
print(f"File URL: {result['public_url']}")

# File is immediately accessible at:
# http://localhost:8000/storage/user123/profile_pictures/filename.jpg
```

### **Web Integration**
```html
<!-- Display uploaded image -->
<img src="http://localhost:8000/storage/user123/profile_pictures/avatar.jpg" alt="Profile">

<!-- Download link -->
<a href="http://localhost:8000/storage/user123/documents/report.pdf" download>Download Report</a>
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **Docker not running**
   - Start Docker Desktop
   - Wait for it to fully initialize

2. **Port conflicts**
   - Make sure ports 8000 and 80 are available
   - Stop other services using these ports

3. **Permission errors**
   - Run PowerShell/Command Prompt as Administrator
   - Check Docker Desktop permissions

4. **Container won't start**
   - Check logs: `docker-compose logs file-server`
   - Rebuild: `docker-compose build --no-cache`

### **Reset Everything**
```powershell
# Stop and remove everything
docker-compose down -v
docker system prune -f

# Re-run deployment script
.\docker_deploy_windows.ps1
```

---

## 📁 **File Organization**

Your files will be organized as:
```
C:\streamline-docker\storage\
├── user123\
│   ├── profile_pictures\
│   │   └── avatar.jpg
│   ├── documents\
│   │   └── report.pdf
│   └── uploads\
│       └── file.txt
└── user456\
    └── media\
        └── video.mp4
```

**Direct URLs**:
- `http://localhost:8000/storage/user123/profile_pictures/avatar.jpg`
- `http://localhost:8000/storage/user123/documents/report.pdf`

---

## 🔐 **Security Notes**

### **For Development** (Default)
- Service token provided works out of the box
- Files accessible via direct URLs
- No user authentication required for file access

### **For Production**
1. Change the service token in `.env.docker`
2. Set up proper domain and SSL
3. Configure user authentication if needed
4. Adjust file size limits and quotas

---

## 🎉 **You're Ready!**

Your Stream-Line file server is now running on Windows with Docker. You can:

✅ **Upload files** using the service token  
✅ **Access files** via direct URLs  
✅ **Integrate** with any Windows application  
✅ **Scale** as needed  

**Start building your file-powered applications!** 🚀
