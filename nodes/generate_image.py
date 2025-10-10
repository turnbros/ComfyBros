import requests
import json
from typing import Tuple


class GenerateImage:
    """Generate images using RunPod serverless instances"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "endpoint": ("STRING", {"default": "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync"}),
                "auth_token": ("STRING", {"default": ""}),
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
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "generate"
    CATEGORY = "ComfyBros/Image Generation"
    
    def generate(self, endpoint: str, auth_token: str, positive_prompt: str, 
                negative_prompt: str, checkpoint: str, width: int, height: int,
                steps: int, cfg: float, seed: int, sampler_name: str, 
                scheduler: str, workflow_name: str) -> Tuple[str]:
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {auth_token}'
        }
        
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
            
            # Return the response as JSON string for now
            # In a real implementation, you might want to process the response
            # to extract image URLs or other specific data
            return (json.dumps(result, indent=2),)
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request error: {str(e)}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"JSON decode error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")