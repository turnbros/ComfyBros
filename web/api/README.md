# Media Gallery FastAPI Backend

A FastAPI-based backend for the Media Gallery application.

## Features

- 📁 **File Management**: List, serve, and delete media files
- 🖼️ **Media Support**: Images (jpg, png, gif, webp, etc.) and Videos (mp4, avi, mov, etc.)
- 🚀 **Job Queue**: Mock job management for image generation
- 📤 **File Upload**: Upload new media files
- 🔄 **CORS Support**: Ready for frontend integration
- 📚 **Auto Documentation**: OpenAPI/Swagger docs included

## Quick Start

1. **Install Dependencies**
   ```bash
   cd api
   pip install -r requirements.txt
   ```

2. **Start the Server**
   ```bash
   python start.py
   ```

3. **Access the API**
   - API Server: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Interactive API: http://localhost:8000/redoc

## API Endpoints

### Media Files
- `GET /api/files` - List all media files
- `GET /api/file/{path}` - Serve a specific media file
- `GET /api/thumbnail/{path}` - Get thumbnail (currently same as file)
- `DELETE /api/delete/{path}` - Delete a media file
- `POST /api/upload` - Upload a new media file

### Generation & Jobs
- `POST /api/generate` - Start image generation (creates job)
- `GET /api/jobs` - Get all jobs
- `POST /api/jobs/{id}/cancel` - Cancel a specific job

## Directory Structure

```
api/
├── main.py           # FastAPI application
├── start.py          # Server startup script  
├── requirements.txt  # Python dependencies
├── media/           # Media files directory
├── jobs.json        # Job queue storage (auto-created)
└── README.md        # This file
```

## Configuration

- **Media Directory**: `api/media/` (configurable in main.py)
- **Server Port**: 8000 (configurable in start.py)
- **CORS Origins**: localhost:3000, localhost:3001

## Development

The server runs with auto-reload enabled, so code changes will automatically restart the server.

To add your own media files, simply copy them to the `api/media/` directory and they will appear in the gallery.

## Integration with ComfyUI

To integrate with ComfyUI:

1. Update the `/api/generate` endpoint to call ComfyUI's API
2. Modify the media directory path to point to ComfyUI's output folder
3. Add webhook support for job status updates
4. Implement thumbnail generation for better performance

## Security Notes

- File access is restricted to the media directory
- Path traversal attacks are prevented
- Only image and video files are served
- File uploads are validated by content type