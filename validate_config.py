#!/usr/bin/env python3
"""
Stream-Line File Server Configuration Validator
==============================================

This script validates that all required environment variables are set
and provides helpful error messages if configuration is missing.
"""

import os
import sys
from pathlib import Path

def print_status(message, status="info"):
    """Print colored status messages."""
    colors = {
        "success": "\033[92m✅",
        "warning": "\033[93m⚠️ ",
        "error": "\033[91m❌",
        "info": "\033[94mℹ️ "
    }
    reset = "\033[0m"
    print(f"{colors.get(status, '')} {message}{reset}")

def validate_environment():
    """Validate environment configuration."""
    print("🔍 Stream-Line File Server Configuration Validation")
    print("=" * 55)
    
    # Required environment variables with defaults
    required_with_defaults = {
        "AUTH_SERVICE_TOKEN": "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340",
        "UPLOAD_SIGNING_KEY": "default-signing-key-change-in-production",
        "UPLOAD_ROOT": "/app",
        "LOG_DIR": "/app/services/upload/logs",
        "PORT": "8000",
        "PYTHONPATH": "/app/services/upload"
    }
    
    # Optional environment variables
    optional_vars = {
        "MAX_BODY_MB": "5120",
        "PER_USER_QUOTA_GB": "500",
        "AUTH_JWT_ALG": "RS256",
        "AUTH_JWT_ISSUER": None,
        "AUTH_JWT_AUDIENCE": None,
        "JWKS_KID": None,
        "JWT_PUBLIC_KEY_PATH": None,
        "AUTH_JWT_PUBLIC_KEY_BASE64": None
    }
    
    all_good = True
    
    print("\n📋 Required Configuration (with defaults):")
    print("-" * 45)
    
    for var, default in required_with_defaults.items():
        value = os.getenv(var)
        if value:
            if value == default:
                print_status(f"{var}: Using default value", "warning")
            else:
                print_status(f"{var}: Custom value set", "success")
        else:
            print_status(f"{var}: Will use default ({default[:30]}...)", "info")
    
    print("\n🔧 Optional Configuration:")
    print("-" * 25)
    
    for var, default in optional_vars.items():
        value = os.getenv(var)
        if value:
            print_status(f"{var}: {value}", "success")
        else:
            if default:
                print_status(f"{var}: Will use default ({default})", "info")
            else:
                print_status(f"{var}: Not set (optional)", "info")
    
    # Check directory permissions
    print("\n📁 Directory Validation:")
    print("-" * 22)
    
    upload_root = os.getenv("UPLOAD_ROOT", "/app")
    log_dir = os.getenv("LOG_DIR", "/app/services/upload/logs")
    
    # Check if we can create directories
    try:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        print_status(f"Log directory: {log_dir}", "success")
    except Exception as e:
        print_status(f"Log directory error: {e}", "error")
        all_good = False
    
    try:
        storage_dir = Path(upload_root) / "storage"
        storage_dir.mkdir(parents=True, exist_ok=True)
        print_status(f"Storage directory: {storage_dir}", "success")
    except Exception as e:
        print_status(f"Storage directory error: {e}", "error")
        all_good = False
    
    # JWT Configuration validation
    print("\n🔐 JWT Configuration:")
    print("-" * 20)
    
    jwt_key_path = os.getenv("JWT_PUBLIC_KEY_PATH")
    jwt_key_b64 = os.getenv("AUTH_JWT_PUBLIC_KEY_BASE64")
    
    if jwt_key_path and Path(jwt_key_path).exists():
        print_status("JWT public key file found", "success")
    elif jwt_key_b64:
        print_status("JWT public key (base64) configured", "success")
    else:
        print_status("No JWT public key configured - only service token auth available", "warning")
    
    print("\n" + "=" * 55)
    
    if all_good:
        print_status("Configuration validation successful! 🎉", "success")
        print_status("File server should start without issues", "success")
        
        print("\n🚀 Quick Start:")
        print("  • Service Token:", os.getenv("AUTH_SERVICE_TOKEN", "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340"))
        print("  • Upload Root:", os.getenv("UPLOAD_ROOT", "/app"))
        print("  • Log Directory:", os.getenv("LOG_DIR", "/app/services/upload/logs"))
    else:
        print_status("Configuration issues detected!", "error")
        print_status("Please fix the issues above before starting the server", "error")
        return False
    
    return True

def show_environment_examples():
    """Show example environment configurations."""
    print("\n📝 Environment Configuration Examples:")
    print("=" * 40)
    
    print("\n🐳 Docker (.env.docker):")
    print("""AUTH_SERVICE_TOKEN=ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340
UPLOAD_SIGNING_KEY=your-secure-signing-key
UPLOAD_ROOT=/app
LOG_DIR=/app/services/upload/logs
PORT=8000
PYTHONPATH=/app/services/upload""")
    
    print("\n🖥️  Production Server:")
    print("""export AUTH_SERVICE_TOKEN="your-production-service-token"
export UPLOAD_SIGNING_KEY="your-production-signing-key"
export UPLOAD_ROOT="/opt/streamline-file-server/storage"
export LOG_DIR="/opt/streamline-file-server/logs"
export JWT_PUBLIC_KEY_PATH="/path/to/jwt-public-key.pem" """)

def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--examples":
        show_environment_examples()
        return
    
    success = validate_environment()
    
    if not success:
        print("\n💡 For configuration examples, run:")
        print("   python3 validate_config.py --examples")
        sys.exit(1)

if __name__ == "__main__":
    main()
