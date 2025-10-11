import requests
import json
import base64
import io
import torch
import random
import re
import os
import folder_paths
from PIL import Image
from typing import Tuple, Optional


class OllamaConnection:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "endpoint_url": ("STRING", {"default": "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync"}),
                "api_key": ("STRING", {"default": ""}),
            }
        }
    
    RETURN_TYPES = ("OLLAMA_CONNECTION",)
    FUNCTION = "create_connection"
    CATEGORY = "ComfyBros/LLM"
    
    def create_connection(self, endpoint_url: str, api_key: str) -> Tuple[dict]:
        connection = {
            "endpoint_url": endpoint_url,
            "api_key": api_key,
            "headers": {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
        }
        return (connection,)


class OllamaConfiguration:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "max_tokens": ("INT", {"default": 512, "min": 1, "max": 4096}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.1}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "control_after_generate": (["fixed", "randomize"], {"default": "fixed"}),
                # Defaults to 240 since that seems to be how long a coldstart takes
                "read_timeout": ("INT", {"default": 240, "min": 1, "max": 600}),
            }
        }
    
    RETURN_TYPES = ("OLLAMA_CONFIG",)
    FUNCTION = "create_config"
    CATEGORY = "ComfyBros/LLM"
    
    def create_config(self, max_tokens: int, temperature: float, seed: int, control_after_generate: str, read_timeout: int) -> Tuple[dict]:
        config = {
            "max_tokens": max_tokens,
            "temperature": temperature,
            "seed": seed,
            "control_after_generate": control_after_generate,
            "read_timeout": read_timeout
        }
        return (config,)


class OllamaConverse:
    @classmethod
    def get_instance_names(cls):
        """Get list of configured serverless instance names"""
        try:
            settings_file = os.path.join(folder_paths.base_path, "user", "default", "comfy.settings.json")

            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    instances = settings.get("serverlessConfig.instances", [])
                    if instances:
                        instance_names = [instance.get("name", f"Instance {i+1}") for i, instance in enumerate(instances) if instance.get("name")]
                        if instance_names:
                            return instance_names
                                
        except Exception as e:
            print(f"Error reading instance configuration: {e}")
        return ["No instances configured"]

    @classmethod
    def INPUT_TYPES(cls):
        instance_names = cls.get_instance_names()
        return {
            "required": {
                "instance_name": (instance_names, {"default": instance_names[0] if instance_names else "No instances configured"}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "max_tokens": ("INT", {"default": 512, "min": 1, "max": 4096}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.1}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
            },
            "optional": {
                "image": ("IMAGE",),
                "system_prompt": ("STRING", {"multiline": True, "default": ""}),
                "read_timeout": ("INT", {"default": 240, "min": 1, "max": 600}),
            }
        }
    
    RETURN_TYPES = ("STRING", "OLLAMA_META")
    RETURN_NAMES = ("response", "meta")
    FUNCTION = "generate_response"
    CATEGORY = "ComfyBros/LLM"
    
    def tensor_to_base64(self, image_tensor: torch.Tensor) -> str:
        """Convert torch tensor to base64 encoded image string"""
        # Convert from [batch, height, width, channels] to PIL Image
        if len(image_tensor.shape) == 4:
            # Take first image from batch
            image_tensor = image_tensor[0]
        
        # Convert to numpy and scale to 0-255
        image_np = (image_tensor.cpu().numpy() * 255).astype('uint8')
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image_np)
        
        # Convert to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str
    
    def get_instance_config(self, instance_name: str) -> dict:
        """Get the configuration for the specified instance"""
        try:
            settings_file = os.path.join(folder_paths.base_path, "user", "default", "comfy.settings.json")

            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    instances = settings.get("serverlessConfig.instances", [])
                    if instances:
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

    def generate_response(self, instance_name: str, prompt: str, max_tokens: int, 
                         temperature: float, seed: int, image: Optional[torch.Tensor] = None, 
                         system_prompt: str = "", read_timeout: int = 240) -> Tuple[str, dict]:
        
        # Get instance configuration
        try:
            instance_config = self.get_instance_config(instance_name)
            endpoint_url = instance_config["endpoint"]
            headers = instance_config["headers"]
        except Exception as e:
            return (f"Error: {str(e)}", {})
        
        # Use the seed parameter directly
        current_seed = seed
        
        # Prepare the input payload
        input_data = {
            "prompt": prompt,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            }
        }
        
        # Add seed to options if it's not -1 (default)
        if current_seed != -1:
            input_data["options"]["seed"] = current_seed
        
        # Add system prompt if provided
        if system_prompt.strip():
            input_data["system"] = system_prompt
        
        # Add image if provided
        if image is not None:
            try:
                image_b64 = self.tensor_to_base64(image)
                input_data["images"] = [image_b64]
            except Exception as e:
                return (f"Error processing image: {str(e)}", {})
        
        payload = {"input": input_data}
        
        # Create meta output for compatibility
        output_meta = {
            "instance_name": instance_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "seed": current_seed
        }
        
        try:
            response = requests.post(endpoint_url, headers=headers, json=payload, timeout=read_timeout)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the response text from RunPod response structure
            if "output" in result and isinstance(result["output"], list) and len(result["output"]) > 0:
                output_item = result["output"][0]
                if "choices" in output_item and isinstance(output_item["choices"], list) and len(output_item["choices"]) > 0:
                    choice = output_item["choices"][0]
                    if "text" in choice:
                        return (choice["text"], output_meta)
            
            # Fallback for old response format
            if "output" in result:
                if isinstance(result["output"], dict) and "response" in result["output"]:
                    return (result["output"]["response"], output_meta)
                elif isinstance(result["output"], str):
                    return (result["output"], output_meta)
            
            # Final fallback: return the full response as JSON string
            return (json.dumps(result, indent=2), output_meta)
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request error: {str(e)}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"JSON decode error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")


