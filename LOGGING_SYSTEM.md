# 📋 Stream-Line Upload Server - Logging System

## 🎯 **Complete Logging Implementation**

Your Stream-Line Upload Server now has a **comprehensive logging system** that tracks every aspect of server operation and user activity.

## 📁 **Log Files Structure**

```
services/upload/logs/
├── server.log      # Server events, startup/shutdown, authentication
├── access.log      # All HTTP requests (JSON format)
├── activity.log    # User file operations (JSON format)  
└── error.log       # Application errors and exceptions
```

## 🔍 **What Gets Logged**

### **1. Server Logs** (`server.log`)
- ✅ Server startup and shutdown events
- ✅ JWT authentication success/failure
- ✅ Service token authentication events
- ✅ Application-level status messages

### **2. Access Logs** (`access.log`) 
- ✅ **Every HTTP request** with full details:
  - Client IP address (with proxy header support)
  - Request method, URL, and query parameters
  - Response status code and processing time
  - User agent and authentication type
  - Timestamp and user identification

### **3. Activity Logs** (`activity.log`)
- ✅ **File operations** by users:
  - File uploads (with metadata)
  - File downloads (direct storage access)
  - File listing requests
  - User ID, client IP, and file details
  - Folder organization tracking

### **4. Error Logs** (`error.log`)
- ✅ **Application errors** and exceptions:
  - Unhandled exceptions with stack traces
  - Authentication failures
  - File operation errors
  - System-level error details

## 🛠️ **Management Tools**

### **1. Log Viewer** (`view-logs.sh`)
```bash
cd /home/ubuntu/file-uploader/services/upload

# View log summary
./view-logs.sh

# View specific logs
./view-logs.sh access 50     # Last 50 access log entries
./view-logs.sh activity 20   # Last 20 activity entries
./view-logs.sh server 30     # Last 30 server entries
./view-logs.sh error         # All error entries

# Real-time monitoring
./view-logs.sh monitor       # Follow all logs live
```

### **2. Log Rotation** (`rotate-logs.sh`)
```bash
# Manual rotation (automatically happens when logs get large)
./rotate-logs.sh

# Automatic rotation when files exceed 100MB
# Keeps 10 compressed backups of each log type
# Cleans up old archives automatically
```

## 📊 **Sample Log Entries**

### **Access Log Entry (JSON)**
```json
{
  "timestamp": "2025-08-19 14:04:06",
  "client_ip": "15.204.248.186", 
  "method": "GET",
  "url": "https://file-server.stream-lineai.com/v1/files/all?user_id=test-user",
  "path": "/v1/files/all",
  "query_params": {"user_id": "test-user"},
  "status_code": 200,
  "response_time_ms": 14.04,
  "user_agent": "curl/7.81.0",
  "auth_type": "Service",
  "user_id": "Anonymous"
}
```

### **Activity Log Entry (JSON)**
```json
{
  "timestamp": "2025-08-19 14:04:20",
  "action": "file_download", 
  "user_id": "test-user",
  "client_ip": "15.204.248.186",
  "file_key": "storage/test-user/videos/xyz789_sample-video.mp4",
  "details": {
    "user_agent": "curl/7.81.0",
    "method": "GET", 
    "file_path": "videos/xyz789_sample-video.mp4"
  }
}
```

### **Server Log Entry**
```
2025-08-19 14:04:06,123 - server - INFO - Service token authentication successful
2025-08-19 13:59:57,356 - server - INFO - Upload Server started successfully!
```

## 🎯 **Perfect for Monitoring:**

### **User Activity Tracking**
- ✅ Which users are uploading/downloading files
- ✅ What files are being accessed most frequently  
- ✅ Client IP addresses and user agents
- ✅ File organization patterns (folders)

### **Performance Monitoring**
- ✅ Response times for all requests
- ✅ Error rates and failure patterns
- ✅ Authentication success/failure rates
- ✅ Server startup/restart events

### **Security Auditing**  
- ✅ Authentication attempts and outcomes
- ✅ File access patterns by user
- ✅ Unusual client behavior detection
- ✅ Error patterns that might indicate attacks

### **Operational Insights**
- ✅ Most popular files and folders
- ✅ Peak usage times and patterns
- ✅ File upload/download volume tracking
- ✅ System health and stability monitoring

## 🔄 **Automatic Features**

- **Log Rotation**: Automatically rotates large log files
- **JSON Formatting**: Easy parsing for analysis tools
- **Real-time Logging**: Live activity as it happens
- **Error Handling**: Never loses log data, even during errors
- **Performance**: Minimal overhead on server operations

---

**Your upload server now has enterprise-grade logging!** 📊  
**Monitor user activity, track performance, and audit security with comprehensive logs.** 🔍
