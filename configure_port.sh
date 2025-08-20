#!/bin/bash

# Stream-Line File Server - Port Configuration Helper
# ===================================================
# 
# This script helps you configure a custom port for the file server

echo "🔧 Stream-Line File Server - Port Configuration"
echo "==============================================="
echo ""

# Get current port
CURRENT_PORT=$(grep "PORT=" .env.docker 2>/dev/null | cut -d'=' -f2)
if [ -z "$CURRENT_PORT" ]; then
    CURRENT_PORT="10000"
fi

echo "Current port: $CURRENT_PORT"
echo ""

# Check for port conflicts
echo "🔍 Checking for port conflicts..."

# Common ports to avoid
COMMON_PORTS="3000 3001 4000 5000 5173 8000 8080 8443 9000"
SUGGESTED_PORTS="10000 10001 10002 10003 10004 10005 11000 11001 11002 12000"

echo "❌ Ports to avoid (commonly used):"
for port in $COMMON_PORTS; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "  $port - IN USE"
    else
        echo "  $port - Available (but commonly used)"
    fi
done

echo ""
echo "✅ Recommended ports:"
for port in $SUGGESTED_PORTS; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "  $port - IN USE"
    else
        echo "  $port - Available ✅"
    fi
done

echo ""
echo "🎯 Port Selection Guidelines:"
echo "  • Use ports 10000+ to avoid conflicts"
echo "  • Avoid common development ports (3000, 8000, etc.)"
echo "  • Consider your server environment"
echo "  • Document your choice for team members"

echo ""
read -p "Enter new port (or press Enter to keep $CURRENT_PORT): " NEW_PORT

if [ -z "$NEW_PORT" ]; then
    echo "Keeping current port: $CURRENT_PORT"
    exit 0
fi

# Validate port number
if ! [[ "$NEW_PORT" =~ ^[0-9]+$ ]] || [ "$NEW_PORT" -lt 1024 ] || [ "$NEW_PORT" -gt 65535 ]; then
    echo "❌ Invalid port number. Must be between 1024 and 65535."
    exit 1
fi

# Check if port is in use
if lsof -i :$NEW_PORT > /dev/null 2>&1; then
    echo "⚠️  Warning: Port $NEW_PORT appears to be in use."
    read -p "Continue anyway? (y/N): " CONTINUE
    if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
        echo "Cancelled."
        exit 1
    fi
fi

echo "🔧 Updating configuration files..."

# Update .env.docker
if [ -f .env.docker ]; then
    sed -i "s/PORT=.*/PORT=$NEW_PORT/" .env.docker
    echo "✅ Updated .env.docker"
fi

# Update docker-compose.yml
if [ -f docker-compose.yml ]; then
    sed -i "s/\".*:.*\"/\"$NEW_PORT:$NEW_PORT\"/" docker-compose.yml
    sed -i "s/localhost:.*/localhost:$NEW_PORT\/healthz\"/" docker-compose.yml
    echo "✅ Updated docker-compose.yml"
fi

# Update nginx.conf if it exists
if [ -f nginx.conf ]; then
    sed -i "s/server file-server:.*/server file-server:$NEW_PORT;/" nginx.conf
    echo "✅ Updated nginx.conf"
fi

echo ""
echo "🎉 Port configuration updated to $NEW_PORT!"
echo ""
echo "📋 Next steps:"
echo "  1. Restart your containers: docker-compose restart"
echo "  2. Test new URL: http://localhost:$NEW_PORT/healthz"
echo "  3. Update your application configuration"
echo ""
echo "🔗 New URLs:"
echo "  • File Server: http://localhost:$NEW_PORT"
echo "  • Health Check: http://localhost:$NEW_PORT/healthz"
echo "  • API Docs: http://localhost:$NEW_PORT/docs"
