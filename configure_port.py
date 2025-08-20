#!/usr/bin/env python3
"""
Stream-Line File Server - Port Configuration Utility
===================================================

This script helps configure a custom port for the file server
to avoid conflicts with other applications.
"""

import os
import sys
import json

def check_port_availability(port):
    """Check if a port is available."""
    import socket
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def find_available_port(start_port=10000, max_attempts=100):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        if check_port_availability(port):
            return port
    return None

def update_env_file(file_path, port):
    """Update or create an .env file with the new port."""
    env_content = f"""# Stream-Line File Server Configuration
PORT={port}
BIND_HOST=0.0.0.0
PYTHONPATH=/app/services/upload
AUTH_SERVICE_TOKEN=ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340
UPLOAD_SIGNING_KEY=production-signing-key-{port}
UPLOAD_ROOT=/app
LOG_DIR=/app/services/upload/logs
MAX_BODY_MB=5120
PER_USER_QUOTA_GB=500
"""
    
    with open(file_path, 'w') as f:
        f.write(env_content)

def update_docker_compose(port):
    """Update docker-compose.yml with the new port."""
    docker_compose_content = f"""services:
  file-server:
    build: .
    ports:
      - "{port}:10000"
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/services/upload/logs
    env_file:
      - .env.docker
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:10000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./storage:/var/www/storage:ro
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - file-server
    restart: unless-stopped
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose_content)

def main():
    """Main function."""
    print("🔧 Stream-Line File Server - Port Configuration")
    print("=" * 50)
    
    # Check current port usage
    default_port = 10000
    print(f"\n📋 Checking default port {default_port}...")
    
    if check_port_availability(default_port):
        print(f"✅ Port {default_port} is available")
        use_default = input(f"Use default port {default_port}? [Y/n]: ").strip().lower()
        
        if use_default in ['', 'y', 'yes']:
            selected_port = default_port
        else:
            selected_port = None
    else:
        print(f"❌ Port {default_port} is already in use")
        selected_port = None
    
    # Find alternative port if needed
    if selected_port is None:
        print("\n🔍 Finding available port...")
        
        custom_port = input("Enter a specific port (or press Enter to auto-find): ").strip()
        
        if custom_port:
            try:
                custom_port = int(custom_port)
                if check_port_availability(custom_port):
                    selected_port = custom_port
                else:
                    print(f"❌ Port {custom_port} is not available")
                    selected_port = find_available_port()
            except ValueError:
                print("❌ Invalid port number")
                selected_port = find_available_port()
        else:
            selected_port = find_available_port()
    
    if selected_port is None:
        print("❌ Could not find an available port")
        sys.exit(1)
    
    print(f"\n✅ Selected port: {selected_port}")
    
    # Update configuration files
    print("\n🔄 Updating configuration files...")
    
    # Update .env.docker
    update_env_file('.env.docker', selected_port)
    print("✅ Updated .env.docker")
    
    # Update .env (if exists)
    if os.path.exists('.env'):
        update_env_file('.env', selected_port)
        print("✅ Updated .env")
    
    # Update docker-compose.yml
    if os.path.exists('docker-compose.yml'):
        update_docker_compose(selected_port)
        print("✅ Updated docker-compose.yml")
    
    # Create configuration summary
    config_summary = {
        "port": selected_port,
        "url": f"http://localhost:{selected_port}",
        "health_check": f"http://localhost:{selected_port}/healthz",
        "service_token": "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"
    }
    
    with open('port_config.json', 'w') as f:
        json.dump(config_summary, f, indent=2)
    
    print("\n📋 Configuration Summary:")
    print(f"  Port: {selected_port}")
    print(f"  URL: http://localhost:{selected_port}")
    print(f"  Health Check: http://localhost:{selected_port}/healthz")
    print(f"  Config saved to: port_config.json")
    
    print("\n🚀 Next Steps:")
    if os.path.exists('docker-compose.yml'):
        print("  1. Restart Docker: docker-compose down && docker-compose up -d")
    else:
        print("  1. Start the server with the new port configuration")
    
    print(f"  2. Test: curl http://localhost:{selected_port}/healthz")
    print("  3. Update your application to use the new port")
    
    # Create a test script
    test_script = f"""#!/bin/bash
# Test the file server on port {selected_port}
echo "Testing file server on port {selected_port}..."
curl -s http://localhost:{selected_port}/healthz | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ Server is healthy: {{data.get(\\"status\\", \\"unknown\\")}}')
    print(f'Free space: {{data.get(\\"disk_free_gb\\", \\"unknown\\")}} GB')
except:
    print('❌ Server is not responding')
"
"""
    
    with open(f'test_port_{selected_port}.sh', 'w') as f:
        f.write(test_script)
    
    os.chmod(f'test_port_{selected_port}.sh', 0o755)
    print(f"  4. Quick test script created: test_port_{selected_port}.sh")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Configuration cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
