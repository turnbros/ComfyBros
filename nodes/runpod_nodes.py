"""
RunPod Serverless Nodes
Provides nodes that can execute tasks on RunPod serverless instances.
"""

import json
import base64
from typing import Tuple, Optional, Dict, Any, List
from ..runpod_client import runpod_manager, RunPodError
from ..settings import settings_manager


class RunPodGenericExecutor:
    """Generic node for executing arbitrary tasks on RunPod serverless instances"""
    
    @classmethod
    def INPUT_TYPES(cls):
        # Get available instances
        try:
            instances = runpod_manager.get_available_instances()
            instance_choices = ["DEFAULT"] + [instance.name for instance in instances]
        except:
            instance_choices = ["DEFAULT"]
        
        return {
            "required": {
                "input_data": ("STRING", {
                    "multiline": True,
                    "default": "{}"
                }),
                "instance": (instance_choices, {
                    "default": "DEFAULT"
                }),
                "synchronous": ("BOOLEAN", {
                    "default": True
                }),
            },
            "optional": {
                "webhook_url": ("STRING", {
                    "multiline": False,
                    "default": ""
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "BOOLEAN", "STRING")
    RETURN_NAMES = ("output", "job_id", "success", "status_message")
    FUNCTION = "execute"
    CATEGORY = "ComfyBros/RunPod"
    
    def execute(self, input_data: str, instance: str, synchronous: bool,
                webhook_url: str = "") -> Tuple[str, str, bool, str]:
        """Execute a generic task on RunPod"""
        try:
            # Parse input data
            try:
                parsed_input = json.loads(input_data)
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON input: {str(e)}"
                print(f"RunPodGenericExecutor: {error_msg}")
                return ("", "", False, error_msg)
            
            # Prepare webhook URL
            webhook = webhook_url.strip() if webhook_url.strip() else None
            
            # Execute on RunPod
            if instance == "DEFAULT":
                response = runpod_manager.execute_on_default_instance(
                    parsed_input, webhook, synchronous
                )
            else:
                response = runpod_manager.execute_on_instance(
                    instance, parsed_input, webhook, synchronous
                )
            
            if synchronous:
                if response.status == "COMPLETED":
                    output_str = json.dumps(response.output) if response.output else ""
                    status_msg = f"Job completed successfully in {response.execution_time:.2f}s"
                    print(f"RunPodGenericExecutor: {status_msg}")
                    return (output_str, response.id, True, status_msg)
                else:
                    error_msg = f"Job failed: {response.error or 'Unknown error'}"
                    print(f"RunPodGenericExecutor: {error_msg}")
                    return ("", response.id, False, error_msg)
            else:
                status_msg = f"Job queued with ID: {response.id}"
                print(f"RunPodGenericExecutor: {status_msg}")
                return ("", response.id, True, status_msg)
                
        except RunPodError as e:
            error_msg = f"RunPod error: {str(e)}"
            print(f"RunPodGenericExecutor: {error_msg}")
            return ("", "", False, error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"RunPodGenericExecutor: {error_msg}")
            return ("", "", False, error_msg)


class RunPodImageGenerator:
    """Node for generating images using RunPod serverless instances"""
    
    @classmethod
    def INPUT_TYPES(cls):
        # Get available instances
        try:
            instances = runpod_manager.get_available_instances()
            instance_choices = ["DEFAULT"] + [instance.name for instance in instances]
        except:
            instance_choices = ["DEFAULT"]
        
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "instance": (instance_choices, {
                    "default": "DEFAULT"
                }),
            },
            "optional": {
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "width": ("INT", {
                    "default": 512,
                    "min": 64,
                    "max": 2048,
                    "step": 64
                }),
                "height": ("INT", {
                    "default": 512,
                    "min": 64,
                    "max": 2048,
                    "step": 64
                }),
                "steps": ("INT", {
                    "default": 20,
                    "min": 1,
                    "max": 150
                }),
                "cfg_scale": ("FLOAT", {
                    "default": 7.0,
                    "min": 1.0,
                    "max": 20.0,
                    "step": 0.1
                }),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 2147483647
                }),
                "model": ("STRING", {
                    "default": ""
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "BOOLEAN", "STRING")
    RETURN_NAMES = ("image", "job_id", "success", "status_message")
    FUNCTION = "generate"
    CATEGORY = "ComfyBros/RunPod"
    
    def generate(self, prompt: str, instance: str, negative_prompt: str = "",
                width: int = 512, height: int = 512, steps: int = 20,
                cfg_scale: float = 7.0, seed: int = -1, model: str = "") -> Tuple[Any, str, bool, str]:
        """Generate an image using RunPod"""
        try:
            # Prepare input data for image generation
            input_data = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_inference_steps": steps,
                "guidance_scale": cfg_scale,
            }
            
            if seed != -1:
                input_data["seed"] = seed
            
            if model.strip():
                input_data["model"] = model.strip()
            
            # Execute on RunPod
            if instance == "DEFAULT":
                response = runpod_manager.execute_on_default_instance(input_data, sync=True)
            else:
                response = runpod_manager.execute_on_instance(instance, input_data, sync=True)
            
            if response.status == "COMPLETED":
                # Process the output - assuming it returns base64 encoded image or URL
                output = response.output
                
                if isinstance(output, dict):
                    # Try to extract image data
                    image_data = output.get("image") or output.get("images", [{}])[0].get("image")
                    image_url = output.get("image_url") or output.get("images", [{}])[0].get("url")
                    
                    if image_data:
                        # Handle base64 encoded image
                        try:
                            import torch
                            import numpy as np
                            from PIL import Image
                            import io
                            
                            # Decode base64 image
                            if image_data.startswith("data:image"):
                                # Remove data URL prefix
                                image_data = image_data.split(",", 1)[1]
                            
                            image_bytes = base64.b64decode(image_data)
                            pil_image = Image.open(io.BytesIO(image_bytes))
                            
                            # Convert to RGB if needed
                            if pil_image.mode != "RGB":
                                pil_image = pil_image.convert("RGB")
                            
                            # Convert to tensor format expected by ComfyUI
                            image_array = np.array(pil_image).astype(np.float32) / 255.0
                            image_tensor = torch.from_numpy(image_array).unsqueeze(0)
                            
                            status_msg = f"Image generated successfully in {response.execution_time:.2f}s"
                            print(f"RunPodImageGenerator: {status_msg}")
                            return (image_tensor, response.id, True, status_msg)
                            
                        except Exception as e:
                            error_msg = f"Error processing image data: {str(e)}"
                            print(f"RunPodImageGenerator: {error_msg}")
                            return (None, response.id, False, error_msg)
                    
                    elif image_url:
                        # Handle image URL
                        try:
                            import requests
                            import torch
                            import numpy as np
                            from PIL import Image
                            import io
                            
                            # Download image
                            img_response = requests.get(image_url, timeout=30)
                            img_response.raise_for_status()
                            
                            pil_image = Image.open(io.BytesIO(img_response.content))
                            
                            # Convert to RGB if needed
                            if pil_image.mode != "RGB":
                                pil_image = pil_image.convert("RGB")
                            
                            # Convert to tensor format
                            image_array = np.array(pil_image).astype(np.float32) / 255.0
                            image_tensor = torch.from_numpy(image_array).unsqueeze(0)
                            
                            status_msg = f"Image generated and downloaded successfully in {response.execution_time:.2f}s"
                            print(f"RunPodImageGenerator: {status_msg}")
                            return (image_tensor, response.id, True, status_msg)
                            
                        except Exception as e:
                            error_msg = f"Error downloading image: {str(e)}"
                            print(f"RunPodImageGenerator: {error_msg}")
                            return (None, response.id, False, error_msg)
                
                # If we get here, output format wasn't recognized
                error_msg = f"Unexpected output format: {type(output)}"
                print(f"RunPodImageGenerator: {error_msg}")
                return (None, response.id, False, error_msg)
            
            else:
                error_msg = f"Job failed: {response.error or 'Unknown error'}"
                print(f"RunPodImageGenerator: {error_msg}")
                return (None, response.id, False, error_msg)
                
        except RunPodError as e:
            error_msg = f"RunPod error: {str(e)}"
            print(f"RunPodImageGenerator: {error_msg}")
            return (None, "", False, error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"RunPodImageGenerator: {error_msg}")
            return (None, "", False, error_msg)


class RunPodTextProcessor:
    """Node for processing text using RunPod serverless instances"""
    
    @classmethod
    def INPUT_TYPES(cls):
        # Get available instances
        try:
            instances = runpod_manager.get_available_instances()
            instance_choices = ["DEFAULT"] + [instance.name for instance in instances]
        except:
            instance_choices = ["DEFAULT"]
        
        return {
            "required": {
                "input_text": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "task_type": (["completion", "summarization", "translation", "custom"], {
                    "default": "completion"
                }),
                "instance": (instance_choices, {
                    "default": "DEFAULT"
                }),
            },
            "optional": {
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "max_tokens": ("INT", {
                    "default": 150,
                    "min": 1,
                    "max": 4096
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1
                }),
                "custom_params": ("STRING", {
                    "multiline": True,
                    "default": "{}"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "BOOLEAN", "STRING")
    RETURN_NAMES = ("output_text", "job_id", "success", "status_message")
    FUNCTION = "process"
    CATEGORY = "ComfyBros/RunPod"
    
    def process(self, input_text: str, task_type: str, instance: str,
                system_prompt: str = "", max_tokens: int = 150,
                temperature: float = 0.7, custom_params: str = "{}") -> Tuple[str, str, bool, str]:
        """Process text using RunPod"""
        try:
            # Parse custom parameters
            try:
                custom_data = json.loads(custom_params)
            except json.JSONDecodeError:
                custom_data = {}
            
            # Prepare input data
            input_data = {
                "task_type": task_type,
                "input_text": input_text,
                "max_tokens": max_tokens,
                "temperature": temperature,
                **custom_data
            }
            
            if system_prompt.strip():
                input_data["system_prompt"] = system_prompt.strip()
            
            # Execute on RunPod
            if instance == "DEFAULT":
                response = runpod_manager.execute_on_default_instance(input_data, sync=True)
            else:
                response = runpod_manager.execute_on_instance(instance, input_data, sync=True)
            
            if response.status == "COMPLETED":
                # Extract text output
                output = response.output
                
                if isinstance(output, dict):
                    text_output = (
                        output.get("text") or 
                        output.get("generated_text") or 
                        output.get("output") or
                        str(output)
                    )
                elif isinstance(output, str):
                    text_output = output
                else:
                    text_output = str(output)
                
                status_msg = f"Text processed successfully in {response.execution_time:.2f}s"
                print(f"RunPodTextProcessor: {status_msg}")
                return (text_output, response.id, True, status_msg)
            
            else:
                error_msg = f"Job failed: {response.error or 'Unknown error'}"
                print(f"RunPodTextProcessor: {error_msg}")
                return ("", response.id, False, error_msg)
                
        except RunPodError as e:
            error_msg = f"RunPod error: {str(e)}"
            print(f"RunPodTextProcessor: {error_msg}")
            return ("", "", False, error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"RunPodTextProcessor: {error_msg}")
            return ("", "", False, error_msg)


class RunPodHealthChecker:
    """Node for checking RunPod instance health and connectivity"""
    
    @classmethod
    def INPUT_TYPES(cls):
        # Get available instances
        try:
            instances = runpod_manager.get_available_instances()
            instance_choices = ["ALL"] + [instance.name for instance in instances]
        except:
            instance_choices = ["ALL"]
        
        return {
            "required": {
                "instance": (instance_choices, {
                    "default": "ALL"
                }),
                "check_connectivity": ("BOOLEAN", {
                    "default": True
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "BOOLEAN", "STRING")
    RETURN_NAMES = ("health_report", "all_healthy", "status_message")
    FUNCTION = "check_health"
    CATEGORY = "ComfyBros/RunPod"
    
    def check_health(self, instance: str, check_connectivity: bool) -> Tuple[str, bool, str]:
        """Check health of RunPod instances"""
        try:
            health_results = {}
            all_healthy = True
            
            if instance == "ALL":
                # Check all instances
                if check_connectivity:
                    results = runpod_manager.validate_all_instances()
                    for instance_name, (healthy, message) in results.items():
                        health_results[instance_name] = {
                            "healthy": healthy,
                            "message": message,
                            "checked_connectivity": True
                        }
                        if not healthy:
                            all_healthy = False
                else:
                    # Just check configuration
                    instances = runpod_manager.get_available_instances()
                    for inst in instances:
                        health_results[inst.name] = {
                            "healthy": True,
                            "message": "Configuration OK (connectivity not checked)",
                            "checked_connectivity": False
                        }
            else:
                # Check specific instance
                if check_connectivity:
                    healthy, message = runpod_manager.validate_instance(instance)
                    health_results[instance] = {
                        "healthy": healthy,
                        "message": message,
                        "checked_connectivity": True
                    }
                    all_healthy = healthy
                else:
                    # Just check if instance exists
                    inst = settings_manager.get_runpod_instance(instance)
                    if inst and inst.enabled:
                        health_results[instance] = {
                            "healthy": True,
                            "message": "Configuration OK (connectivity not checked)",
                            "checked_connectivity": False
                        }
                    else:
                        health_results[instance] = {
                            "healthy": False,
                            "message": "Instance not found or disabled",
                            "checked_connectivity": False
                        }
                        all_healthy = False
            
            # Generate report
            report_lines = []
            for inst_name, result in health_results.items():
                status = "✓ HEALTHY" if result["healthy"] else "✗ UNHEALTHY"
                connectivity = " (with connectivity check)" if result["checked_connectivity"] else ""
                report_lines.append(f"{inst_name}: {status}{connectivity}")
                report_lines.append(f"  Message: {result['message']}")
                report_lines.append("")
            
            health_report = "\n".join(report_lines)
            status_message = f"Health check completed. {len([r for r in health_results.values() if r['healthy']])}/{len(health_results)} instances healthy"
            
            print(f"RunPodHealthChecker: {status_message}")
            return (health_report, all_healthy, status_message)
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            print(f"RunPodHealthChecker: {error_msg}")
            return ("", False, error_msg)