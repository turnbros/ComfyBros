from typing import Tuple


class EndpointConfiguration:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "endpoint": ("STRING", {"default": "https://api.example.com"}),
                "auth_token": ("STRING", {"default": ""}),
            }
        }
    
    RETURN_TYPES = ("ENDPOINT_CONFIG",)
    FUNCTION = "create_endpoint_config"
    CATEGORY = "ComfyBros/Configuration"
    
    def create_endpoint_config(self, endpoint: str, auth_token: str) -> Tuple[dict]:
        config = {
            "endpoint": endpoint,
            "auth_token": auth_token,
            "headers": {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {auth_token}' if auth_token else None
            }
        }
        # Remove Authorization header if no token provided
        if not auth_token:
            del config["headers"]["Authorization"]
        
        return (config,)