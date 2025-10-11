import requests
import json
import base64
import io
import torch
import os
import random
import tempfile
from PIL import Image
from typing import Tuple
import folder_paths


class WAN22GenerateVideo:
    """Generate videos using RunPod serverless instances with image_to_video workflow"""
    
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
                "input_image": ("IMAGE",),
                "positive_prompt": ("STRING", {"multiline": True, "default": "something positive"}),
                "negative_prompt": ("STRING", {"multiline": True, "default": "blurry, low quality, distorted"}),
                "width": ("INT", {"default": 512, "min": 64, "max": 2048, "step": 64}),
                "height": ("INT", {"default": 512, "min": 64, "max": 2048, "step": 64}),
                "length": ("INT", {"default": 81, "min": 1, "max": 300}),
                "fps": ("INT", {"default": 24, "min": 1, "max": 60}),
                "steps": ("INT", {"default": 4, "min": 1, "max": 150}),
                "cfg": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 30.0, "step": 0.1}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "sampler_name": ("STRING", {"default": "euler"}),
                "scheduler": ("STRING", {"default": "simple"}),
            },
            "optional": {
                "input_image_string": ("STRING", {"multiline": True, "default": ""}),
            }
        }
    
    RETURN_TYPES = ("VIDEO", "STRING")
    RETURN_NAMES = ("video_data", "metadata")
    FUNCTION = "generate"
    CATEGORY = "ComfyBros/Video Generation"
    
    def tensor_to_base64(self, tensor: torch.Tensor) -> str:
        """Convert torch tensor to base64 string"""
        # Convert tensor from [B, H, W, C] format (ComfyUI format) to PIL Image
        if tensor.dim() == 4:
            # Take first batch item if batched
            tensor = tensor[0]
        
        # Ensure tensor is in [H, W, C] format and convert to uint8
        if tensor.max() <= 1.0:
            # Tensor is normalized, scale to 0-255
            tensor = (tensor * 255).clamp(0, 255).to(torch.uint8)
        else:
            tensor = tensor.clamp(0, 255).to(torch.uint8)
        
        # Convert to PIL Image
        numpy_image = tensor.cpu().numpy()
        pil_image = Image.fromarray(numpy_image, mode='RGB')
        
        # Convert to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def base64_to_video_file(self, base64_string: str, filename: str = None) -> str:
        """Convert base64 string to video file and return file path"""
        try:
            # Decode base64 to bytes
            video_bytes = base64.b64decode(base64_string)
            
            # Create a temporary file for the video
            if filename and filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                # Use provided filename if it has a video extension
                video_extension = os.path.splitext(filename)[1]
            else:
                # Default to .mp4
                video_extension = '.mp4'
            
            # Create temp file in ComfyUI's output directory if possible
            try:
                output_dir = folder_paths.get_output_directory()
            except:
                output_dir = tempfile.gettempdir()
            
            # Create unique filename
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=video_extension, 
                dir=output_dir,
                prefix='generated_video_'
            )
            
            # Write video data to file
            temp_file.write(video_bytes)
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            raise RuntimeError(f"Error converting base64 to video file: {str(e)}")

    def process_input_image(self, input_image, input_image_string: str = None) -> str:
        """Process input image - either torch tensor, base64 data, or file path"""
        # If input_image is a torch tensor (from IMAGE input)
        if isinstance(input_image, torch.Tensor):
            return self.tensor_to_base64(input_image)
        
        # If input_image_string is provided and input_image is empty/None, use the string
        if input_image_string and input_image_string.strip():
            input_image = input_image_string
        
        # Handle string inputs (base64 or file path)
        if isinstance(input_image, str):
            if not input_image.strip():
                raise RuntimeError("Input image is required")
            
            # Check if it's already base64 encoded data
            if input_image.startswith('data:image/'):
                # Extract base64 data from data URL
                return input_image.split(',', 1)[1]
            elif self.is_base64(input_image):
                # Already base64 encoded
                return input_image
            else:
                # Treat as file path
                return self.file_to_base64(input_image)
        
        raise RuntimeError("Invalid input image format")
    
    def is_base64(self, s: str) -> bool:
        """Check if string is valid base64"""
        try:
            base64.b64decode(s, validate=True)
            return True
        except Exception:
            return False
    
    def file_to_base64(self, file_path: str) -> str:
        """Convert image file to base64"""
        try:
            # Try relative to ComfyUI input directory first
            full_path = os.path.join(folder_paths.get_input_directory(), file_path)
            if not os.path.exists(full_path):
                # Try absolute path
                full_path = file_path
            
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Image file not found: {file_path}")
            
            with open(full_path, 'rb') as f:
                image_data = f.read()
                return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            raise RuntimeError(f"Error reading image file '{file_path}': {str(e)}")

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

    def generate(self, instance_name: str, input_image, positive_prompt: str, 
                negative_prompt: str, width: int, height: int, length: int, fps: int,
                steps: int, cfg: float, seed: int, sampler_name: str, 
                scheduler: str, input_image_string: str = None) -> Tuple[str, str]:
        
        # Process the input image
        processed_image = self.process_input_image(input_image, input_image_string)
        
        # Generate random seed if -1
        if seed == -1:
            seed = random.randint(0, 2147483647)
        
        # Get instance configuration
        config = self.get_instance_config(instance_name)
        endpoint = config["endpoint"]
        headers = config["headers"]
        
        # Prepare payload structure for image_to_video workflow
        payload = {
            "input": {
                "workflow_name": "image_to_video",
                "workflow_params": {
                    "input_image": processed_image,
                    "positive_prompt": positive_prompt,
                    "negative_prompt": negative_prompt,
                    "width": width,
                    "height": height,
                    "length": length,
                    "fps": fps,
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
            response = requests.post(endpoint, headers=headers, json=payload, timeout=600)
            response.raise_for_status()
            
            result = response.json()
            
            # Parse the response to extract video data
            if ("output" in result and 
                "result" in result["output"] and 
                "videos" in result["output"]["result"] and 
                len(result["output"]["result"]["videos"]) > 0):
                
                # Get the first video
                first_video = result["output"]["result"]["videos"][0]
                
                if "data" in first_video:
                    # Convert base64 video data to file
                    video_base64 = first_video["data"]
                    filename = first_video.get("filename", "generated_video.mp4")
                    
                    # Convert base64 to video file
                    video_file_path = self.base64_to_video_file(video_base64, filename)
                    
                    # Create metadata string with generation parameters
                    metadata = {
                        "filename": filename,
                        "file_path": video_file_path,
                        "format": first_video.get("format", "MP4"),
                        "parameters": result["output"]["result"].get("parameters", {}),
                        "execution_time": result.get("executionTime", 0),
                        "delay_time": result.get("delayTime", 0),
                        "status": result["output"]["result"].get("status", "unknown"),
                        "video_info": {
                            "width": width,
                            "height": height,
                            "length": length,
                            "fps": fps
                        }
                    }
                    
                    return (video_file_path, json.dumps(metadata, indent=2))
                else:
                    raise RuntimeError("No video data found in response")
            else:
                raise RuntimeError(f"Unexpected response structure: {json.dumps(result, indent=2)}")
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request error: {str(e)}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"JSON decode error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")