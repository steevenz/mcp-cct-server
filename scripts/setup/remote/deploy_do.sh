#!/bin/bash
# CCT DigitalOcean Deployment Script
# This script automates the setup of Docker, Nginx, and Certbot on Ubuntu.

set -e

echo "=== CCT DIGITALOCEAN DEPLOYMENT START ==="

# 1. Update System
sudo apt-get update
sudo apt-get upgrade -y

# 2. Install Docker
if ! command -v docker &> /dev/null; then
    echo "[*] Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# 3. Install Nginx & Certbot
echo "[*] Installing Nginx and Certbot..."
sudo apt-get install -y nginx certbot python3-certbot-nginx

# 4. Configure Nginx
DOMAIN=$1
if [ -z "$DOMAIN" ]; then
    echo "Usage: ./deploy_do.sh <your-domain.com>"
    exit 1
fi

echo "[*] Configuring Nginx for $DOMAIN..."
cat <<EOF | sudo tee /etc/nginx/sites-available/cct-mcp
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # SSE Support
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 24h;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/cct-mcp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 5. SSL with Let's Encrypt
echo "[*] Obtaining SSL certificate for $DOMAIN..."
echo "NOTE: This will prompt for email and agreement."
# sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email webmaster@$DOMAIN

# 6. Setup Project
echo "[*] Setting up CCT Server..."
if [ ! -f .env ]; then
    cp .env.example .env
    BOOTSTRAP_KEY="cct_bootstrap_$(openssl rand -base64 32)"
    sed -i "s/CCT_BOOTSTRAP_API_KEY=.*/CCT_BOOTSTRAP_API_KEY=$BOOTSTRAP_KEY/" .env
    echo "[!] Generated new CCT_BOOTSTRAP_API_KEY in .env"
    echo "[!] Save this key: $BOOTSTRAP_KEY"
fi

# 7. Start Docker
echo "[*] Starting CCT Server via Docker Compose..."
# docker compose -f docker-compose.prod.yml up -d --build

# 8. Security Hardening (IP Whitelist)
echo "[*] (Optional) Secure your server by whitelisting your IP."
echo "    Add 'CCT_AUTH_ALLOWED_IPS=your.public.ip' to your .env to restrict handshakes."

echo "=== DEPLOYMENT COMPLETE ==="
echo "Handshake Portal: https://$DOMAIN/handshake"
echo "SSE Endpoint: https://$DOMAIN/cct"
