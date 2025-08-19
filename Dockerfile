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

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Start the server from the correct directory
WORKDIR /app/services/upload
CMD ["python", "app/main.py"]
