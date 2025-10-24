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


class WAN22GenerateVideo:
    """Generate videos using RunPod serverless instances with image_to_video workflow"""
    
    @classmethod
    def INPUT_TYPES(cls):
        names = instance_names()
        return {
            "required": {
                "instance_name": (names, {"default": names[0] if names else "No instances configured"}),
                "input_image": ("IMAGE",),
                "positive_prompt": ("STRING", {"multiline": True, "default": "something positive"}),
                "negative_prompt": ("STRING", {"multiline": True, "default": "blurry, low quality, distorted"}),
                "width": ("INT", {"default": 512, "min": 64, "max": 2048, "step": 64}),
                "height": ("INT", {"default": 512, "min": 64, "max": 2048, "step": 64}),
                "length": ("INT", {"default": 80, "min": 8, "max": 800, "step": 8}),
                "fps": ("INT", {"default": 24, "min": 1, "max": 60}),
                "steps": ("INT", {"default": 4, "min": 1, "max": 150}),
                "cfg": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 30.0, "step": 0.1}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "sampler_name": ([
                    "euler", "euler_ancestral", "heun", "heunpp2", "dpm_2", "dpm_2_ancestral",
                    "lms", "dpm_fast", "dpm_adaptive", "dpmpp_2s_ancestral", "dpmpp_sde", "dpmpp_sde_gpu",
                    "dpmpp_2m", "dpmpp_2m_sde", "dpmpp_2m_sde_gpu", "dpmpp_3m_sde", "dpmpp_3m_sde_gpu", 
                    "ddpm", "lcm", "ddim", "uni_pc", "uni_pc_bh2"
                ], {"default": "euler"}),
                "scheduler": ([
                    "normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform", "beta"
                ], {"default": "simple"}),
                "shift": ("INT", {"default": 0, "min": -100, "max": 100}),
                "low_model_checkpoint": ("STRING", {"default": "wan22_smooth_mix_i2v_low.safetensors"}),
                "high_model_checkpoint": ("STRING", {"default": "wan22_smooth_mix_i2v_high.safetensors"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("frames", "metadata")
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

    def frames_to_video_file(self, frames: List[dict], fps: int, output_filename: str = None) -> str:
        """Convert list of base64 frame data to video file using ffmpeg"""
        try:
            # Get output directory
            try:
                output_dir = folder_paths.get_output_directory()
            except:
                output_dir = tempfile.gettempdir()
            
            # Create temporary directory for frames
            temp_dir = tempfile.mkdtemp(prefix='video_frames_', dir=output_dir)
            
            # Sort frames by frame_number to ensure correct sequence
            sorted_frames = sorted(frames, key=lambda x: x.get('frame_number', 0))
            
            # Save each frame as an image file
            frame_paths = []
            for i, frame in enumerate(sorted_frames):
                frame_data = frame.get('data', '')
                if not frame_data:
                    continue
                    
                # Decode base64 to image
                image_bytes = base64.b64decode(frame_data)
                frame_path = os.path.join(temp_dir, f"frame_{i:06d}.png")
                
                with open(frame_path, 'wb') as f:
                    f.write(image_bytes)
                frame_paths.append(frame_path)
            
            if not frame_paths:
                raise RuntimeError("No valid frames found to create video")
            
            # Create output video file
            if output_filename:
                video_filename = output_filename
            else:
                video_filename = f"generated_video_{int(time.time())}.mp4"
            
            video_path = os.path.join(output_dir, video_filename)
            
            # Use ffmpeg to create video from frames
            # Pattern: frame_%06d.png means frame_000000.png, frame_000001.png, etc.
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-framerate', str(fps),
                '-i', os.path.join(temp_dir, 'frame_%06d.png'),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-crf', '18',  # High quality
                video_path
            ]
            
            # Run ffmpeg
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
            
            # Clean up temporary frame files
            for frame_path in frame_paths:
                try:
                    os.remove(frame_path)
                except:
                    pass
            
            try:
                os.rmdir(temp_dir)
            except:
                pass
            
            return video_path
            
        except Exception as e:
            # Clean up on error
            try:
                for frame_path in frame_paths:
                    os.remove(frame_path)
                os.rmdir(temp_dir)
            except:
                pass
            raise RuntimeError(f"Error creating video from frames: {str(e)}")

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

    def generate(self, instance_name: str, input_image, positive_prompt: str, 
                negative_prompt: str, width: int, height: int, length: int, fps: int,
                steps: int, cfg: float, seed: int, sampler_name: str, 
                scheduler: str, shift: int, low_model_checkpoint: str, high_model_checkpoint: str ) -> Tuple[torch.Tensor, str]:

        # Process the input image
        processed_image = self.process_input_image(input_image, None)
        
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
                "scheduler": scheduler,
                "shift": shift,
                "low_model_checkpoint": low_model_checkpoint,
                "high_model_checkpoint": high_model_checkpoint
            }
        }
        
        try:
            # Poll the endpoint again to check status
            result = send_request(endpoint, headers, payload)
            
            # Parse the response to extract frame data (new R2 ZIP archive schema)
            if ("output" in result and 
                "result" in result["output"] and 
                "frames" in result["output"]["result"]):
                
                frames_info = result["output"]["result"]["frames"]
                frame_count = result["output"]["result"].get("frame_count", 0)
                
                # Check if this is the new R2 ZIP archive format
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
                        "parameters": result["output"]["result"].get("parameters", {}),
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
                            "fps": fps
                        }
                    }
                    
                    return (frame_tensors, json.dumps(metadata, indent=2))
                
                # Fallback: old direct frames format (list of frame objects)
                elif isinstance(frames_info, list) and len(frames_info) > 0:
                    print(f"Processing {len(frames_info)} frames from direct format...")
                    
                    # Convert frames to tensor batch
                    frame_tensors = self.frames_to_tensor_batch(frames_info)
                    
                    # Create metadata string with generation parameters
                    metadata = {
                        "frame_count": len(frames_info),
                        "tensor_shape": list(frame_tensors.shape),
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
                    
                    return (frame_tensors, json.dumps(metadata, indent=2))
                else:
                    raise RuntimeError("Invalid frames format in response")
                
            # Fallback: try old schema for backwards compatibility
            elif ("output" in result and 
                  "result" in result["output"] and 
                  "videos" in result["output"]["result"] and 
                  len(result["output"]["result"]["videos"]) > 0):
                
                # Get the first video (old schema)
                first_video = result["output"]["result"]["videos"][0]
                
                if "data" in first_video:
                    # Old schema fallback - return error since we can't convert a single video file to frames
                    raise RuntimeError("Old video format detected but this node now outputs individual frames. Please use the updated workflow that returns frames.")
                else:
                    raise RuntimeError("No video data found in response")
            else:
                raise RuntimeError(f"Unexpected response structure: {json.dumps(result, indent=2)}")

        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")