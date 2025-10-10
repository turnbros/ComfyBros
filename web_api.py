"""
ComfyBros Web API Endpoints
Provides HTTP endpoints for the web settings interface.
"""

import json
from typing import Dict, Any, Tuple
from aiohttp import web
from .settings import settings_manager
from .runpod_client import RunPodClient, RunPodError
from .logger import get_logger

logger = get_logger("WebAPI")


class ComfyBrosWebAPI:
    """Web API handler for ComfyBros settings"""
    
    def __init__(self):
        self.routes = [
            ("GET", "/api/comfybros/settings", self.get_settings),
            ("POST", "/api/comfybros/settings", self.save_settings),
            ("POST", "/api/comfybros/test_connection", self.test_connection),
            ("POST", "/api/comfybros/validate_instance", self.validate_instance),
        ]
    
    async def get_settings(self, request) -> web.Response:
        """Get current ComfyBros settings"""
        try:
            settings = settings_manager.load_settings()
            
            # Convert settings to dict for JSON serialization
            settings_dict = {
                "runpod": {
                    "api_key": settings.runpod.api_key,
                    "enabled": settings.runpod.enabled,
                    "default_instance": settings.runpod.default_instance,
                    "instances": [
                        {
                            "name": inst.name,
                            "endpoint_id": inst.endpoint_id,
                            "description": inst.description,
                            "enabled": inst.enabled,
                            "max_workers": inst.max_workers,
                            "timeout_seconds": inst.timeout_seconds
                        }
                        for inst in settings.runpod.instances
                    ]
                }
            }
            
            logger.info("Settings retrieved successfully")
            return web.json_response(settings_dict)
            
        except Exception as e:
            logger.error(f"Error getting settings: {str(e)}")
            return web.json_response(
                {"error": f"Failed to get settings: {str(e)}"}, 
                status=500
            )
    
    async def save_settings(self, request) -> web.Response:
        """Save ComfyBros settings"""
        try:
            data = await request.json()
            
            # Validate required fields
            if "runpod" not in data:
                return web.json_response(
                    {"error": "Missing runpod configuration"}, 
                    status=400
                )
            
            runpod_data = data["runpod"]
            
            # Load current settings
            settings = settings_manager.load_settings()
            
            # Update RunPod settings
            settings.runpod.api_key = runpod_data.get("api_key", "")
            settings.runpod.enabled = runpod_data.get("enabled", False)
            settings.runpod.default_instance = runpod_data.get("default_instance", "")
            
            # Update instances
            settings.runpod.instances = []
            for inst_data in runpod_data.get("instances", []):
                from .settings import RunPodServerlessInstance
                instance = RunPodServerlessInstance(
                    name=inst_data.get("name", ""),
                    endpoint_id=inst_data.get("endpoint_id", ""),
                    description=inst_data.get("description", ""),
                    enabled=inst_data.get("enabled", True),
                    max_workers=inst_data.get("max_workers", 1),
                    timeout_seconds=inst_data.get("timeout_seconds", 300)
                )
                settings.runpod.instances.append(instance)
            
            # Save settings
            if settings_manager.save_settings(settings):
                logger.info("Settings saved successfully")
                return web.json_response({"success": True, "message": "Settings saved successfully"})
            else:
                logger.error("Failed to save settings")
                return web.json_response(
                    {"error": "Failed to save settings"}, 
                    status=500
                )
                
        except json.JSONDecodeError:
            return web.json_response(
                {"error": "Invalid JSON data"}, 
                status=400
            )
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            return web.json_response(
                {"error": f"Failed to save settings: {str(e)}"}, 
                status=500
            )
    
    async def test_connection(self, request) -> web.Response:
        """Test RunPod API connection"""
        try:
            data = await request.json()
            api_key = data.get("api_key", "")
            
            if not api_key:
                return web.json_response(
                    {"success": False, "message": "API key is required"}, 
                    status=400
                )
            
            # Test connection with provided API key
            client = RunPodClient(api_key)
            success, message = client.validate_connection()
            
            logger.info(f"Connection test: {'success' if success else 'failed'} - {message}")
            
            return web.json_response({
                "success": success,
                "message": message
            })
            
        except json.JSONDecodeError:
            return web.json_response(
                {"success": False, "message": "Invalid JSON data"}, 
                status=400
            )
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return web.json_response({
                "success": False,
                "message": f"Connection test failed: {str(e)}"
            })
    
    async def validate_instance(self, request) -> web.Response:
        """Validate a specific RunPod instance"""
        try:
            data = await request.json()
            instance_name = data.get("instance_name", "")
            
            if not instance_name:
                return web.json_response(
                    {"success": False, "message": "Instance name is required"}, 
                    status=400
                )
            
            # Get instance from settings
            instance = settings_manager.get_runpod_instance(instance_name)
            if not instance:
                return web.json_response({
                    "success": False,
                    "message": f"Instance '{instance_name}' not found"
                })
            
            # Validate instance
            from .runpod_client import runpod_manager
            success, message = runpod_manager.validate_instance(instance_name)
            
            logger.info(f"Instance validation for '{instance_name}': {'success' if success else 'failed'} - {message}")
            
            return web.json_response({
                "success": success,
                "message": message
            })
            
        except json.JSONDecodeError:
            return web.json_response(
                {"success": False, "message": "Invalid JSON data"}, 
                status=400
            )
        except Exception as e:
            logger.error(f"Error validating instance: {str(e)}")
            return web.json_response({
                "success": False,
                "message": f"Instance validation failed: {str(e)}"
            })


def register_api_routes(app):
    """Register ComfyBros API routes with the provided aiohttp app"""
    api = ComfyBrosWebAPI()
    
    for method, path, handler in api.routes:
        app.router.add_route(method, path, handler)
        logger.info(f"Registered API route: {method} {path}")
    
    logger.info("ComfyBros Web API routes registered successfully")