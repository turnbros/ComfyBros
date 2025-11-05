import time
import requests
import json
from typing import Tuple
from ._instance_utils import instance_config, instance_names


class ModuleManagement:
    """API Node - Manage models and modules using RunPod serverless instances via API calls"""
    
    @classmethod
    def INPUT_TYPES(cls):
        names = instance_names()
        return {
            "required": {
                "instance_name": (names, {"default": names[0] if names else "No instances configured"}),
                "management_action": (["list", "get"], {"default": "list"}),
            },
            "optional": {
                "model_kind": ("STRING", {"default": None}),
                "model_name": ("STRING", {"default": None}),
                "model_path": ("STRING", {"default": None}),
                "model_provider": ("STRING", {"default": None}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result_json",)
    FUNCTION = "api_call"
    CATEGORY = "ComfyBros/API Nodes/Model Management"
    API_NODE = True
    DESCRIPTION = "Manage models and modules using RunPod serverless instances via API calls. Supports listing and getting model information with optional filtering."
    
    def send_request(self, endpoint: str, headers: dict, payload: dict) -> dict:
        """Send a POST request to the RunPod endpoint and return the JSON response."""
        response = requests.post(f"{endpoint}/run", headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        job_id = result["id"]
        timeout = 900
        start_time = time.time()
        
        while (result["status"] == "IN_QUEUE" or result["status"] == "IN_PROGRESS"):
            if time.time() - start_time > timeout:
                raise RuntimeError("Request timed out waiting for module management response")

            print("Module management in queue, waiting 2 seconds...")
            time.sleep(2)

            response = requests.post(f"{endpoint}/status/{job_id}", headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
        
        return result

    def api_call(self, instance_name: str, management_action: str, 
                 model_kind: str = "", model_name: str = "", 
                 model_path: str = "", model_provider: str = "") -> Tuple[str]:

        config = instance_config(instance_name)
        endpoint = config["endpoint"]
        headers = config["headers"]
        
        # Build workflow params, only including non-empty optional parameters
        workflow_params = {
            "management_action": management_action
        }
        
        if model_kind:
            workflow_params["model_kind"] = model_kind
        if model_name:
            workflow_params["model_name"] = model_name
        if model_path:
            workflow_params["model_path"] = model_path
        if model_provider:
            workflow_params["model_provider"] = model_provider
        
        payload = {
            "input": {
                "workflow_name": "module_management",
                "workflow_params": workflow_params
            }
        }
        
        try:
            result = self.send_request(endpoint, headers, payload)

            if "output" in result:
                # Format the output with metadata
                response_data = {
                    "status": "success",
                    "management_action": management_action,
                    "workflow_params": workflow_params,
                    "execution_time": result.get("executionTime", 0),
                    "delay_time": result.get("delayTime", 0),
                    "output": result["output"]
                }
                
                return (json.dumps(response_data, indent=2),)
            else:
                raise RuntimeError(f"Unexpected response structure: {json.dumps(result, indent=2)}")
            
        except requests.exceptions.RequestException as e:
            error_response = {
                "status": "error",
                "error_type": "request_error",
                "message": str(e),
                "management_action": management_action,
                "workflow_params": workflow_params
            }
            return (json.dumps(error_response, indent=2),)
        except json.JSONDecodeError as e:
            error_response = {
                "status": "error",
                "error_type": "json_decode_error", 
                "message": str(e),
                "management_action": management_action,
                "workflow_params": workflow_params
            }
            return (json.dumps(error_response, indent=2),)
        except Exception as e:
            error_response = {
                "status": "error",
                "error_type": "unexpected_error",
                "message": str(e),
                "management_action": management_action,
                "workflow_params": workflow_params
            }
            return (json.dumps(error_response, indent=2),)