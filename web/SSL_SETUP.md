# SSL Setup Guide

This guide covers multiple approaches to run the Media Gallery with SSL/HTTPS.

## Option 1: Self-Signed Certificates (Development)

### Generate Self-Signed Certificates

```bash
# Create a directory for certificates
mkdir -p certs

# Generate self-signed certificate (valid for 365 days)
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout certs/key.pem \
  -out certs/cert.pem \
  -days 365 \
  -subj "/CN=localhost"
```

### Update API Server (start.py)

Edit `api/start.py`:

```python
#!/usr/bin/env python3
"""
FastAPI Media Gallery Server Startup Script
"""
import uvicorn
import sys
from pathlib import Path

if __name__ == "__main__":
    # Change to API directory
    api_dir = Path(__file__).parent
    sys.path.insert(0, str(api_dir))

    print("🚀 Starting FastAPI Media Gallery Server with SSL...")
    print("📁 Media directory: api/media/")
    print("🌐 API docs will be available at: https://localhost:8443/docs")
    print("🖼️ Frontend should be at: https://localhost:3001")
    print()

    # SSL configuration
    cert_dir = api_dir.parent / "certs"

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8443,  # Changed to 8443 for HTTPS
        reload=True,
        reload_dirs=[str(api_dir)],
        ssl_keyfile=str(cert_dir / "key.pem"),
        ssl_certfile=str(cert_dir / "cert.pem")
    )
```

### Update Frontend (vite.config.js)

Edit `vite.config.js`:

```javascript
import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import fs from 'fs'
import path from 'path'

export default defineConfig({
  plugins: [svelte()],
  server: {
    port: 3001,
    https: {
      key: fs.readFileSync(path.resolve(__dirname, 'certs/key.pem')),
      cert: fs.readFileSync(path.resolve(__dirname, 'certs/cert.pem'))
    },
    proxy: {
      '/api': {
        target: 'https://localhost:8443',
        changeOrigin: true,
        secure: false  // Allow self-signed certificates
      }
    }
  }
})
```

### Trust the Certificate (macOS)

```bash
# Add certificate to keychain and trust it
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain certs/cert.pem
```

### Update start-dev.sh

Edit `start-dev.sh` to update URLs:

```bash
echo "🖼️  Frontend: https://localhost:3001"
echo "🔗  API:      https://localhost:8443"
echo "📚  API Docs: https://localhost:8443/docs"
```

---

## Option 2: Reverse Proxy with Caddy (Recommended for Production)

### Install Caddy

```bash
# macOS
brew install caddy

# Linux
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

### Create Caddyfile

Create `Caddyfile` in the web directory:

```caddy
# Local development with automatic HTTPS
localhost:443 {
    # Frontend
    reverse_proxy localhost:3001

    # API
    handle /api/* {
        reverse_proxy localhost:8000
    }

    # Enable logging
    log {
        output file ./caddy-access.log
    }
}
```

For production with a domain:

```caddy
yourdomain.com {
    # Automatic HTTPS with Let's Encrypt

    # Frontend
    reverse_proxy localhost:3001

    # API
    handle /api/* {
        reverse_proxy localhost:8000
    }

    # Enable logging
    log {
        output file ./caddy-access.log
    }
}
```

### Run with Caddy

```bash
# Start backend (without SSL)
uv run ./api/start.py &

# Start frontend (without SSL)
npm run dev &

# Start Caddy
caddy run
```

Access at: `https://localhost` or `https://yourdomain.com`

---

## Option 3: Nginx Reverse Proxy

### Install Nginx

```bash
# macOS
brew install nginx

# Linux
sudo apt install nginx
```

### Generate SSL Certificates (if not using Let's Encrypt)

```bash
mkdir -p /usr/local/etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /usr/local/etc/nginx/ssl/nginx.key \
  -out /usr/local/etc/nginx/ssl/nginx.crt \
  -subj "/CN=localhost"
```

### Nginx Configuration

Create `/usr/local/etc/nginx/servers/media-gallery.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name localhost;

    ssl_certificate /usr/local/etc/nginx/ssl/nginx.crt;
    ssl_certificate_key /usr/local/etc/nginx/ssl/nginx.key;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Frontend
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Important for video streaming
        proxy_buffering off;
        proxy_request_buffering off;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name localhost;
    return 301 https://$server_name$request_uri;
}
```

### Start Services

```bash
# Start backend and frontend normally
./start-dev.sh

# Start nginx
sudo nginx
# or reload if already running
sudo nginx -s reload
```

Access at: `https://localhost`

---

## Option 4: Let's Encrypt (Production Only)

### Using Certbot with Nginx

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate and auto-configure nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is set up automatically
# Test renewal
sudo certbot renew --dry-run
```

### Using Caddy (Automatic)

Caddy automatically obtains and renews Let's Encrypt certificates:

```caddy
yourdomain.com {
    reverse_proxy localhost:3001

    handle /api/* {
        reverse_proxy localhost:8000
    }
}
```

That's it! Caddy handles everything automatically.

---

## Recommendations

- **Development**: Use **Option 1** (self-signed certificates) or **Option 2** (Caddy)
- **Production**: Use **Option 2** (Caddy) or **Option 4** (Let's Encrypt with Nginx)
- **Simplest**: Caddy is the easiest option - it handles SSL automatically

## Testing

After setting up SSL:

1. Visit `https://localhost` (or your domain)
2. You may need to accept the self-signed certificate warning in development
3. Check browser console for mixed content warnings
4. Test video playback to ensure byte-range requests work over HTTPS

## Troubleshooting

### Browser Shows "Not Secure"
- For self-signed certs, this is normal. Click "Advanced" → "Proceed"
- For production, ensure your domain DNS is pointing to your server

### Videos Don't Load
- Check that proxy isn't buffering responses
- Ensure `proxy_buffering off` in nginx or equivalent in other proxies
- Verify Content-Range headers are being passed through

### CORS Errors
- Update CORS settings in `api/main.py` to include HTTPS origins
- Add your HTTPS domain to `allow_origins` list
