import requests
import json
import base64
import io
import torch
import os
from PIL import Image
from typing import Tuple


class GenerateImage:
    """Generate images using RunPod serverless instances"""
    
    @classmethod
    def get_instance_names(cls):
        """Get list of configured serverless instance names"""
        try:
            # Try to read from ComfyUI settings if available
            import folder_paths
            settings_file = os.path.join(folder_paths.get_user_data_path(), "settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    instances = settings.get("serverlessConfig.instances", [])
                    instance_names = [instance.get("name", f"Instance {i+1}") for i, instance in enumerate(instances) if instance.get("name")]
                    if instance_names:
                        return instance_names
        except Exception:
            pass
        return ["No instances configured"]
    
    @classmethod
    def INPUT_TYPES(cls):
        instance_names = cls.get_instance_names()
        return {
            "required": {
                "instance_name": (instance_names, {"default": instance_names[0] if instance_names else "No instances configured"}),
                "positive_prompt": ("STRING", {"multiline": True, "default": "a majestic dragon flying over a medieval castle"}),
                "negative_prompt": ("STRING", {"multiline": True, "default": "blurry, low quality, distorted"}),
                "checkpoint": ("STRING", {"default": "novaRealityXL_illustriousV70.safetensors"}),
                "width": ("INT", {"default": 512, "min": 64, "max": 2048, "step": 64}),
                "height": ("INT", {"default": 512, "min": 64, "max": 2048, "step": 64}),
                "steps": ("INT", {"default": 50, "min": 1, "max": 150}),
                "cfg": ("FLOAT", {"default": 5.0, "min": 1.0, "max": 30.0, "step": 0.1}),
                "seed": ("INT", {"default": 12345, "min": -1, "max": 2147483647}),
                "sampler_name": ("STRING", {"default": "dpmpp_2m_sde"}),
                "scheduler": ("STRING", {"default": "karras"}),
                "workflow_name": ("STRING", {"default": "text_to_image"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "metadata")
    FUNCTION = "generate"
    CATEGORY = "ComfyBros/Image Generation"
    
    def base64_to_tensor(self, base64_string: str) -> torch.Tensor:
        """Convert base64 string to torch tensor for ComfyUI"""
        # Decode base64 to bytes
        image_bytes = base64.b64decode(base64_string)
        
        # Create PIL Image from bytes
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Convert PIL to list of pixel values, then to tensor
        width, height = pil_image.size
        pixel_data = list(pil_image.getdata())
        
        # Convert to torch tensor and reshape
        image_tensor = torch.tensor(pixel_data, dtype=torch.float32)
        image_tensor = image_tensor.view(height, width, 3) / 255.0
        
        # Add batch dimension [H, W, C] -> [1, H, W, C]
        image_tensor = image_tensor.unsqueeze(0)
        
        return image_tensor

    def get_instance_config(self, instance_name: str) -> dict:
        """Get the configuration for the specified instance"""
        try:
            import folder_paths
            settings_file = os.path.join(folder_paths.get_user_data_path(), "settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    instances = settings.get("serverlessConfig.instances", [])
                    for instance in instances:
                        if instance.get("name") == instance_name:
                            return {
                                "endpoint": instance.get("endpoint", ""),
                                "headers": {
                                    'Content-Type': 'application/json',
                                    'Authorization': f'Bearer {instance.get("auth_token", "")}'
                                }
                            }
        except Exception as e:
            raise RuntimeError(f"Error loading instance configuration: {str(e)}")
        
        raise RuntimeError(f"Instance '{instance_name}' not found in configuration")

    def generate(self, instance_name: str, positive_prompt: str, 
                negative_prompt: str, checkpoint: str, width: int, height: int,
                steps: int, cfg: float, seed: int, sampler_name: str, 
                scheduler: str, workflow_name: str) -> Tuple[torch.Tensor, str]:
        
        # Get instance configuration
        config = self.get_instance_config(instance_name)
        endpoint = config["endpoint"]
        headers = config["headers"]
        
        # Prepare payload structure
        payload = {
            "input": {
                "workflow_name": workflow_name,
                "workflow_params": {
                    "positive_prompt": positive_prompt,
                    "negative_prompt": negative_prompt,
                    "checkpoint": checkpoint,
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "cfg": cfg,
                    "seed": seed,
                    "sampler_name": sampler_name,
                    "scheduler": scheduler
                }
            }
        }
        
        try:
            # Make the request to RunPod
            response = requests.post(endpoint, headers=headers, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            
            # Parse the response to extract image data
            if ("output" in result and 
                "result" in result["output"] and 
                "images" in result["output"]["result"] and 
                len(result["output"]["result"]["images"]) > 0):
                
                # Get the first image
                first_image = result["output"]["result"]["images"][0]
                
                if "data" in first_image:
                    # Convert base64 image to tensor
                    image_tensor = self.base64_to_tensor(first_image["data"])
                    
                    # Create metadata string with generation parameters
                    metadata = {
                        "filename": first_image.get("filename", "generated_image.png"),
                        "format": first_image.get("format", "PNG"),
                        "parameters": result["output"]["result"].get("parameters", {}),
                        "execution_time": result.get("executionTime", 0),
                        "delay_time": result.get("delayTime", 0),
                        "status": result["output"]["result"].get("status", "unknown")
                    }
                    
                    return (image_tensor, json.dumps(metadata, indent=2))
                else:
                    raise RuntimeError("No image data found in response")
            else:
                raise RuntimeError(f"Unexpected response structure: {json.dumps(result, indent=2)}")
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request error: {str(e)}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"JSON decode error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")