"""
ComfyBros Web Extension Registration
Registers the web interface and API endpoints with ComfyUI server.
"""

import os
import importlib.util
from .web_api import register_api_routes
from .logger import get_logger

logger = get_logger("WebExtension")

WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web")


def init_web_extension():
    """Initialize the ComfyBros web extension"""
    try:
        # Try to import ComfyUI server components
        try:
            import server
            from server import PromptServer
            web_app = PromptServer.instance.app
            
            # Register API routes
            register_api_routes(web_app)
            
            # Serve static web files
            web_app.router.add_static('/comfybros/', WEB_DIRECTORY)
            
            logger.info("ComfyBros web extension initialized successfully")
            return True
            
        except ImportError as e:
            logger.warning(f"Could not import ComfyUI server components: {e}")
            logger.info("Web extension will not be available")
            return False
            
    except Exception as e:
        logger.error(f"Error initializing web extension: {e}")
        return False


# Auto-initialize when module is imported
try:
    init_web_extension()
except Exception as e:
    logger.error(f"Failed to auto-initialize web extension: {e}")