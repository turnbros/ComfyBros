import time
import os
import tempfile
import zipfile
import boto3
from botocore.exceptions import ClientError

import requests
import json
import base64
import io
import torch
from PIL import Image
from typing import Tuple, List
import folder_paths
from ._instance_utils import instance_config, instance_names
from ._runpod_utils import send_request, cancel_job


class GenerateImage:
    """Generate images using RunPod serverless instances"""
    
    @classmethod
    def INPUT_TYPES(cls):
        names = instance_names()
        return {
            "required": {
                "instance_name": (names, {"default": names[0] if names else "No instances configured"}),
                "positive_prompt": ("STRING", {"multiline": True, "default": "a majestic dragon flying over a medieval castle"}),
                "negative_prompt": ("STRING", {"multiline": True, "default": "blurry, low quality, distorted"}),
                "checkpoint": ("STRING", {"default": "novaRealityXL_illustriousV70.safetensors"}),
                "width": ("INT", {"default": 512, "min": 128, "max": 2048, "step": 16}),
                "height": ("INT", {"default": 512, "min": 128, "max": 2048, "step": 16}),
                "steps": ("INT", {"default": 50, "min": 1, "max": 150}),
                "cfg": ("FLOAT", {"default": 5.0, "min": 1.0, "max": 30.0, "step": 0.1}),
                "seed": ("INT", {"default": 12345, "min": -1, "max": 2147483647}),
                "sampler_name": ([
                    "euler", "euler_ancestral", "heun", "heunpp2", "dpm_2", "dpm_2_ancestral",
                    "lms", "dpm_fast", "dpm_adaptive", "dpmpp_2s_ancestral", "dpmpp_sde", "dpmpp_sde_gpu",
                    "dpmpp_2m", "dpmpp_2m_sde", "dpmpp_2m_sde_gpu", "dpmpp_3m_sde", "dpmpp_3m_sde_gpu", 
                    "ddpm", "lcm", "ddim", "uni_pc", "uni_pc_bh2"
                ], {"default": "dpmpp_2m_sde"}),
                "scheduler": ([
                    "normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform", "beta"
                ], {"default": "karras"}),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 512}),
                "upscale": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "metadata")
    FUNCTION = "generate"
    CATEGORY = "ComfyBros/Image Generation"
    API_NODE = True
    
    def __init__(self):
        self._current_job_id = None
    
    def cancel(self):
        """Cancel the current RunPod job if running"""
        if self._current_job_id:
            print(f"Cancelling RunPod job {self._current_job_id}")
            cancel_job(self._current_job_id)
            self._current_job_id = None
    
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

    def get_r2_config(self) -> dict:
        """Get R2 configuration from settings"""
        try:
            settings_file = os.path.join(folder_paths.base_path, "user", "default", "comfy.settings.json")
            print(f"Printing settings file path for R2 config: {settings_file}")

            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    required_keys = ["serverlessConfig.offloadBucket.cloudflare_account_id", "serverlessConfig.offloadBucket.name", "serverlessConfig.offloadBucket.secret_key_id", "serverlessConfig.offloadBucket.secret_key"]
                    if all(key in settings for key in required_keys):
                        return {
                            "account_id": settings["serverlessConfig.offloadBucket.cloudflare_account_id"],
                            "bucket_name": settings["serverlessConfig.offloadBucket.name"],
                            "access_key_id": settings["serverlessConfig.offloadBucket.secret_key_id"],
                            "secret_access_key": settings["serverlessConfig.offloadBucket.secret_key"]
                        }
                    else:
                        missing_keys = [key for key in required_keys if key not in settings]
                        raise RuntimeError(f"Missing R2 configuration keys: {missing_keys}")
        except Exception as e:
            raise RuntimeError(f"Error loading R2 configuration: {str(e)}")
        
        raise RuntimeError("R2 configuration not found in settings")

    def download_r2_archive(self, bucket: str, key: str) -> bytes:
        """Download ZIP archive from Cloudflare R2 using boto3"""
        try:
            r2_config = self.get_r2_config()
            
            # Create S3 client configured for Cloudflare R2
            account_id = r2_config["account_id"]
            endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
            
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=r2_config["access_key_id"],
                aws_secret_access_key=r2_config["secret_access_key"],
                region_name='auto'  # R2 uses 'auto' as the region
            )
            
            print(f"Downloading {key} from R2 bucket {bucket}...")
            
            # Download the object
            response = s3_client.get_object(Bucket=bucket, Key=key)
            
            # Read the content
            content = response['Body'].read()
            
            print(f"Downloaded {len(content)} bytes from R2")
            
            return content
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise RuntimeError(f"R2 client error ({error_code}): {error_message}")
        except Exception as e:
            raise RuntimeError(f"Error downloading archive from R2: {str(e)}")

    def extract_images_from_zip(self, zip_data: bytes) -> List[dict]:
        """Extract image files from ZIP archive and convert to image data"""
        try:
            images = []
            
            # Create a temporary directory for extraction
            temp_dir = tempfile.mkdtemp(prefix='r2_images_')
            
            try:
                # Extract ZIP archive
                with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_file:
                    zip_file.extractall(temp_dir)
                
                # Get all image files and sort them
                image_files = []
                for filename in os.listdir(temp_dir):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        image_files.append(filename)
                
                # Sort by image number if possible, otherwise alphabetically
                try:
                    # Try to sort by numeric image number in filename
                    image_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x))))
                except:
                    # Fall back to alphabetical sort
                    image_files.sort()
                
                # Convert each image to base64
                for i, filename in enumerate(image_files):
                    file_path = os.path.join(temp_dir, filename)
                    
                    with open(file_path, 'rb') as f:
                        image_data = f.read()
                        base64_data = base64.b64encode(image_data).decode('utf-8')
                    
                    images.append({
                        "data": base64_data,
                        "format": "PNG",
                        "filename": filename
                    })
                
            finally:
                # Clean up temporary directory
                try:
                    for filename in os.listdir(temp_dir):
                        os.remove(os.path.join(temp_dir, filename))
                    os.rmdir(temp_dir)
                except:
                    pass
            
            return images
            
        except Exception as e:
            raise RuntimeError(f"Error extracting images from ZIP: {str(e)}")

    def generate(self, instance_name: str, positive_prompt: str,
                negative_prompt: str, checkpoint: str, width: int, height: int,
                steps: int, cfg: float, seed: int, sampler_name: str,
                scheduler: str, denoise: float, batch_size: int, upscale: bool) -> Tuple[torch.Tensor, str]:

        # Get instance configuration
        config = instance_config(instance_name)
        endpoint = config["endpoint"]
        headers = config["headers"]
        
        # Prepare payload structure
        payload = {
            "input": {
                "positive_prompt": positive_prompt,
                "negative_prompt": negative_prompt,
                "checkpoint": checkpoint,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg": cfg,
                "seed": seed,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "denoise": denoise,
                "batch_size": batch_size,
                "upscale": upscale
            }
        }
        
        try:
            # Make the request to RunPod
            def set_job_id(job_id):
                self._current_job_id = job_id
            
            result = send_request(endpoint, headers, payload, job_callback=set_job_id)
            self._current_job_id = None  # Clear after completion

            # Parse the response to extract image data
            if ("output" in result and
                "images" in result["output"]):
                
                images_info = result["output"]["images"]
                
                # Check if this is the new R2 ZIP archive format
                if isinstance(images_info, dict) and "bucket" in images_info and "key" in images_info:
                    image_count = result["output"].get("image_count", 0)
                    print(f"Downloading ZIP archive with {image_count} images from R2...")
                    
                    # Download ZIP archive from R2
                    bucket = images_info["bucket"]
                    key = images_info["key"]
                    zip_data = self.download_r2_archive(bucket, key)
                    
                    print(f"Extracting {image_count} images from ZIP archive...")
                    
                    # Extract images from ZIP
                    images = self.extract_images_from_zip(zip_data)
                    
                    print(f"Converting {len(images)} images to tensor batch...")
                    
                    # Process all images in the batch
                    image_tensors = []
                    for i, image_data in enumerate(images):
                        if "data" in image_data:
                            # Convert base64 image to tensor
                            image_tensor = self.base64_to_tensor(image_data["data"])
                            image_tensors.append(image_tensor)
                        else:
                            raise RuntimeError(f"No image data found in response for image {i}")
                    
                    # Stack all images into a single batch tensor
                    if image_tensors:
                        batch_tensor = torch.cat(image_tensors, dim=0)
                        
                        # Create metadata string with generation parameters
                        metadata = {
                            "batch_size": len(image_tensors),
                            "image_count": image_count,
                            "tensor_shape": list(batch_tensor.shape),
                            "filenames": [img.get("filename", f"generated_image_{i}.png") 
                                        for i, img in enumerate(images)],
                            "format": images[0].get("format", "PNG") if images else "PNG",
                            "parameters": result["output"].get("parameters", {}),
                            "execution_time": result.get("executionTime", 0),
                            "delay_time": result.get("delayTime", 0),
                            "status": result["output"].get("status", "unknown"),
                            "r2_info": {
                                "bucket": bucket,
                                "key": key,
                                "filename": images_info.get("filename", "unknown"),
                                "size_bytes": images_info.get("size_bytes", 0)
                            }
                        }
                        
                        return (batch_tensor, json.dumps(metadata, indent=2))
                    else:
                        raise RuntimeError("No valid images found in batch")
                
                # Handle legacy format (direct image array)
                elif isinstance(images_info, list) and len(images_info) > 0:
                    # Process all images in the batch (legacy format)
                    image_tensors = []
                    for i, image_data in enumerate(images_info):
                        if "data" in image_data:
                            # Convert base64 image to tensor
                            image_tensor = self.base64_to_tensor(image_data["data"])
                            image_tensors.append(image_tensor)
                        else:
                            raise RuntimeError(f"No image data found in response for image {i}")
                    
                    # Stack all images into a single batch tensor
                    if image_tensors:
                        batch_tensor = torch.cat(image_tensors, dim=0)
                        
                        # Create metadata string with generation parameters
                        metadata = {
                            "batch_size": len(image_tensors),
                            "filenames": [img.get("filename", f"generated_image_{i}.png") 
                                        for i, img in enumerate(images_info)],
                            "format": images_info[0].get("format", "PNG"),
                            "parameters": result["output"].get("parameters", {}),
                            "execution_time": result.get("executionTime", 0),
                            "delay_time": result.get("delayTime", 0),
                            "status": result["output"].get("status", "unknown")
                        }
                        
                        return (batch_tensor, json.dumps(metadata, indent=2))
                    else:
                        raise RuntimeError("No valid images found in batch")
                else:
                    raise RuntimeError("No images found in response")
            else:
                raise RuntimeError(f"Unexpected response structure: {json.dumps(result, indent=2)}")
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request error: {str(e)}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"JSON decode error: {str(e)}")
        except Exception as e:
            # Clear job ID on any error
            self._current_job_id = None
            raise RuntimeError(f"Unexpected error: {str(e)}")