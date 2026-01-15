#!/bin/bash
# Scribe Deployment Script
# Run with: sudo bash /srv/projects/illanes00-scribe/deploy/install.sh

set -e

echo "=== Scribe Deployment ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

PROJECT_DIR="/srv/projects/illanes00-scribe"
DEPLOY_DIR="$PROJECT_DIR/deploy"

echo "1. Installing Python dependencies..."
cd "$PROJECT_DIR/backend"
pip3 install -r requirements.txt --quiet

echo "2. Building frontend..."
cd "$PROJECT_DIR/frontend"
npm ci --silent
npm run build

echo "3. Installing systemd services..."
cp "$DEPLOY_DIR/illanes00-scribe-backend.service" /etc/systemd/system/
cp "$DEPLOY_DIR/illanes00-scribe-frontend.service" /etc/systemd/system/
systemctl daemon-reload

echo "4. Enabling and starting services..."
systemctl enable illanes00-scribe-backend illanes00-scribe-frontend
systemctl restart illanes00-scribe-backend illanes00-scribe-frontend

echo "5. Checking service status..."
sleep 3
systemctl status illanes00-scribe-backend --no-pager || true
systemctl status illanes00-scribe-frontend --no-pager || true

echo "6. Updating Caddy configuration..."
if ! grep -q "scribe.illanes00.cl" /etc/caddy/Caddyfile 2>/dev/null; then
    echo ""
    echo "=== MANUAL STEP REQUIRED ==="
    echo "Add to /etc/caddy/Caddyfile:"
    cat "$DEPLOY_DIR/Caddyfile.scribe"
    echo ""
    echo "Then run: sudo systemctl reload caddy"
else
    echo "Caddy configuration already exists"
fi

echo ""
echo "=== Deployment Complete ==="
echo "Backend:  http://localhost:8132/health"
echo "Frontend: http://localhost:8133"
echo "Site:     https://scribe.illanes00.cl"
