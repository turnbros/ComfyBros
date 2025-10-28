from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import uuid
from PIL import Image, ImageOps
import io

app = FastAPI(title="Media Gallery API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MEDIA_DIR = Path("/opt/ComfyUI/output")  # Directory containing media files
THUMBNAILS_DIR = Path("thumbnails")  # Thumbnail cache directory
JOBS_FILE = Path("jobs.json")  # Job queue storage

# Ensure directories exist
MEDIA_DIR.mkdir(exist_ok=True)
THUMBNAILS_DIR.mkdir(exist_ok=True)

# Pydantic models
class MediaFile(BaseModel):
    name: str
    path: str
    size: int
    modified: str
    type: str  # 'image' or 'video'

class GenerateRequest(BaseModel):
    trigger: str
    timestamp: int
    prompt: Optional[str] = None

class Job(BaseModel):
    id: str
    name: str
    status: str  # 'pending', 'running', 'completed', 'failed', 'cancelled'
    created: str
    progress: Optional[int] = None
    error: Optional[str] = None

# Helper functions
def load_jobs() -> List[Job]:
    """Load jobs from JSON file"""
    if not JOBS_FILE.exists():
        return []
    try:
        with open(JOBS_FILE, 'r') as f:
            data = json.load(f)
            return [Job(**job) for job in data]
    except Exception:
        return []

def save_jobs(jobs: List[Job]):
    """Save jobs to JSON file"""
    with open(JOBS_FILE, 'w') as f:
        json.dump([job.dict() for job in jobs], f, indent=2)

def get_file_type(file_path: Path) -> str:
    """Determine if file is image or video based on extension"""
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type:
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
    return 'unknown'

def generate_thumbnail(image_path: Path, size: tuple = (300, 300)) -> bytes:
    """Generate a thumbnail for an image and return as bytes"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img
            
            # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=85, optimize=True)
            return img_byte_arr.getvalue()
    except Exception as e:
        print(f"Error generating thumbnail for {image_path}: {e}")
        return None

def scan_media_files() -> List[MediaFile]:
    """Scan media directory and return list of media files"""
    media_files = []
    
    # Supported file extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
    supported_extensions = image_extensions | video_extensions
    
    for file_path in MEDIA_DIR.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            try:
                stat = file_path.stat()
                file_type = get_file_type(file_path)
                
                if file_type in ['image', 'video']:
                    relative_path = file_path.relative_to(MEDIA_DIR)
                    media_files.append(MediaFile(
                        name=file_path.name,
                        path=str(relative_path),
                        size=stat.st_size,
                        modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        type=file_type
                    ))
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
    
    return sorted(media_files, key=lambda x: x.modified, reverse=True)

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Media Gallery API", "version": "1.0.0"}

@app.get("/api/files", response_model=List[MediaFile])
async def get_files():
    """Get list of all media files"""
    return scan_media_files()

@app.get("/api/file/{file_path:path}")
async def get_file(file_path: str):
    """Serve a media file"""
    full_path = MEDIA_DIR / file_path
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    # Security check - ensure file is within media directory
    try:
        full_path.resolve().relative_to(MEDIA_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(full_path)

@app.get("/api/thumbnail/{file_path:path}")
async def get_thumbnail(file_path: str):
    """Get thumbnail for a media file"""
    try:
        # Validate path to prevent traversal attacks
        full_path = MEDIA_DIR / file_path
        full_path.resolve().relative_to(MEDIA_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if it's an image
    if get_file_type(full_path) != 'image':
        # For videos, just serve the original file for now
        return FileResponse(full_path)
    
    # Generate cache filename
    cache_name = f"{file_path.replace('/', '_').replace('\\', '_')}_thumb.jpg"
    cache_path = THUMBNAILS_DIR / cache_name
    
    # Check if thumbnail exists and is newer than original
    if cache_path.exists() and cache_path.stat().st_mtime > full_path.stat().st_mtime:
        return FileResponse(cache_path, media_type="image/jpeg")
    
    # Generate new thumbnail
    thumbnail_data = generate_thumbnail(full_path)
    if thumbnail_data is None:
        # Fall back to original file if thumbnail generation fails
        return FileResponse(full_path)
    
    # Save to cache
    try:
        with open(cache_path, 'wb') as f:
            f.write(thumbnail_data)
    except Exception as e:
        print(f"Failed to cache thumbnail: {e}")
    
    # Return thumbnail
    return Response(content=thumbnail_data, media_type="image/jpeg")

@app.delete("/api/delete/{file_path:path}")
async def delete_file(file_path: str):
    """Delete a media file"""
    full_path = MEDIA_DIR / file_path
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security check - ensure file is within media directory
    try:
        full_path.resolve().relative_to(MEDIA_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        full_path.unlink()
        return {"message": f"File {file_path} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@app.post("/api/generate")
async def generate_image(request: GenerateRequest):
    """Start image generation (mock implementation)"""
    jobs = load_jobs()
    
    # Create new job
    job = Job(
        id=str(uuid.uuid4()),
        name="Image Generation",
        status="pending",
        created=datetime.now().isoformat(),
        progress=0
    )
    
    jobs.append(job)
    save_jobs(jobs)
    
    return {"message": "Generation started", "job_id": job.id}

@app.get("/api/jobs", response_model=dict)
async def get_jobs():
    """Get all jobs"""
    jobs = load_jobs()
    return {"jobs": [job.dict() for job in jobs]}

@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a job"""
    jobs = load_jobs()
    
    for job in jobs:
        if job.id == job_id:
            if job.status in ['pending', 'running']:
                job.status = 'cancelled'
                save_jobs(jobs)
                return {"message": f"Job {job_id} cancelled"}
            else:
                raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    
    raise HTTPException(status_code=404, detail="Job not found")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a media file"""
    # Validate file type
    if not file.content_type or not (
        file.content_type.startswith('image/') or 
        file.content_type.startswith('video/')
    ):
        raise HTTPException(status_code=400, detail="Only image and video files are allowed")
    
    # Save file
    file_path = MEDIA_DIR / file.filename
    
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {"message": f"File {file.filename} uploaded successfully", "path": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

# Mount static files (optional - for serving web app)
# app.mount("/", StaticFiles(directory="../dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
