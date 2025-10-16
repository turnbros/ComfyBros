import json
import base64
import io
import torch
import os
import random
import tempfile
import time
import subprocess
import zipfile
import boto3
from botocore.exceptions import ClientError
from PIL import Image
from typing import Tuple, List
import folder_paths
from ._instance_utils import instance_config, instance_names
from ._runpod_utils import send_request


class TextToVideo:
    """Generate videos from text using RunPod serverless instances with standalone_text_to_video workflow"""
    
    @classmethod
    def INPUT_TYPES(cls):
        names = instance_names()
        return {
            "required": {
                "instance_name": (names, {"default": names[0] if names else "No instances configured"}),
                "positive_prompt": ("STRING", {"multiline": True, "default": "a beautiful landscape with mountains and trees"}),
                "negative_prompt": ("STRING", {"multiline": True, "default": "Bright tones, overexposed, static, blurred details, subtitles, style, works, paintings, images, static, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background, three legs, many people in the background, walking backwards"}),
                "width": ("INT", {"default": 512, "min": 64, "max": 2048, "step": 64}),
                "height": ("INT", {"default": 512, "min": 64, "max": 2048, "step": 64}),
                "length": ("INT", {"default": 81, "min": 1, "max": 300}),
                "fps": ("INT", {"default": 24, "min": 1, "max": 60}),
                "steps": ("INT", {"default": 50, "min": 1, "max": 150}),
                "cfg": ("FLOAT", {"default": 5, "min": 0.1, "max": 30.0, "step": 0.1}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 32}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("frames", "metadata")
    FUNCTION = "generate"
    CATEGORY = "ComfyBros/Video Generation"
    
    def frames_to_tensor_batch(self, frames: List[dict]) -> torch.Tensor:
        """Convert list of base64 frame data to batched tensor for ComfyUI"""
        # Sort frames by frame_number to ensure correct sequence
        sorted_frames = sorted(frames, key=lambda x: x.get('frame_number', 0))
        
        frame_tensors = []
        for frame in sorted_frames:
            frame_data = frame.get('data', '')
            if not frame_data:
                continue
            
            # Decode base64 to image bytes
            image_bytes = base64.b64decode(frame_data)
            
            # Create PIL Image from bytes
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Convert PIL to tensor [H, W, C] format
            width, height = pil_image.size
            pixel_data = list(pil_image.getdata())
            
            # Convert to torch tensor and reshape
            frame_tensor = torch.tensor(pixel_data, dtype=torch.float32)
            frame_tensor = frame_tensor.view(height, width, 3) / 255.0  # Normalize to 0-1
            
            frame_tensors.append(frame_tensor)
        
        if not frame_tensors:
            raise RuntimeError("No valid frames found to create tensor batch")
        
        # Stack all frames into a batch [B, H, W, C] format
        batched_tensor = torch.stack(frame_tensors, dim=0)
        
        return batched_tensor

    def get_instance_config(self, instance_name: str) -> dict:
        """Get the configuration for the specified instance"""
        return instance_config(instance_name)

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

    def extract_frames_from_zip(self, zip_data: bytes) -> List[dict]:
        """Extract frame images from ZIP archive and convert to frame data"""
        try:
            frames = []
            
            # Create a temporary directory for extraction
            temp_dir = tempfile.mkdtemp(prefix='r2_frames_')
            
            try:
                # Extract ZIP archive
                with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_file:
                    zip_file.extractall(temp_dir)
                
                # Get all image files and sort them
                image_files = []
                for filename in os.listdir(temp_dir):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        image_files.append(filename)
                
                # Sort by frame number if possible, otherwise alphabetically
                try:
                    # Try to sort by numeric frame number in filename
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
                    
                    frames.append({
                        "data": base64_data,
                        "format": "PNG",
                        "frame_number": i
                    })
                
            finally:
                # Clean up temporary directory
                try:
                    for filename in os.listdir(temp_dir):
                        os.remove(os.path.join(temp_dir, filename))
                    os.rmdir(temp_dir)
                except:
                    pass
            
            return frames
            
        except Exception as e:
            raise RuntimeError(f"Error extracting frames from ZIP: {str(e)}")

    def generate(self, instance_name: str, positive_prompt: str, negative_prompt: str,
                width: int, height: int, length: int, fps: int, steps: int,
                cfg: float, seed: int, batch_size: int) -> Tuple[torch.Tensor, str]:
        
        # Generate random seed if -1
        if seed == -1:
            seed = random.randint(0, 2147483647)
        
        # Get instance configuration
        config = self.get_instance_config(instance_name)
        endpoint = config["endpoint"]
        headers = config["headers"]
        
        # Prepare payload structure for standalone_text_to_video workflow
        payload = {
            "input": {
                "workflow_name": "standalone_text_to_video",
                "workflow_params": {
                    "positive_prompt": positive_prompt,
                    "negative_prompt": negative_prompt,
                    "width": width,
                    "height": height,
                    "length": length,
                    "fps": fps,
                    "steps": steps,
                    "cfg": cfg,
                    "seed": seed,
                    "batch_size": batch_size,
                    "model_path": "/runpod-volume/shared_models"
                }
            }
        }
        
        try:
            # Send request to RunPod endpoint
            result = send_request(endpoint, headers, payload)
            
            # Parse the response to extract frame data (R2 ZIP archive schema)
            if ("output" in result and 
                "result" in result["output"] and 
                "frames" in result["output"]["result"]):
                
                frames_info = result["output"]["result"]["frames"]
                frame_count = result["output"]["result"].get("frame_count", 0)
                
                # Check if this is the R2 ZIP archive format
                if isinstance(frames_info, dict) and "bucket" in frames_info and "key" in frames_info:
                    print(f"Downloading ZIP archive with {frame_count} frames from R2...")
                    
                    # Download ZIP archive from R2
                    bucket = frames_info["bucket"]
                    key = frames_info["key"]
                    zip_data = self.download_r2_archive(bucket, key)
                    
                    print(f"Extracting {frame_count} frames from ZIP archive...")
                    
                    # Extract frames from ZIP
                    frames = self.extract_frames_from_zip(zip_data)
                    
                    print(f"Converting {len(frames)} frames to tensor batch...")
                    
                    # Convert frames to tensor batch
                    frame_tensors = self.frames_to_tensor_batch(frames)
                    
                    # Create metadata string with generation parameters
                    metadata = {
                        "frame_count": frame_count,
                        "tensor_shape": list(frame_tensors.shape),
                        "parameters": {
                            "prompt": positive_prompt,
                            "negative_prompt": negative_prompt,
                            "width": width,
                            "height": height,
                            "length": length,
                            "fps": fps,
                            "num_inference_steps": steps,
                            "guidance_scale": cfg,
                            "seed": seed,
                            "batch_size": batch_size
                        },
                        "execution_time": result.get("executionTime", 0),
                        "delay_time": result.get("delayTime", 0),
                        "status": result["output"]["result"].get("status", "unknown"),
                        "r2_info": {
                            "bucket": bucket,
                            "key": key,
                            "filename": frames_info.get("filename", "unknown"),
                            "size_bytes": frames_info.get("size_bytes", 0)
                        },
                        "video_info": {
                            "width": width,
                            "height": height,
                            "length": length,
                            "batch_size": batch_size
                        }
                    }
                    
                    return (frame_tensors, json.dumps(metadata, indent=2))
                
                # Fallback: direct frames format (list of frame objects)
                elif isinstance(frames_info, list) and len(frames_info) > 0:
                    print(f"Processing {len(frames_info)} frames from direct format...")
                    
                    # Convert frames to tensor batch
                    frame_tensors = self.frames_to_tensor_batch(frames_info)
                    
                    # Create metadata string with generation parameters
                    metadata = {
                        "frame_count": len(frames_info),
                        "tensor_shape": list(frame_tensors.shape),
                        "parameters": {
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "width": width,
                            "height": height,
                            "length": length,
                            "fps": fps,
                            "num_inference_steps": steps,
                            "guidance_scale": cfg,
                            "seed": seed,
                            "batch_size": batch_size
                        },
                        "execution_time": result.get("executionTime", 0),
                        "delay_time": result.get("delayTime", 0),
                        "status": result["output"]["result"].get("status", "unknown"),
                        "video_info": {
                            "width": width,
                            "height": height,
                            "length": length,
                            "batch_size": batch_size
                        }
                    }
                    
                    return (frame_tensors, json.dumps(metadata, indent=2))
                else:
                    raise RuntimeError("Invalid frames format in response")
                
            else:
                raise RuntimeError(f"Unexpected response structure: {json.dumps(result, indent=2)}")

        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")


__all__ = ["TextToVideo"]