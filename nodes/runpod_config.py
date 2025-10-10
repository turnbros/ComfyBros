"""
RunPod Configuration Nodes
Provides nodes for configuring RunPod serverless instances and API settings.
"""

from typing import Tuple, Optional, List, Dict, Any
from ..settings import settings_manager, RunPodServerlessInstance


class RunPodConfiguration:
    """Node for configuring RunPod API key and global settings"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {
                    "multiline": False,
                    "default": ""
                }),
                "enabled": ("BOOLEAN", {
                    "default": True
                }),
            },
            "optional": {}
        }
    
    RETURN_TYPES = ("STRING", "BOOLEAN")
    RETURN_NAMES = ("status_message", "success")
    FUNCTION = "configure"
    CATEGORY = "ComfyBros/RunPod"
    
    def configure(self, api_key: str, enabled: bool) -> Tuple[str, bool]:
        """Configure RunPod API settings"""
        try:
            settings = settings_manager.load_settings()
            
            # Update API key
            if api_key.strip():
                settings.runpod.api_key = api_key.strip()
                print(f"RunPodConfiguration: Updated API key")
            else:
                print("RunPodConfiguration: Warning - Empty API key provided")
            
            # Update enabled status
            settings.runpod.enabled = enabled
            
            # Save settings
            if settings_manager.save_settings(settings):
                status_msg = "RunPod configuration updated successfully"
                print(f"RunPodConfiguration: {status_msg}")
                return (status_msg, True)
            else:
                status_msg = "Failed to save RunPod configuration"
                print(f"RunPodConfiguration: {status_msg}")
                return (status_msg, False)
                
        except Exception as e:
            error_msg = f"Error configuring RunPod: {str(e)}"
            print(f"RunPodConfiguration: {error_msg}")
            return (error_msg, False)


class RunPodInstanceManager:
    """Node for managing RunPod serverless instances"""
    
    @classmethod
    def INPUT_TYPES(cls):
        # Get existing instances for the dropdown
        try:
            settings = settings_manager.load_settings()
            instance_names = [instance.name for instance in settings.runpod.instances]
            instance_choices = ["CREATE_NEW"] + instance_names + ["DELETE_SELECTED"]
        except:
            instance_choices = ["CREATE_NEW", "DELETE_SELECTED"]
        
        return {
            "required": {
                "action": (instance_choices, {
                    "default": "CREATE_NEW"
                }),
                "instance_name": ("STRING", {
                    "multiline": False,
                    "default": ""
                }),
                "endpoint_id": ("STRING", {
                    "multiline": False,
                    "default": ""
                }),
            },
            "optional": {
                "description": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "enabled": ("BOOLEAN", {
                    "default": True
                }),
                "max_workers": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 10
                }),
                "timeout_seconds": ("INT", {
                    "default": 300,
                    "min": 30,
                    "max": 3600
                }),
                "set_as_default": ("BOOLEAN", {
                    "default": False
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "BOOLEAN")
    RETURN_NAMES = ("status_message", "success")
    FUNCTION = "manage_instance"
    CATEGORY = "ComfyBros/RunPod"
    
    def manage_instance(self, action: str, instance_name: str, endpoint_id: str,
                       description: str = "", enabled: bool = True,
                       max_workers: int = 1, timeout_seconds: int = 300,
                       set_as_default: bool = False) -> Tuple[str, bool]:
        """Manage RunPod instances (create, update, delete)"""
        try:
            if action == "CREATE_NEW":
                return self._create_instance(
                    instance_name, endpoint_id, description, enabled,
                    max_workers, timeout_seconds, set_as_default
                )
            elif action == "DELETE_SELECTED":
                return self._delete_instance(instance_name)
            elif action in settings_manager.load_settings().runpod.instances:
                return self._update_instance(
                    action, instance_name, endpoint_id, description, enabled,
                    max_workers, timeout_seconds, set_as_default
                )
            else:
                return ("Invalid action selected", False)
                
        except Exception as e:
            error_msg = f"Error managing RunPod instance: {str(e)}"
            print(f"RunPodInstanceManager: {error_msg}")
            return (error_msg, False)
    
    def _create_instance(self, name: str, endpoint_id: str, description: str,
                        enabled: bool, max_workers: int, timeout_seconds: int,
                        set_as_default: bool) -> Tuple[str, bool]:
        """Create a new RunPod instance"""
        if not name.strip():
            return ("Instance name is required", False)
        
        if not endpoint_id.strip():
            return ("Endpoint ID is required", False)
        
        instance = RunPodServerlessInstance(
            name=name.strip(),
            endpoint_id=endpoint_id.strip(),
            description=description.strip(),
            enabled=enabled,
            max_workers=max_workers,
            timeout_seconds=timeout_seconds
        )
        
        if settings_manager.add_runpod_instance(instance):
            status_msg = f"Created RunPod instance '{name}'"
            
            # Set as default if requested
            if set_as_default:
                settings = settings_manager.load_settings()
                settings.runpod.default_instance = name
                settings_manager.save_settings(settings)
                status_msg += " and set as default"
            
            print(f"RunPodInstanceManager: {status_msg}")
            return (status_msg, True)
        else:
            return (f"Failed to create instance '{name}' (name may already exist)", False)
    
    def _delete_instance(self, name: str) -> Tuple[str, bool]:
        """Delete a RunPod instance"""
        if not name.strip():
            return ("Instance name is required for deletion", False)
        
        if settings_manager.remove_runpod_instance(name.strip()):
            status_msg = f"Deleted RunPod instance '{name}'"
            print(f"RunPodInstanceManager: {status_msg}")
            return (status_msg, True)
        else:
            return (f"Failed to delete instance '{name}' (not found)", False)
    
    def _update_instance(self, selected_name: str, new_name: str, endpoint_id: str,
                        description: str, enabled: bool, max_workers: int,
                        timeout_seconds: int, set_as_default: bool) -> Tuple[str, bool]:
        """Update an existing RunPod instance"""
        settings = settings_manager.load_settings()
        
        # Find the instance to update
        instance_to_update = None
        for instance in settings.runpod.instances:
            if instance.name == selected_name:
                instance_to_update = instance
                break
        
        if not instance_to_update:
            return (f"Instance '{selected_name}' not found", False)
        
        # Update instance properties
        if new_name.strip() and new_name != selected_name:
            # Check if new name already exists
            for instance in settings.runpod.instances:
                if instance.name == new_name and instance != instance_to_update:
                    return (f"Instance name '{new_name}' already exists", False)
            instance_to_update.name = new_name.strip()
        
        if endpoint_id.strip():
            instance_to_update.endpoint_id = endpoint_id.strip()
        
        instance_to_update.description = description.strip()
        instance_to_update.enabled = enabled
        instance_to_update.max_workers = max_workers
        instance_to_update.timeout_seconds = timeout_seconds
        
        # Set as default if requested
        if set_as_default:
            settings.runpod.default_instance = instance_to_update.name
        
        if settings_manager.save_settings(settings):
            status_msg = f"Updated RunPod instance '{instance_to_update.name}'"
            if set_as_default:
                status_msg += " and set as default"
            print(f"RunPodInstanceManager: {status_msg}")
            return (status_msg, True)
        else:
            return ("Failed to save instance updates", False)


class RunPodInstanceSelector:
    """Node for selecting and outputting RunPod instance configurations"""
    
    @classmethod
    def INPUT_TYPES(cls):
        # Get available instances
        try:
            settings = settings_manager.load_settings()
            instance_names = [instance.name for instance in settings.runpod.instances if instance.enabled]
            if not instance_names:
                instance_names = ["No instances available"]
        except:
            instance_names = ["No instances available"]
        
        return {
            "required": {
                "instance": (instance_names, {
                    "default": instance_names[0] if instance_names else "No instances available"
                }),
            },
            "optional": {
                "use_default": ("BOOLEAN", {
                    "default": True
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT", "INT", "BOOLEAN")
    RETURN_NAMES = ("instance_name", "endpoint_id", "description", "max_workers", "timeout_seconds", "available")
    FUNCTION = "select_instance"
    CATEGORY = "ComfyBros/RunPod"
    
    def select_instance(self, instance: str, use_default: bool = True) -> Tuple[str, str, str, int, int, bool]:
        """Select a RunPod instance and output its configuration"""
        try:
            settings = settings_manager.load_settings()
            
            # Check if RunPod is enabled
            if not settings.runpod.enabled:
                print("RunPodInstanceSelector: RunPod integration is disabled")
                return ("", "", "RunPod integration disabled", 1, 300, False)
            
            # Get the selected instance
            selected_instance = None
            
            if use_default or instance == "No instances available":
                selected_instance = settings_manager.get_default_runpod_instance()
            else:
                selected_instance = settings_manager.get_runpod_instance(instance)
            
            if selected_instance and selected_instance.enabled:
                print(f"RunPodInstanceSelector: Selected instance '{selected_instance.name}'")
                return (
                    selected_instance.name,
                    selected_instance.endpoint_id,
                    selected_instance.description,
                    selected_instance.max_workers,
                    selected_instance.timeout_seconds,
                    True
                )
            else:
                error_msg = f"Instance '{instance}' not found or disabled"
                print(f"RunPodInstanceSelector: {error_msg}")
                return ("", "", error_msg, 1, 300, False)
                
        except Exception as e:
            error_msg = f"Error selecting RunPod instance: {str(e)}"
            print(f"RunPodInstanceSelector: {error_msg}")
            return ("", "", error_msg, 1, 300, False)