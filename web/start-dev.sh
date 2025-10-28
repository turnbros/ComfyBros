#!/bin/bash

echo "🚀 Starting Media Gallery Development Environment"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found. Please install Python 3."
    exit 1
fi

# Check if Node.js is available
if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm is required but not found. Please install Node.js."
    exit 1
fi

echo "📦 Installing Python dependencies..."
cd api
pip3 install -r requirements.txt
echo ""

echo "🐍 Starting FastAPI backend on port 8000..."
python3 start.py &
BACKEND_PID=$!
cd ..

echo "📦 Installing Node.js dependencies..."
npm install
echo ""

echo "🌐 Starting Svelte frontend on port 3001..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Development environment started!"
echo ""
echo "🖼️  Frontend: http://localhost:3001"
echo "🔗  API:      http://localhost:8000"
echo "📚  API Docs: http://localhost:8000/docs"
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