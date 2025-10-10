from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# Web directory for ComfyUI to serve static files
WEB_DIRECTORY = "./web"

# Initialize web extension for settings interface
try:
    from .web_api import register_api_routes
    from .logger import get_logger
    
    logger = get_logger("ComfyBros")
    
    # Register API routes when the extension is loaded
    try:
        from server import PromptServer
        app = PromptServer.instance.app
        register_api_routes(app)
        logger.info("ComfyBros API routes registered successfully")
    except Exception as e:
        logger.error(f"Failed to register ComfyBros API routes: {e}")
        
except Exception as e:
    print(f"ComfyBros: Warning - Could not initialize web extension: {e}")

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']