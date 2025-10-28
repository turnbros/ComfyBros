#!/usr/bin/env python3
"""
Simple HTTP server for ComfyUI Gallery that serves files and provides API endpoints.
"""

import os
import json
import mimetypes
import hashlib
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
        self.thumbnail_dir = self.output_dir / "thumbnails"
        self.thumbnail_dir.mkdir(exist_ok=True)
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
                root_path = Path(root)
                
                # Remove hidden directories and thumbnails directory from traversal
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'thumbnails']
                
                # Skip the thumbnails directory and any subdirectories
                if self.thumbnail_dir in root_path.parents or root_path == self.thumbnail_dir:
                    continue
                
                for filename in filenames:
                    if any(filename.lower().endswith(ext) for ext in supported_extensions):
                        file_path = Path(root) / filename
                        
                        # Additional check to ensure file is not in thumbnails directory
                        if self.thumbnail_dir in file_path.parents:
                            continue
                            
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
    
    def get_thumbnail_path(self, file_path):
        """Get the path for a cached thumbnail"""
        # Create a hash of the original file path for the thumbnail filename
        file_hash = hashlib.md5(str(file_path).encode()).hexdigest()
        return self.thumbnail_dir / f"{file_hash}.jpg"
    
    def is_thumbnail_valid(self, file_path, thumbnail_path):
        """Check if cached thumbnail is newer than the original file"""
        if not thumbnail_path.exists():
            return False
        
        try:
            file_mtime = file_path.stat().st_mtime
            thumbnail_mtime = thumbnail_path.stat().st_mtime
            return thumbnail_mtime >= file_mtime
        except:
            return False
    
    def generate_thumbnail(self, file_path, size=(300, 300)):
        """Generate or retrieve cached thumbnail for an image or video file"""
        try:
            file_path = Path(file_path)
            thumbnail_path = self.get_thumbnail_path(file_path)
            
            print(f"Generating thumbnail for: {file_path}")
            print(f"Thumbnail path: {thumbnail_path}")
            
            # Check if we have a valid cached thumbnail
            if self.is_thumbnail_valid(file_path, thumbnail_path):
                print(f"Using cached thumbnail: {thumbnail_path}")
                with open(thumbnail_path, 'rb') as f:
                    return f.read()
            
            # Generate new thumbnail
            thumbnail_data = None
            
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                print(f"Processing image: {file_path}")
                # Image thumbnail
                try:
                    with Image.open(file_path) as img:
                        print(f"Opened image: {img.size}, mode: {img.mode}")
                        img.thumbnail(size, Image.Resampling.LANCZOS)
                        print(f"Resized to: {img.size}")
                        
                        # Convert to RGB if necessary
                        if img.mode in ('RGBA', 'P'):
                            img = img.convert('RGB')
                        
                        with tempfile.BytesIO() as output:
                            img.save(output, format='JPEG', quality=85)
                            thumbnail_data = output.getvalue()
                            print(f"Generated thumbnail data: {len(thumbnail_data)} bytes")
                except Exception as e:
                    print(f"Error processing image {file_path}: {e}")
                    return None
            
            elif file_path.suffix.lower() in ['.mp4', '.webm', '.mov', '.avi']:
                print(f"Processing video: {file_path}")
                # Video thumbnail using ffmpeg (if available)
                try:
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                        cmd = [
                            'ffmpeg', '-i', str(file_path), '-vf', 'thumbnail', 
                            '-frames:v', '1', '-f', 'image2', '-y', temp_file.name
                        ]
                        result = subprocess.run(cmd, capture_output=True, check=True)
                        print(f"ffmpeg completed successfully")
                        
                        with Image.open(temp_file.name) as img:
                            img.thumbnail(size, Image.Resampling.LANCZOS)
                            with tempfile.BytesIO() as output:
                                img.save(output, format='JPEG', quality=85)
                                thumbnail_data = output.getvalue()
                                os.unlink(temp_file.name)
                                print(f"Generated video thumbnail: {len(thumbnail_data)} bytes")
                except subprocess.CalledProcessError as e:
                    print(f"ffmpeg error for {file_path}: {e.stderr.decode()}")
                except FileNotFoundError:
                    print(f"ffmpeg not found for {file_path}")
                except Exception as e:
                    print(f"Error processing video {file_path}: {e}")
            
            # Cache the thumbnail if we generated one
            if thumbnail_data:
                try:
                    with open(thumbnail_path, 'wb') as f:
                        f.write(thumbnail_data)
                    print(f"Cached thumbnail: {thumbnail_path}")
                except Exception as e:
                    print(f"Warning: Could not cache thumbnail: {e}")
            else:
                print(f"No thumbnail data generated for: {file_path}")
            
            return thumbnail_data
            
        except Exception as e:
            print(f"Exception in generate_thumbnail for {file_path}: {e}")
            import traceback
            traceback.print_exc()
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
    
    def handler(*handler_args, **handler_kwargs):
        return GalleryHandler(*handler_args, output_dir=args.output_dir, **handler_kwargs)
    
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