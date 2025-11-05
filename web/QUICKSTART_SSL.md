# Quick Start: Running with SSL/HTTPS

## 🚀 Easiest Method: Using Caddy (Recommended)

Caddy automatically handles SSL certificates for you!

### 1. Install Caddy

```bash
# macOS
brew install caddy

# Linux (Debian/Ubuntu)
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

### 2. Run the Application

```bash
./start-with-caddy.sh
```

### 3. Access the App

Open your browser to: **https://localhost**

That's it! Caddy handles everything automatically.

---

## 🔧 Alternative: Self-Signed Certificates

If you want SSL directly in the application without a reverse proxy:

### 1. Run with SSL

```bash
./start-dev-ssl.sh
```

This script will:
- Auto-generate SSL certificates if they don't exist
- Attempt to trust them on macOS (no browser warnings!)
- Start both backend and frontend with HTTPS

### 2. Access the App

- Frontend: **https://localhost:3001**
- API: **https://localhost:8443**
- API Docs: **https://localhost:8443/docs**

### Note on Browser Warnings

If you see a "Not Secure" warning:
1. Click **Advanced**
2. Click **Proceed to localhost (unsafe)**

This is normal for self-signed certificates in development.

---

## 📖 Detailed Documentation

For more options (Nginx, Let's Encrypt, production setup), see [SSL_SETUP.md](SSL_SETUP.md)

---

## 🐛 Troubleshooting

### "Caddy: command not found"
Install Caddy using the commands above.

### "Certificate not trusted" on macOS
Run manually:
```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain certs/cert.pem
```

### Videos don't play over HTTPS
Make sure your browser isn't blocking mixed content. All requests should be HTTPS.

### Port already in use
Check if another process is using the port:
```bash
# Check port 443 (Caddy)
lsof -i :443

# Check port 8443 (API)
lsof -i :8443

# Kill the process
kill -9 <PID>
```
