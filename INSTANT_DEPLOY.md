# 🚀 Stream-Line File Server - One-Click MVP Deployment

Get your file server running in **5 minutes** on any server!

## 📦 Three Deployment Options

### Option 1: Full Production Setup (Recommended)
**One command to rule them all!** 🎯

```bash
wget https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/one_click_setup.sh
chmod +x one_click_setup.sh
sudo ./one_click_setup.sh
```

**What it does:**
- ✅ Installs all dependencies (Python, nginx, SSL)
- ✅ Downloads and configures the file server
- ✅ Sets up SSL certificate with Let's Encrypt
- ✅ Creates systemd service for auto-start
- ✅ Runs MVP test to verify everything works
- ✅ Ready for production traffic

**Requirements:** Ubuntu/Debian server with domain name

---

### Option 2: Docker Deployment (Quick & Clean)
**For containerized environments** 🐳

```bash
wget https://raw.githubusercontent.com/Wesman687/streamline-file-uploader/main/docker_deploy.sh
chmod +x docker_deploy.sh
sudo ./docker_deploy.sh
```

**What it does:**
- ✅ Installs Docker & Docker Compose
- ✅ Downloads and builds containers
- ✅ Sets up nginx proxy
- ✅ Starts all services
- ✅ Tests deployment

**Requirements:** Any Linux server

---

### Option 3: Manual Clone (For Developers)
**Full control deployment** 🛠️

```bash
git clone https://github.com/Wesman687/streamline-file-uploader.git
cd streamline-file-uploader
./deploy_to_project.sh /path/to/your/project
```

**What you get:**
- 📁 Complete source code
- 📚 Integration examples for Django/Flask/FastAPI
- 📖 Comprehensive documentation
- 🔧 Deployment scripts

---

## 🎯 After Deployment

### Your File Server Will Be Running At:
- **URL**: `https://your-domain.com` (Option 1) or `http://localhost` (Option 2)
- **Status**: Check at `/healthz`
- **Documentation**: Available at `/docs`

### Integration in Your Apps:
```python
# 1. Copy streamline_file_client.py to your project
# 2. Use this code:

from streamline_file_client import StreamLineFileClient

client = StreamLineFileClient("ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340")
result = client.upload_file("user123", "/path/to/file.jpg", "profile_pictures")

print(f"File available at: {result['public_url']}")
# File is immediately accessible at the public URL!
```

### Service Token:
```
ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340
```

---

## 🔥 What You Get

✅ **Production-Ready File Server**
- Upload, download, list, delete files
- Organized folder structure
- Direct file URLs (no auth needed for access)
- Service token authentication for uploads

✅ **Complete Integration Package** 
- Python client library
- Django, Flask, FastAPI examples
- Database integration patterns
- Error handling and logging

✅ **Zero-Configuration Deployment**
- Automatic SSL certificates
- nginx proxy configuration
- systemd service setup
- Storage and logging

✅ **Immediate File Access**
```html
<!-- Files are instantly accessible -->
<img src="https://your-server.com/storage/user123/profile_pictures/avatar.jpg">
<a href="https://your-server.com/storage/user123/documents/contract.pdf" download>Download</a>
```

---

## 🚀 Ready to Go!

1. **Pick your deployment method** (Option 1 recommended for production)
2. **Run the one-liner command**
3. **Copy the client library to your projects**
4. **Start uploading files!**

### The 422 error is completely fixed! 🎉

Your file server will be production-ready with working uploads, downloads, and direct file access. No more configuration headaches!

---

## 📞 Need Help?

- 📖 **Full Documentation**: Available after deployment
- 🧪 **Test Script**: Automatically runs after setup
- 🔧 **Integration Examples**: Complete code for all frameworks
- 📋 **Logs**: Available for troubleshooting

**Everything just works!** ✨
