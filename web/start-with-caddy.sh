#!/bin/bash

echo "🚀 Starting Media Gallery with Caddy (Automatic HTTPS)"
echo ""

# Check if Caddy is installed
if ! command -v caddy &> /dev/null; then
    echo "❌ Caddy is not installed!"
    echo ""
    echo "🔧 Install Caddy:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "   brew install caddy"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "   See: https://caddyserver.com/docs/install"
    fi
    echo ""
    exit 1
fi

echo "🐍 Starting FastAPI backend on port 8000..."
uv run ./api/start.py &
BACKEND_PID=$!

echo "📦 Installing Node.js dependencies..."
npm install
echo ""

echo "🌐 Starting Svelte frontend on port 3001..."
npm run dev &
FRONTEND_PID=$!

# Wait for services to start
sleep 2

echo ""
echo "🔒 Starting Caddy with automatic HTTPS..."
caddy run &
CADDY_PID=$!

echo ""
echo "✅ All services started!"
echo ""
echo "🔒 Access the app at: https://localhost"
echo "📚 API Docs: https://localhost/api/docs (Note: via Caddy proxy)"
echo ""
echo "📁 Add media files to api/media/ directory to see them in the gallery"
echo ""
echo "Press Ctrl+C to stop all servers..."

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    kill $CADDY_PID 2>/dev/null
    echo "✅ All servers stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for any process to exit
wait
