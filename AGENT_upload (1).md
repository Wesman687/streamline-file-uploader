# Agent: **Upload Server** — production-only, standalone (file-server.stream-lineai.com)

This agent provides the **file system** for Stream‑Line customers: **single & chunked uploads**, **batch ZIP downloads**, **signed URLs** with HMAC, and metadata. It **only runs server-side** (no dev mode). Storage is an OVH-mounted filesystem.

> **Domains & Ports**
>
> - **Public domain:** `file-server.stream-lineai.com` (TLS via Nginx + Certbot)
> - **App listen port (prod):** `127.0.0.1:5070` (reverse-proxied by Nginx)
> - **No separate dev setup** — you will deploy directly to the server

---

## 0) Mission (hand this to the agent)

1) Scaffold a standalone FastAPI service:
```
services/upload
  app/main.py
  app/routes/files.py
  app/security/jwt.py
  app/core/storage.py
  app/core/signer.py
  app/core/zipper.py
  app/models/*.py (pydantic)
  app/utils/*.py
```
2) Accept **Stream‑Line JWT** for end-user routes; accept `X-Service-Token` for internal service calls from other agents.
3) Store files under `UPLOAD_ROOT=/data/uploads/users/{user_id}/yyyy/mm/dd/` on the OVH mount.
4) Provide **chunked** and **single-shot** upload modes, **signed URL** reads (HMAC) with **Range** support, and **batch ZIP** streaming.
5) Production-only deployment behind **Nginx** on `file-server.stream-lineai.com` with **systemd** service for robust restarts and one-command reloads.

---

## 1) Environment (`/etc/stream-line/upload.env`)

```
PORT=5070
BIND_HOST=127.0.0.1
UPLOAD_ROOT=/data/uploads
PUBLIC_BASE_URL=https://file-server.stream-lineai.com

# Auth
AUTH_JWT_PUBLIC_KEY_BASE64=...     # Stream-Line public key (base64 PEM)
AUTH_SERVICE_TOKEN=...             # service-to-service secret

# Signed URL
UPLOAD_SIGNING_KEY=...             # HMAC secret
SIGNED_URL_TTL_DEFAULT=3600

# Limits & quotas
MAX_BODY_MB=5120
PER_USER_QUOTA_GB=500
```

Mount your OVH volume to `/data/uploads` (owned by the runtime user, e.g., `uploadsvc:uploadsvc`).

---

## 2) Systemd unit (auto-restart + controlled reload)

Create the service user and folders:
```bash
sudo useradd -r -s /usr/sbin/nologin uploadsvc || true
sudo mkdir -p /opt/upload-server /var/log/upload-server
sudo chown -R uploadsvc:uploadsvc /opt/upload-server /var/log/upload-server /data/uploads
```

Install your app into `/opt/upload-server` (e.g., `git pull` or rsync the build). Create a virtualenv there.

**Unit file:** `/etc/systemd/system/upload-server.service`
```ini
[Unit]
Description=Stream-Line Upload Server (FastAPI via uvicorn)
After=network.target

[Service]
Type=simple
User=uploadsvc
Group=uploadsvc
EnvironmentFile=/etc/stream-line/upload.env
WorkingDirectory=/opt/upload-server
# Adjust path to your venv's uvicorn
ExecStart=/opt/upload-server/.venv/bin/uvicorn app.main:app --host ${BIND_HOST} --port ${PORT} --proxy-headers --forwarded-allow-ips="*"
Restart=always
RestartSec=5
LimitNOFILE=65535
# Optional: set resource limits
# MemoryMax=4G

# Log to journald (use journalctl) or forward to files via systemd
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Reload and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now upload-server
sudo systemctl status upload-server --no-pager
```

**Deploy/reload pattern** (no dev autoreload):
```bash
# pull new code / install deps
cd /opt/upload-server && git pull && . .venv/bin/activate && pip install -r requirements.txt
sudo systemctl restart upload-server
```

---

## 3) Nginx reverse proxy (TLS + Range + big uploads)

> This host may serve **multiple apps**. Use **separate server blocks** to avoid conflicts.
> Below only handles `file-server.stream-lineai.com` and proxies to `127.0.0.1:5070`.

### 3.1 Server block
`/etc/nginx/sites-available/file-server.stream-lineai.com`:
```nginx
server {
  listen 80;
  server_name file-server.stream-lineai.com;
  # Allow Certbot HTTP-01
  location /.well-known/acme-challenge/ { root /var/www/html; }
  location / { return 301 https://$host$request_uri; }
}

server {
  listen 443 ssl http2;
  server_name file-server.stream-lineai.com;

  # TLS (Certbot will manage these)
  ssl_certificate /etc/letsencrypt/live/file-server.stream-lineai.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/file-server.stream-lineai.com/privkey.pem;
  include /etc/letsencrypt/options-ssl-nginx.conf;
  ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

  # Large uploads + efficient serving
  client_max_body_size 5G;
  sendfile on;
  tcp_nopush on;
  tcp_nodelay on;

  # Proxy to Uvicorn
  location / {
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_request_buffering off;      # stream large bodies
    proxy_buffering off;
    proxy_pass http://127.0.0.1:5070;
  }
}
```

Enable and test:
```bash
sudo ln -s /etc/nginx/sites-available/file-server.stream-lineai.com /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 3.2 Certbot
```bash
sudo apt-get update && sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d file-server.stream-lineai.com --non-interactive --agree-tos -m admin@stream-lineai.com
# Auto-renew cron is installed by certbot; verify with:
systemctl list-timers | grep certbot
```

> Because you have **multiple sites**, keep each domain in its own file under `sites-available/` and enable only the intended symlinks in `sites-enabled/`.

---

## 4) HTTP API (unchanged from prior plan)

### Upload lifecycle
- `POST /v1/files/init` → `{ mode: "single"|"chunked"|"batch", files:[{name,size,mime}] }` → `{ uploadId, parts? }`
- `POST /v1/files/part` → `{ uploadId, partNumber, chunkBase64 }`
- `POST /v1/files/complete` → `{ uploadId, sha256, meta? }` → `{ key, size, mime, sha256 }`

### Download & metadata
- `GET /v1/files/signed-url?key=...&disposition=inline|attachment&ttl=3600`
- `GET /v1/files/metadata/{key}` → `{ size, mime, sha256, createdAt }`
- `POST /v1/files/batch-download` → `{ token }`
- `GET /v1/files/batch-download/{token}` → streams ZIP
- `DELETE /v1/files/{key}`

**Auth rules**
- End-user routes require valid Stream‑Line JWT (cookie or bearer) including `user_id`.
- Internal service calls may use header `X-Service-Token: <AUTH_SERVICE_TOKEN>`.

---

## 5) Signed URL design (HMAC)

- URL: `/get/{b64(key)}?exp=TIMESTAMP&sig=HMAC`
- `sig = HMAC_SHA256( key | exp , UPLOAD_SIGNING_KEY )`
- The app validates signature/expiry and serves the file with **Accept-Ranges** for seeking.

Optional: use `X-Accel-Redirect` to offload file IO to Nginx (`/internal/` alias to `/data/uploads/`).

---

## 6) Logging, rotation, and health

- App logs go to **journald**: `journalctl -u upload-server -f`.
- Nginx logs: `/var/log/nginx/access.log` and `error.log` (logrotate is preconfigured on most distros).
- Health check: `GET /healthz` returns `{ status, disk_free_gb, writable }`.

Optional extra logrotate for app:
`/etc/logrotate.d/upload-server` (only if you redirect to files instead of journald).

---

## 7) Firewall / security

- Open **443** on the host (HTTPS).
- Keep **5070** bound to **127.0.0.1** only.
- Enforce quotas by `PER_USER_QUOTA_GB`, per-IP rate-limits at Nginx (optional).
- Ensure permissions on `/data/uploads` are `uploadsvc:uploadsvc` (0700 or 0750).

---

## 8) Deliverables

- FastAPI app with routes + OpenAPI docs.
- HMAC signer/validator + JWT verifier.
- Chunked upload coordinator with temp-part files under `/data/uploads/.parts`.
- Batch ZIP streamer.
- Systemd service working and enabled; Nginx + Certbot configured for domain.