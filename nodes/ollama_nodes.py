import requests
import json
import base64
import io
import torch
import random
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
            }
        }
    
    RETURN_TYPES = ("OLLAMA_CONFIG",)
    FUNCTION = "create_config"
    CATEGORY = "ComfyBros/LLM"
    
    def create_config(self, max_tokens: int, temperature: float, seed: int, control_after_generate: str) -> Tuple[dict]:
        config = {
            "max_tokens": max_tokens,
            "temperature": temperature,
            "seed": seed,
            "control_after_generate": control_after_generate
        }
        return (config,)


class OllamaConverse:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "connection": ("OLLAMA_CONNECTION",),
                "config": ("OLLAMA_CONFIG",),
                "meta": ("OLLAMA_META",),
                "image": ("IMAGE",),
                "system_prompt": ("STRING", {"multiline": True, "default": ""}),
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
    
    def generate_response(self, prompt: str, connection: Optional[dict] = None, 
                         config: Optional[dict] = None, meta: Optional[dict] = None,
                         image: Optional[torch.Tensor] = None, system_prompt: str = "") -> Tuple[str, dict]:
        
        # Use meta if provided, otherwise use direct connection/config
        if meta is not None:
            actual_connection = meta.get("connection")
            actual_config = meta.get("config")
        else:
            actual_connection = connection
            actual_config = config
        
        # Validate we have required connection and config
        if actual_connection is None:
            return ("Error: No connection provided (either directly or via meta)", {})
        if actual_config is None:
            return ("Error: No configuration provided (either directly or via meta)", {})
        
        endpoint_url = actual_connection["endpoint_url"]
        headers = actual_connection["headers"]
        
        # Handle seed and control_after_generate logic
        current_seed = actual_config.get("seed", -1)
        control_after_generate = actual_config.get("control_after_generate", "fixed")
        
        # If control_after_generate is "randomize", generate a random seed
        if control_after_generate == "randomize":
            current_seed = random.randint(0, 2147483647)
        
        # Prepare the input payload
        input_data = {
            "prompt": prompt,
            "options": {
                "num_predict": actual_config["max_tokens"],
                "temperature": actual_config["temperature"]
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
                # Create meta for error case
                output_meta = {
                    "connection": actual_connection,
                    "config": actual_config
                }
                return (f"Error processing image: {str(e)}", output_meta)
        
        payload = {"input": input_data}
        
        # Create updated config with the current seed for passing to next node
        updated_config = actual_config.copy()
        updated_config["current_seed"] = current_seed
        
        # Create meta output to pass connection and config to next node
        output_meta = {
            "connection": actual_connection,
            "config": updated_config
        }
        
        try:
            response = requests.post(endpoint_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the response text from RunPod response structure
            if "output" in result:
                if isinstance(result["output"], dict) and "response" in result["output"]:
                    return (result["output"]["response"], output_meta)
                elif isinstance(result["output"], str):
                    return (result["output"], output_meta)
            
            # Fallback: return the full response as JSON string
            return (json.dumps(result, indent=2), output_meta)
            
        except requests.exceptions.RequestException as e:
            return (f"Request error: {str(e)}", output_meta)
        except json.JSONDecodeError as e:
            return (f"JSON decode error: {str(e)}", output_meta)
        except Exception as e:
            return (f"Unexpected error: {str(e)}", output_meta)


