"""
ComfyBros Web Extension Initialization
This file is automatically loaded by ComfyUI to initialize web extensions.
"""

import os
from .web_api import register_api_routes
from .logger import get_logger

logger = get_logger("WebInit")

def init(server):
    """Initialize ComfyBros web extension with ComfyUI server"""
    try:
        # Register API routes with the server
        register_api_routes(server.app)
        logger.info("ComfyBros web API initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize ComfyBros web extension: {e}")
        # Don't raise exception to avoid breaking ComfyUI startup
        return False
    
    return True