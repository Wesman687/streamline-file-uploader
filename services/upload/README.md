# Stream-Line Upload Server

🚀 **PRODUCTION STATUS: LIVE** - https://file-server.stream-lineai.com

A production-ready file upload and management service for Stream-Line customers. This service provides single & chunked uploads, batch ZIP downloads, signed URLs with HMAC authentication, and comprehensive metadata management.

## ✅ Live Features

- **File Upload API** - Multiple upload modes (single, chunked, batch)
- **File Listing** - `/v1/files/all` endpoint with folder filtering
- **Direct Storage Access** - Public URLs: `/storage/{user-id}/{path}`
- **JWT Authentication** - Full Stream-Line integration with JWKS
- **Service Authentication** - API access for Stream-Line services
- **Video Streaming** - HTTP range requests for media files
- **SSL/HTTPS** - Let's Encrypt certificate with auto-renewal
- **Systemd Service** - Auto-restart and boot persistence

## Features

- **Multiple Upload Modes**: Single-shot, chunked, and batch uploads
- **Authentication**: Stream-Line JWT for end-users, service tokens for internal APIs
- **Signed URLs**: HMAC-secured URLs with expiration and range support
- **Batch Downloads**: ZIP streaming for multiple files
- **Quota Management**: Per-user storage quotas
- **Production Ready**: Systemd service, Nginx reverse proxy, SSL support

## Architecture

```
services/upload/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── routes/
│   │   └── files.py         # File management API routes
│   ├── security/
│   │   └── jwt.py           # JWT validation and service auth
│   ├── core/
│   │   ├── storage.py       # File storage management
│   │   ├── signer.py        # HMAC URL signing
│   │   └── zipper.py        # ZIP streaming for batch downloads
│   ├── models/
│   │   └── __init__.py      # Pydantic data models
│   └── utils/
│       └── __init__.py      # Utility functions
├── requirements.txt         # Python dependencies
├── upload.env.template      # Environment configuration template
├── upload-server.service    # Systemd service configuration
├── nginx-file-server.conf   # Nginx reverse proxy configuration
├── deploy.sh               # Automated deployment script
└── README.md               # This file
```

## Quick Start

### 1. Deploy the Service

```bash
cd services/upload
./deploy.sh
```

The deployment script will:

- Install system dependencies (Python, Nginx, Certbot)
- Create service user and directories
- Set up Python virtual environment
- Install systemd service
- Configure Nginx reverse proxy
- Set up SSL certificate (if DNS is configured)

### 2. Configure Environment

Edit `/etc/stream-line/upload.env`:

```bash
sudo nano /etc/stream-line/upload.env
```

**Required settings:**

```env
# Authentication (REQUIRED)
AUTH_JWT_PUBLIC_KEY_BASE64=<base64-encoded-pem-public-key>
AUTH_SERVICE_TOKEN=<secure-random-token>
UPLOAD_SIGNING_KEY=<secure-random-key-for-hmac>

# Server settings
PORT=5070
BIND_HOST=127.0.0.1
UPLOAD_ROOT=/data/uploads
PUBLIC_BASE_URL=https://file-server.stream-lineai.com

# Limits
MAX_BODY_MB=5120
PER_USER_QUOTA_GB=500
```

### 3. Start the Service

```bash
sudo systemctl start upload-server
sudo systemctl status upload-server
```

### 4. Check Logs

```bash
# Application logs
journalctl -u upload-server -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## File-Server API Documentation

Once deployed, API documentation is available at:

- **Swagger UI**: `https://file-server.stream-lineai.com/docs`
- **ReDoc**: `https://file-server.stream-lineai.com/redoc`

### Key Endpoints

#### Upload Workflow

1. **Initialize Upload**: `POST /v1/files/init`
2. **Upload Parts** (chunked): `POST /v1/files/part`
3. **Complete Upload**: `POST /v1/files/complete`

#### File Access

- **List All Files**: `GET /v1/files/all?user_id={user_id}&folder={folder}`
- **Get Signed URL**: `GET /v1/files/signed-url?key=...`
- **File Metadata**: `GET /v1/files/metadata/{key}`
- **Direct Access**: `GET /get/{encoded_key}?exp=...&sig=...`
- **Storage Path Access**: `GET /storage/{user_id}/{folder}/{filename}` (direct URL access)

#### Batch Operations

- **Create Batch**: `POST /v1/files/batch-download`
- **Download ZIP**: `GET /v1/files/batch-download/{token}`

#### Management

- **Delete File**: `DELETE /v1/files/{key}`
- **Health Check**: `GET /healthz`

### Authentication

**End-user routes** require Stream-Line JWT:

```http
Authorization: Bearer <jwt-token>
# OR
Cookie: auth_token=<jwt-token>
```

**Service routes** use service token:

```http
X-Service-Token: <service-token>
```

## File Storage Structure

Files are stored with user-based organization and optional folder structure:

```
/data/uploads/
├── storage/
│   └── {user_id}/
│       ├── {folder}/           # Optional folder (e.g., "main", "main/pictures")
│       │   ├── {uuid}_{filename}
│       │   └── {uuid}_{filename}.meta
│       └── {uuid}_{filename}   # Files without folder
└── .parts/          # Temporary chunks during upload
    └── {upload_id}/
        ├── metadata.json
        ├── part_000001
        └── part_000002
```

### Folder Support

You can organize uploads into folders by including a `folder` parameter:

```json
{
  "mode": "single",
  "files": [{ "name": "image.jpg", "size": 1024, "mime": "image/jpeg" }],
  "folder": "main/pictures"
}
```

This will store the file at: `storage/{user_id}/main/pictures/{uuid}_image.jpg`

## API Examples

### List All Files for a User

```bash
# List all files for a user (service authentication)
curl -H "X-Service-Token: <service-token>" \
     "https://file-server.stream-lineai.com/v1/files/all?user_id=user123"

# List files in a specific folder
curl -H "X-Service-Token: <service-token>" \
     "https://file-server.stream-lineai.com/v1/files/all?user_id=user123&folder=main/pictures"
```

Response:

```json
{
  "files": [
    {
      "key": "storage/user123/main/pictures/abc123_image.jpg",
      "filename": "image.jpg",
      "size": 1024,
      "mime": "image/jpeg",
      "created_at": "2025-08-18T09:48:00.809581",
      "folder": "main/pictures"
    }
  ],
  "total_count": 1,
  "total_size": 1024
}
```

### Direct Storage Path Access

You can also access files directly via their storage paths without authentication:

```bash
# Direct access to any file via storage path
https://file-server.stream-lineai.com/storage/user123/main/pictures/abc123_image.jpg
https://file-server.stream-lineai.com/storage/user123/videos/xyz789_video.mp4
https://file-server.stream-lineai.com/storage/user123/documents/def456_document.pdf
```

**Features:**

- No authentication required
- Supports HTTP range requests for video/audio streaming
- Proper MIME type detection from metadata
- HEAD requests supported for metadata queries
- Efficient streaming for large files

## Signed URLs

Signed URLs provide secure, time-limited access to files:

```
https://file-server.stream-lineai.com/get/{base64(key)}?exp=1234567890&sig=hmac_signature
```

- **Signature**: `HMAC_SHA256(key|exp, UPLOAD_SIGNING_KEY)`
- **Expiration**: Unix timestamp
- **Range Support**: HTTP Range requests for partial content

## Development

### Local Development Setup

```bash
# Clone and setup
git clone <repository>
cd services/upload

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AUTH_JWT_PUBLIC_KEY_BASE64="..."
export AUTH_SERVICE_TOKEN="test-token"
export UPLOAD_SIGNING_KEY="test-signing-key"
export UPLOAD_ROOT="./test-uploads"

# Run development server
python app/main.py
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when implemented)
pytest tests/
```

## Production Deployment

### System Requirements

- **OS**: Ubuntu 20.04+ (or compatible Linux distribution)
- **Python**: 3.8+
- **Memory**: 2GB+ RAM recommended
- **Storage**: Mounted volume at `/data/uploads`
- **Network**: Ports 80, 443 open for HTTPS

### Security Considerations

1. **File System Permissions**:

   ```bash
   sudo chown -R uploadsvc:uploadsvc /data/uploads
   sudo chmod 750 /data/uploads
   ```

2. **Firewall**: Only open ports 80 and 443. Keep port 5070 internal.

3. **Environment Variables**: Protect sensitive configuration:

   ```bash
   sudo chmod 600 /etc/stream-line/upload.env
   ```

4. **Regular Updates**: Keep system and dependencies updated.

### Monitoring

- **Health Check**: `GET /healthz` returns disk usage and writability
- **Logs**: Application logs via journald, access logs via Nginx
- **Metrics**: Monitor disk usage, response times, error rates

### Backup Strategy

1. **Configuration**: Backup `/etc/stream-line/upload.env`
2. **Data**: Regular backups of `/data/uploads`
3. **Database**: If metadata storage is added, backup database

## Troubleshooting

### Common Issues

1. **Service won't start**:

   ```bash
   journalctl -u upload-server -n 50
   ```

2. **Permission errors**:

   ```bash
   sudo chown -R uploadsvc:uploadsvc /opt/upload-server /data/uploads
   ```

3. **SSL certificate issues**:

   ```bash
   sudo certbot renew --dry-run
   ```

4. **Nginx configuration**:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### Performance Tuning

1. **Increase file limits**:

   ```ini
   # In upload-server.service
   LimitNOFILE=65535
   ```

2. **Nginx optimization**:

   ```nginx
   # In nginx configuration
   client_max_body_size 5G;
   sendfile on;
   tcp_nopush on;
   ```

3. **Python optimization**:
   ```bash
   # Consider using gunicorn for production
   pip install gunicorn
   ```

## License

This software is part of the Stream-Line platform and is proprietary to Stream-Line AI.

## Support

For support and issues:

- **Internal**: Contact the Stream-Line development team
- **Logs**: Check journalctl and Nginx logs for diagnostics
- **Health**: Monitor `/healthz` endpoint for system status
