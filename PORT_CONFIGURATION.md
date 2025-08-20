# 🔧 Port Configuration Guide

## 🎯 **Default Port: 10000** (Changed from 8000)

The Stream-Line file server now uses **port 10000** by default to avoid conflicts with common development servers.

---

## ⚡ **Quick Port Configuration**

### **Use Default Port (10000)**
```bash
# All deployment scripts use port 10000 by default
# No configuration needed!
```

### **Use Custom Port**
```bash
# Download port configuration utility
wget https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/configure_port.py
python3 configure_port.py

# Follow interactive prompts to:
# ✅ Check port availability
# ✅ Find alternative ports
# ✅ Update all config files
# ✅ Create test scripts
```

### **Windows Custom Port**
```powershell
# Download port configuration utility
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/configure_port.py" -OutFile "configure_port.py"
python configure_port.py
```

---

## 🔄 **Environment Variable Method**

### **Set Custom Port Before Deployment**
```bash
# Linux/macOS
export PORT=12345
./docker_deploy.sh

# Windows PowerShell
$env:PORT = "12345"
.\docker_deploy_windows.ps1
```

### **Update Existing Deployment**
```bash
# Update .env.docker file
echo "PORT=12345" > .env.docker
echo "BIND_HOST=0.0.0.0" >> .env.docker
# ... add other variables

# Restart containers
docker-compose down
docker-compose up -d
```

---

## 🏢 **Multi-Server Environment Setup**

### **For Developers Running 5-6+ Apps**

#### **Option 1: Auto-Port Assignment**
```bash
# Use the port utility to find available ports
for app in app1 app2 app3 app4 app5; do
    mkdir $app-fileserver
    cd $app-fileserver
    wget https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/configure_port.py
    python3 configure_port.py  # Will auto-find available port
    wget https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/docker_deploy.sh
    ./docker_deploy.sh
    cd ..
done
```

#### **Option 2: Manual Port Assignment**
```bash
# Assign specific port ranges
export PORT=10001 && ./docker_deploy.sh  # App 1
export PORT=10002 && ./docker_deploy.sh  # App 2  
export PORT=10003 && ./docker_deploy.sh  # App 3
export PORT=10004 && ./docker_deploy.sh  # App 4
export PORT=10005 && ./docker_deploy.sh  # App 5
```

#### **Option 3: Port Ranges by Project**
```bash
# Development ports: 10000-10099
# Staging ports: 10100-10199  
# Production ports: 10200-10299

export PORT=10001  # Dev App 1
export PORT=10002  # Dev App 2
export PORT=10101  # Staging App 1
export PORT=10201  # Prod App 1
```

---

## 📋 **Port Reference Table**

| **Environment** | **Port Range** | **Example** |
|----------------|----------------|-------------|
| **Default** | 10000 | http://localhost:10000 |
| **Development** | 10000-10099 | 10001, 10002, 10003... |
| **Staging** | 10100-10199 | 10101, 10102, 10103... |
| **Production** | 10200-10299 | 10201, 10202, 10203... |
| **Testing** | 10300-10399 | 10301, 10302, 10303... |

---

## 🔧 **Application Integration**

### **Framework Configuration Examples**

#### **Django (Multiple File Servers)**
```python
# settings.py
FILE_SERVERS = {
    'user_uploads': {
        'url': 'http://localhost:10001',
        'token': 'token1'
    },
    'product_images': {
        'url': 'http://localhost:10002', 
        'token': 'token2'
    },
    'documents': {
        'url': 'http://localhost:10003',
        'token': 'token3'
    }
}

# Usage
from streamline_file_client import StreamLineFileClient

def upload_user_file(user_id, file_path):
    config = FILE_SERVERS['user_uploads']
    client = StreamLineFileClient(config['token'], config['url'])
    return client.upload_file(user_id, file_path, "uploads")
```

#### **Express.js (Node.js)**
```javascript
// config.js
const FILE_SERVERS = {
  development: 'http://localhost:10001',
  staging: 'http://localhost:10101',
  production: 'https://files.yourdomain.com'
};

const FILE_SERVER_URL = FILE_SERVERS[process.env.NODE_ENV || 'development'];
```

#### **React Frontend**
```javascript
// config.js
const config = {
  development: {
    fileServerUrl: 'http://localhost:10001'
  },
  production: {
    fileServerUrl: 'https://files.yourdomain.com'
  }
};

export const FILE_SERVER_URL = config[process.env.NODE_ENV].fileServerUrl;
```

---

## 🧪 **Testing Multiple Ports**

### **Test All Running Servers**
```bash
# Create a test script for all your ports
for port in 10001 10002 10003 10004 10005; do
    echo "Testing port $port..."
    curl -s http://localhost:$port/healthz | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ Port $port: {data.get(\"status\", \"unknown\")}')
except:
    print(f'❌ Port $port: Not responding')
"
done
```

### **Windows PowerShell Test**
```powershell
# Test multiple ports
$ports = @(10001, 10002, 10003, 10004, 10005)
foreach ($port in $ports) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$port/healthz" -UseBasicParsing
        Write-Host "✅ Port $port: Running" -ForegroundColor Green
    } catch {
        Write-Host "❌ Port $port: Not responding" -ForegroundColor Red
    }
}
```

---

## 🔄 **Migration from Port 8000**

### **If You Have Existing Port 8000 Deployments**

1. **Update Configuration**:
   ```bash
   # Download the fix script
   wget https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/docker_fix.sh
   ./docker_fix.sh
   ```

2. **Or Use Port Utility**:
   ```bash
   # Use the port configuration utility
   wget https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/configure_port.py
   python3 configure_port.py
   ```

3. **Update Your Applications**:
   ```python
   # Change from:
   FILE_SERVER_URL = "http://localhost:8000"
   
   # To:
   FILE_SERVER_URL = "http://localhost:10000"  # Or your custom port
   ```

---

## 🎯 **Best Practices**

✅ **Use the port utility** for automatic conflict detection  
✅ **Document your port assignments** in your team wiki  
✅ **Use environment variables** for different deployment environments  
✅ **Test all ports** after deployment  
✅ **Reserve port ranges** for different types of services  
✅ **Update application configs** when changing ports  

**The file server now works seamlessly in multi-application environments!** 🚀
