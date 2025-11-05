#!/usr/bin/env python3
"""
FastAPI Media Gallery Server Startup Script with SSL
"""
import uvicorn
import sys
from pathlib import Path

if __name__ == "__main__":
    # Change to API directory
    api_dir = Path(__file__).parent
    sys.path.insert(0, str(api_dir))

    # SSL certificate paths
    cert_dir = api_dir.parent / "certs"
    ssl_keyfile = cert_dir / "key.pem"
    ssl_certfile = cert_dir / "cert.pem"

    # Check if certificates exist
    if not ssl_keyfile.exists() or not ssl_certfile.exists():
        print("❌ SSL certificates not found!")
        print(f"   Looking for: {ssl_keyfile} and {ssl_certfile}")
        print()
        print("🔧 Generate certificates with:")
        print(f"   mkdir -p {cert_dir}")
        print(f"   openssl req -x509 -newkey rsa:4096 -nodes \\")
        print(f"     -keyout {ssl_keyfile} \\")
        print(f"     -out {ssl_certfile} \\")
        print(f"     -days 365 -subj '/CN=localhost'")
        print()
        sys.exit(1)

    print("🚀 Starting FastAPI Media Gallery Server with SSL...")
    print("📁 Media directory: api/media/")
    print("🌐 API docs will be available at: https://localhost:8443/docs")
    print("🖼️ Frontend should be at: https://localhost:3001")
    print("🔒 SSL certificates loaded successfully")
    print()
    print("⚠️  Browser will show a security warning for self-signed certificates.")
    print("   Click 'Advanced' → 'Proceed to localhost' to continue.")
    print()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8443,
        reload=True,
        reload_dirs=[str(api_dir)],
        ssl_keyfile=str(ssl_keyfile),
        ssl_certfile=str(ssl_certfile)
    )
