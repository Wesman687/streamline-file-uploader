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

# Add startup validation (optional - can be disabled by setting SKIP_VALIDATION=1)
RUN echo '#!/bin/bash\nif [ "$SKIP_VALIDATION" != "1" ]; then\n  python /app/validate_config.py\nfi\npython app/main.py\n' > start.sh && chmod +x start.sh

CMD ["./start.sh"]
