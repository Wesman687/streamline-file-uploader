#!/bin/bash
# Quick development workflow for updating the server

set -e

echo "🔧 Stream-Line Upload Server - Quick Update Workflow"
echo ""

# Check if we're in the right directory
if [ ! -f "deploy.sh" ]; then
    echo "❌ Please run this from the /home/ubuntu/file-uploader directory"
    exit 1
fi

# Show current status
echo "📊 Current service status:"
sudo systemctl status upload-server --no-pager | head -5

echo ""
echo "🔍 Available commands:"
echo "  1. deploy    - Pull from GitHub and restart service"
echo "  2. restart   - Just restart the service"
echo "  3. logs      - Show recent logs"
echo "  4. status    - Show detailed service status"
echo "  5. test      - Run health checks"
echo ""

read -p "Enter command (1-5): " choice

case $choice in
    1|deploy)
        echo "🚀 Running deployment..."
        ./deploy.sh
        ;;
    2|restart)
        echo "🔄 Restarting service..."
        sudo systemctl restart upload-server
        sleep 2
        echo "✅ Service restarted"
        sudo systemctl status upload-server --no-pager | head -5
        ;;
    3|logs)
        echo "📋 Recent logs:"
        sudo journalctl -u upload-server -n 20 --no-pager
        ;;
    4|status)
        echo "📊 Detailed service status:"
        sudo systemctl status upload-server --no-pager
        ;;
    5|test)
        echo "🩺 Running health checks..."
        echo "Health endpoint:"
        curl -s https://file-server.stream-lineai.com/healthz | python3 -m json.tool
        echo ""
        echo "JWKS endpoint:"
        curl -s https://file-server.stream-lineai.com/.well-known/jwks.json | python3 -c "import sys, json; data = json.load(sys.stdin); print(f'✅ JWKS active - KID: {data[\"keys\"][0][\"kid\"]}')"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac
