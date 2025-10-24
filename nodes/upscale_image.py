import json
import base64
import io
import torch
import os
import random
import tempfile
import time
import zipfile
import boto3
from botocore.exceptions import ClientError
from PIL import Image
from typing import Tuple
import folder_paths
from ._instance_utils import instance_config, instance_names
from ._runpod_utils import send_request


class WAN22UpscaleImage:
    """Upscale images using RunPod serverless instances with upscale workflow"""
    
    @classmethod
    def INPUT_TYPES(cls):
        names = instance_names()
        return {
            "required": {
                "instance_name": (names, {"default": names[0] if names else "No instances configured"}),
                "input_image": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("upscaled_image", "metadata")
    FUNCTION = "upscale"
    CATEGORY = "ComfyBros/Image Enhancement"
    
    def tensor_to_base64(self, tensor: torch.Tensor) -> str:
        """Convert torch tensor to base64 string"""
        if tensor.dim() == 4:
            tensor = tensor[0]
        
        if tensor.max() <= 1.0:
            tensor = (tensor * 255).clamp(0, 255).to(torch.uint8)
        else:
            tensor = tensor.clamp(0, 255).to(torch.uint8)
        
        numpy_image = tensor.cpu().numpy()
        pil_image = Image.fromarray(numpy_image, mode='RGB')
        
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def base64_to_tensor(self, base64_string: str) -> torch.Tensor:
        """Convert base64 string to tensor for ComfyUI"""
        image_bytes = base64.b64decode(base64_string)
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        width, height = pil_image.size
        pixel_data = list(pil_image.getdata())
        
        image_tensor = torch.tensor(pixel_data, dtype=torch.float32)
        image_tensor = image_tensor.view(height, width, 3) / 255.0
        
        return image_tensor.unsqueeze(0)

    def process_input_image(self, input_image, input_image_string: str = None) -> str:
        """Process input image - either torch tensor, base64 data, or file path"""
        if isinstance(input_image, torch.Tensor):
            return self.tensor_to_base64(input_image)
        
        if input_image_string and input_image_string.strip():
            input_image = input_image_string
        
        if isinstance(input_image, str):
            if not input_image.strip():
                raise RuntimeError("Input image is required")
            
            if input_image.startswith('data:image/'):
                return input_image.split(',', 1)[1]
            elif self.is_base64(input_image):
                return input_image
            else:
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
            full_path = os.path.join(folder_paths.get_input_directory(), file_path)
            if not os.path.exists(full_path):
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
            print(f"Reading R2 config from: {settings_file}")

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
            
            account_id = r2_config["account_id"]
            endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
            
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=r2_config["access_key_id"],
                aws_secret_access_key=r2_config["secret_access_key"],
                region_name='auto'
            )
            
            print(f"Downloading {key} from R2 bucket {bucket}...")
            
            response = s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()
            
            print(f"Downloaded {len(content)} bytes from R2")
            
            return content
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise RuntimeError(f"R2 client error ({error_code}): {error_message}")
        except Exception as e:
            raise RuntimeError(f"Error downloading archive from R2: {str(e)}")

    def extract_image_from_zip(self, zip_data: bytes) -> str:
        """Extract upscaled image from ZIP archive and return as base64"""
        try:
            temp_dir = tempfile.mkdtemp(prefix='r2_upscale_')
            
            try:
                with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_file:
                    zip_file.extractall(temp_dir)
                
                image_files = []
                for filename in os.listdir(temp_dir):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        image_files.append(filename)
                
                if not image_files:
                    raise RuntimeError("No image files found in ZIP archive")
                
                image_files.sort()
                main_image = image_files[0]
                file_path = os.path.join(temp_dir, main_image)
                
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                
                return base64_data
                
            finally:
                try:
                    for filename in os.listdir(temp_dir):
                        os.remove(os.path.join(temp_dir, filename))
                    os.rmdir(temp_dir)
                except:
                    pass
            
        except Exception as e:
            raise RuntimeError(f"Error extracting image from ZIP: {str(e)}")

    def upscale(self, instance_name: str, input_image) -> Tuple[torch.Tensor, str]:

        processed_image = self.process_input_image(input_image, None)
        
        config = self.get_instance_config(instance_name)
        endpoint = config["endpoint"]
        headers = config["headers"]
        
        payload = {
            "input": {
                "input_image": processed_image
            }
        }
        
        try:
            result = send_request(endpoint, headers, payload)
            
            if ("output" in result and 
                "image" in result["output"]):
                
                image_info = result["output"]["image"]
                
                if isinstance(image_info, dict) and "bucket" in image_info and "key" in image_info:
                    print(f"Downloading upscaled image from R2...")
                    
                    bucket = image_info["bucket"]
                    key = image_info["key"]
                    zip_data = self.download_r2_archive(bucket, key)
                    
                    print(f"Extracting upscaled image from ZIP archive...")
                    
                    upscaled_image_b64 = self.extract_image_from_zip(zip_data)
                    
                    print(f"Converting upscaled image to tensor...")
                    
                    upscaled_tensor = self.base64_to_tensor(upscaled_image_b64)
                    
                    metadata = {
                        "tensor_shape": list(upscaled_tensor.shape),
                        "parameters": result["output"].get("parameters", {}),
                        "execution_time": result.get("executionTime", 0),
                        "delay_time": result.get("delayTime", 0),
                        "status": result["output"].get("status", "unknown"),
                        "r2_info": {
                            "bucket": bucket,
                            "key": key,
                            "filename": image_info.get("filename", "unknown"),
                            "size_bytes": image_info.get("size_bytes", 0)
                        }
                    }
                    
                    return (upscaled_tensor, json.dumps(metadata, indent=2))

        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")