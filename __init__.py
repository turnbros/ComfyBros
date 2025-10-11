from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# Initialize web extension for settings interface
try:
    from . import web_extension
except Exception as e:
    print(f"ComfyBros: Warning - Could not initialize web extension: {e}")

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

# Web directory for ComfyUI to serve static files
WEB_DIRECTORY = "./web"