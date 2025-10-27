#!/usr/bin/env python3
"""
Simple HTTP server for ComfyUI Gallery that serves files and provides API endpoints.
"""

import os
import json
import mimetypes
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import base64
from PIL import Image
import tempfile
import subprocess

class GalleryHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, output_dir="../../ComfyUI/output", **kwargs):
        self.output_dir = Path(output_dir).resolve()
        super().__init__(*args, **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/files':
            self.handle_api_files()
        elif parsed_path.path.startswith('/api/file/'):
            self.handle_api_file(parsed_path.path[10:])  # Remove '/api/file/'
        elif parsed_path.path.startswith('/api/thumbnail/'):
            self.handle_api_thumbnail(parsed_path.path[15:])  # Remove '/api/thumbnail/'
        else:
            # Serve static files from web directory
            super().do_GET()
    
    def handle_api_files(self):
        """Return list of all media files in the output directory"""
        try:
            files = []
            supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.webm', '.mov', '.avi'}
            
            for root, dirs, filenames in os.walk(self.output_dir):
                for filename in filenames:
                    if any(filename.lower().endswith(ext) for ext in supported_extensions):
                        file_path = Path(root) / filename
                        rel_path = file_path.relative_to(self.output_dir)
                        
                        stat = file_path.stat()
                        file_info = {
                            'name': filename,
                            'path': str(rel_path).replace('\\', '/'),
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'type': 'video' if filename.lower().endswith(('.mp4', '.webm', '.mov', '.avi')) else 'image'
                        }
                        files.append(file_info)
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(files).encode())
            
        except Exception as e:
            self.send_error(500, f"Error listing files: {str(e)}")
    
    def handle_api_file(self, file_path):
        """Serve a file from the output directory"""
        try:
            full_path = self.output_dir / file_path
            if not full_path.exists() or not full_path.is_file():
                self.send_error(404, "File not found")
                return
            
            # Security check - ensure file is within output directory
            if not str(full_path.resolve()).startswith(str(self.output_dir)):
                self.send_error(403, "Access denied")
                return
            
            self.send_response(200)
            mime_type, _ = mimetypes.guess_type(str(full_path))
            if mime_type:
                self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(full_path.stat().st_size))
            self.end_headers()
            
            with open(full_path, 'rb') as f:
                self.wfile.write(f.read())
                
        except Exception as e:
            self.send_error(500, f"Error serving file: {str(e)}")
    
    def handle_api_thumbnail(self, file_path):
        """Generate and serve a thumbnail for an image or video"""
        try:
            full_path = self.output_dir / file_path
            if not full_path.exists() or not full_path.is_file():
                self.send_error(404, "File not found")
                return
            
            # Security check
            if not str(full_path.resolve()).startswith(str(self.output_dir)):
                self.send_error(403, "Access denied")
                return
            
            thumbnail_data = self.generate_thumbnail(full_path)
            if thumbnail_data:
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', str(len(thumbnail_data)))
                self.end_headers()
                self.wfile.write(thumbnail_data)
            else:
                self.send_error(500, "Could not generate thumbnail")
                
        except Exception as e:
            self.send_error(500, f"Error generating thumbnail: {str(e)}")
    
    def generate_thumbnail(self, file_path, size=(300, 300)):
        """Generate a thumbnail for an image or video file"""
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                # Image thumbnail
                with Image.open(file_path) as img:
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                    with tempfile.BytesIO() as output:
                        img.save(output, format='JPEG', quality=85)
                        return output.getvalue()
            
            elif file_path.suffix.lower() in ['.mp4', '.webm', '.mov', '.avi']:
                # Video thumbnail using ffmpeg (if available)
                try:
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                        cmd = [
                            'ffmpeg', '-i', str(file_path), '-vf', 'thumbnail', 
                            '-frames:v', '1', '-f', 'image2', '-y', temp_file.name
                        ]
                        subprocess.run(cmd, capture_output=True, check=True)
                        
                        with Image.open(temp_file.name) as img:
                            img.thumbnail(size, Image.Resampling.LANCZOS)
                            with tempfile.BytesIO() as output:
                                img.save(output, format='JPEG', quality=85)
                                os.unlink(temp_file.name)
                                return output.getvalue()
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Fallback to a placeholder or return None
                    pass
            
            return None
            
        except Exception:
            return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ComfyUI Gallery Server')
    parser.add_argument('--port', type=int, default=8000, help='Port to serve on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--output-dir', default='../../ComfyUI/output', 
                       help='Path to ComfyUI output directory')
    
    args = parser.parse_args()
    
    # Change to web directory to serve static files
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    def handler(*args, **kwargs):
        return GalleryHandler(*args, output_dir=args.output_dir, **kwargs)
    
    httpd = HTTPServer((args.host, args.port), handler)
    print(f"Gallery server running at http://{args.host}:{args.port}")
    print(f"Serving files from: {Path(args.output_dir).resolve()}")
    print("Access the gallery at: http://localhost:8000/gallery.html")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == '__main__':
    main()