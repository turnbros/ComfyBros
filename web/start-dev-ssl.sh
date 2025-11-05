#!/bin/bash

echo "🚀 Starting Media Gallery Development Environment with SSL"
echo ""

# Check if certificates exist
CERT_DIR="certs"
if [ ! -f "$CERT_DIR/key.pem" ] || [ ! -f "$CERT_DIR/cert.pem" ]; then
    echo "❌ SSL certificates not found!"
    echo ""
    echo "🔧 Generating self-signed certificates..."
    mkdir -p "$CERT_DIR"

    openssl req -x509 -newkey rsa:4096 -nodes \
        -keyout "$CERT_DIR/key.pem" \
        -out "$CERT_DIR/cert.pem" \
        -days 365 \
        -subj "/CN=localhost" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "✅ Certificates generated successfully"
        echo ""

        # Try to trust certificate on macOS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "🔐 Adding certificate to macOS keychain..."
            sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$CERT_DIR/cert.pem" 2>/dev/null
            if [ $? -eq 0 ]; then
                echo "✅ Certificate trusted (no browser warnings)"
            else
                echo "⚠️  Could not auto-trust certificate. You'll see browser warnings."
            fi
            echo ""
        fi
    else
        echo "❌ Failed to generate certificates"
        exit 1
    fi
fi

echo "🐍 Starting FastAPI backend on port 8443 (HTTPS)..."
uv run ./api/start-ssl.py &
BACKEND_PID=$!

echo "📦 Installing Node.js dependencies..."
npm install
echo ""

echo "🌐 Starting Svelte frontend on port 3001 (HTTPS)..."
npm run dev -- --https &
FRONTEND_PID=$!

echo ""
echo "✅ Development environment started with SSL!"
echo ""
echo "🔒 HTTPS URLs:"
echo "🖼️  Frontend: https://localhost:3001"
echo "🔗  API:      https://localhost:8443"
echo "📚  API Docs: https://localhost:8443/docs"
echo ""
echo "⚠️  If using self-signed certificates, your browser will show a warning."
echo "   Click 'Advanced' → 'Proceed to localhost' to continue."
echo ""
echo "📁 Add media files to api/media/ directory to see them in the gallery"
echo ""
echo "Press Ctrl+C to stop both servers..."

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for either process to exit
wait
