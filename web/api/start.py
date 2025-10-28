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
    
    print("🚀 Starting FastAPI Media Gallery Server...")
    print("📁 Media directory: api/media/")
    print("🌐 API docs will be available at: http://localhost:8000/docs")
    print("🖼️ Frontend should be at: http://localhost:3001")
    print()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(api_dir)]
    )