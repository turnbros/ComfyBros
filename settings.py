"""
ComfyBros Settings Management System
Handles configuration for RunPod serverless instances and other extension settings.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field


@dataclass
class RunPodServerlessInstance:
    """Configuration for a RunPod serverless instance"""
    name: str
    endpoint_id: str
    description: str = ""
    enabled: bool = True
    max_workers: int = 1
    timeout_seconds: int = 300


@dataclass
class RunPodSettings:
    """RunPod API configuration"""
    api_key: str = ""
    instances: List[RunPodServerlessInstance] = field(default_factory=list)
    default_instance: str = ""
    enabled: bool = False


@dataclass
class ComfyBrosSettings:
    """Main settings for ComfyBros extension"""
    runpod: RunPodSettings = field(default_factory=RunPodSettings)
    
    
class SettingsManager:
    """Manages settings persistence and access"""
    
    def __init__(self, settings_file: str = "comfybros_settings.json"):
        self.settings_file = settings_file
        self.settings_path = self._get_settings_path()
        self._settings: Optional[ComfyBrosSettings] = None
    
    def _get_settings_path(self) -> str:
        """Get the full path to the settings file"""
        # Try to save in ComfyUI's user directory if available
        try:
            import folder_paths
            user_dir = folder_paths.get_user_directory()
            return os.path.join(user_dir, self.settings_file)
        except (ImportError, AttributeError):
            # Fallback to extension directory
            ext_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(ext_dir, self.settings_file)
    
    def load_settings(self) -> ComfyBrosSettings:
        """Load settings from file or create default settings"""
        if self._settings is not None:
            return self._settings
            
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, 'r') as f:
                    data = json.load(f)
                self._settings = self._dict_to_settings(data)
                print(f"ComfyBros: Loaded settings from {self.settings_path}")
            except Exception as e:
                print(f"ComfyBros: Error loading settings: {e}")
                self._settings = ComfyBrosSettings()
        else:
            self._settings = ComfyBrosSettings()
            print("ComfyBros: Created default settings")
            
        return self._settings
    
    def save_settings(self, settings: Optional[ComfyBrosSettings] = None) -> bool:
        """Save settings to file"""
        if settings is None:
            settings = self._settings
        if settings is None:
            return False
            
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            
            with open(self.settings_path, 'w') as f:
                json.dump(self._settings_to_dict(settings), f, indent=2)
            print(f"ComfyBros: Saved settings to {self.settings_path}")
            self._settings = settings
            return True
        except Exception as e:
            print(f"ComfyBros: Error saving settings: {e}")
            return False
    
    def _settings_to_dict(self, settings: ComfyBrosSettings) -> Dict[str, Any]:
        """Convert settings to dictionary for JSON serialization"""
        result = asdict(settings)
        # Convert instances list properly
        if 'runpod' in result and 'instances' in result['runpod']:
            result['runpod']['instances'] = [
                asdict(instance) if hasattr(instance, '__dict__') else instance
                for instance in settings.runpod.instances
            ]
        return result
    
    def _dict_to_settings(self, data: Dict[str, Any]) -> ComfyBrosSettings:
        """Convert dictionary to settings object"""
        # Handle RunPod instances
        runpod_data = data.get('runpod', {})
        instances_data = runpod_data.get('instances', [])
        instances = [
            RunPodServerlessInstance(**instance_data) if isinstance(instance_data, dict) else instance_data
            for instance_data in instances_data
        ]
        
        runpod_settings = RunPodSettings(
            api_key=runpod_data.get('api_key', ''),
            instances=instances,
            default_instance=runpod_data.get('default_instance', ''),
            enabled=runpod_data.get('enabled', False)
        )
        
        return ComfyBrosSettings(runpod=runpod_settings)
    
    def get_runpod_settings(self) -> RunPodSettings:
        """Get RunPod specific settings"""
        settings = self.load_settings()
        return settings.runpod
    
    def update_runpod_api_key(self, api_key: str) -> bool:
        """Update RunPod API key"""
        settings = self.load_settings()
        settings.runpod.api_key = api_key
        return self.save_settings(settings)
    
    def add_runpod_instance(self, instance: RunPodServerlessInstance) -> bool:
        """Add a new RunPod instance"""
        settings = self.load_settings()
        
        # Check if instance with same name already exists
        for existing in settings.runpod.instances:
            if existing.name == instance.name:
                print(f"ComfyBros: Instance '{instance.name}' already exists")
                return False
        
        settings.runpod.instances.append(instance)
        
        # Set as default if it's the first instance
        if len(settings.runpod.instances) == 1:
            settings.runpod.default_instance = instance.name
            
        return self.save_settings(settings)
    
    def remove_runpod_instance(self, instance_name: str) -> bool:
        """Remove a RunPod instance"""
        settings = self.load_settings()
        
        # Find and remove instance
        for i, instance in enumerate(settings.runpod.instances):
            if instance.name == instance_name:
                settings.runpod.instances.pop(i)
                
                # Update default instance if needed
                if settings.runpod.default_instance == instance_name:
                    settings.runpod.default_instance = (
                        settings.runpod.instances[0].name if settings.runpod.instances else ""
                    )
                
                return self.save_settings(settings)
        
        print(f"ComfyBros: Instance '{instance_name}' not found")
        return False
    
    def get_runpod_instance(self, instance_name: str) -> Optional[RunPodServerlessInstance]:
        """Get a specific RunPod instance by name"""
        settings = self.load_settings()
        for instance in settings.runpod.instances:
            if instance.name == instance_name:
                return instance
        return None
    
    def get_default_runpod_instance(self) -> Optional[RunPodServerlessInstance]:
        """Get the default RunPod instance"""
        settings = self.load_settings()
        if settings.runpod.default_instance:
            return self.get_runpod_instance(settings.runpod.default_instance)
        elif settings.runpod.instances:
            return settings.runpod.instances[0]
        return None


# Global settings manager instance
settings_manager = SettingsManager()