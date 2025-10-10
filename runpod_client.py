"""
RunPod Serverless API Client
Handles communication with RunPod serverless endpoints.
"""

import json
import time
import requests
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from .settings import settings_manager, RunPodServerlessInstance


@dataclass
class RunPodRequest:
    """Represents a request to RunPod serverless"""
    input_data: Dict[str, Any]
    webhook_url: Optional[str] = None
    policy: Optional[Dict[str, Any]] = None


@dataclass
class RunPodResponse:
    """Represents a response from RunPod serverless"""
    id: str
    status: str
    output: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    raw_response: Optional[Dict[str, Any]] = None


class RunPodError(Exception):
    """Custom exception for RunPod API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RunPodClient:
    """Client for RunPod serverless API"""
    
    BASE_URL = "https://api.runpod.ai/v2"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize RunPod client"""
        self.api_key = api_key or self._get_api_key()
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })
    
    def _get_api_key(self) -> str:
        """Get API key from settings"""
        try:
            settings = settings_manager.load_settings()
            return settings.runpod.api_key
        except Exception as e:
            print(f"RunPodClient: Error getting API key from settings: {e}")
            return ""
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            
            # Log request details for debugging
            print(f"RunPodClient: {method} {url} -> {response.status_code}")
            
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', f"HTTP {response.status_code}")
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                
                raise RunPodError(
                    f"RunPod API error: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data if 'error_data' in locals() else None
                )
            
            return response
            
        except requests.exceptions.RequestException as e:
            raise RunPodError(f"Network error: {str(e)}")
    
    def run_sync(self, endpoint_id: str, request_data: RunPodRequest, timeout: int = 300) -> RunPodResponse:
        """Run a synchronous request to RunPod serverless endpoint"""
        if not self.api_key:
            raise RunPodError("No API key configured. Please set up RunPod configuration first.")
        
        # Start the job
        job_id = self.run_async(endpoint_id, request_data)
        
        # Poll for completion
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.get_status(endpoint_id, job_id)
                
                if response.status in ["COMPLETED", "FAILED"]:
                    response.execution_time = time.time() - start_time
                    return response
                elif response.status == "CANCELLED":
                    raise RunPodError(f"Job {job_id} was cancelled")
                
                # Wait before next poll
                time.sleep(2)
                
            except RunPodError as e:
                if "not found" in str(e).lower():
                    # Job might not be ready yet, continue polling
                    time.sleep(1)
                    continue
                raise
        
        # Timeout reached
        raise RunPodError(f"Job {job_id} timed out after {timeout} seconds")
    
    def run_async(self, endpoint_id: str, request_data: RunPodRequest) -> str:
        """Start an asynchronous request to RunPod serverless endpoint"""
        if not self.api_key:
            raise RunPodError("No API key configured. Please set up RunPod configuration first.")
        
        url = f"{self.BASE_URL}/{endpoint_id}/run"
        
        payload = {
            "input": request_data.input_data
        }
        
        if request_data.webhook_url:
            payload["webhook"] = request_data.webhook_url
        
        if request_data.policy:
            payload["policy"] = request_data.policy
        
        response = self._make_request("POST", url, json=payload)
        result = response.json()
        
        job_id = result.get("id")
        if not job_id:
            raise RunPodError(f"No job ID returned from RunPod: {result}")
        
        print(f"RunPodClient: Started job {job_id} on endpoint {endpoint_id}")
        return job_id
    
    def get_status(self, endpoint_id: str, job_id: str) -> RunPodResponse:
        """Get the status of a RunPod job"""
        url = f"{self.BASE_URL}/{endpoint_id}/status/{job_id}"
        
        response = self._make_request("GET", url)
        result = response.json()
        
        return RunPodResponse(
            id=job_id,
            status=result.get("status", "UNKNOWN"),
            output=result.get("output"),
            error=result.get("error"),
            raw_response=result
        )
    
    def cancel_job(self, endpoint_id: str, job_id: str) -> bool:
        """Cancel a RunPod job"""
        url = f"{self.BASE_URL}/{endpoint_id}/cancel/{job_id}"
        
        try:
            response = self._make_request("POST", url)
            result = response.json()
            return result.get("status") == "cancelled"
        except RunPodError:
            return False
    
    def get_health(self, endpoint_id: str) -> Dict[str, Any]:
        """Check the health of a RunPod endpoint"""
        url = f"{self.BASE_URL}/{endpoint_id}/health"
        
        response = self._make_request("GET", url)
        return response.json()
    
    def validate_connection(self) -> Tuple[bool, str]:
        """Validate the RunPod API connection and credentials"""
        if not self.api_key:
            return False, "No API key configured"
        
        try:
            # Try to make a simple request to validate credentials
            # Since we don't have a specific validation endpoint, we'll try to get user info
            url = f"{self.BASE_URL}/user"
            response = self._make_request("GET", url)
            
            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"Invalid response: {response.status_code}"
                
        except RunPodError as e:
            if e.status_code == 401:
                return False, "Invalid API key"
            else:
                return False, f"Connection failed: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"


class RunPodManager:
    """High-level manager for RunPod operations"""
    
    def __init__(self):
        self.client = RunPodClient()
    
    def execute_on_instance(self, instance_name: str, input_data: Dict[str, Any],
                          webhook_url: Optional[str] = None,
                          sync: bool = True) -> RunPodResponse:
        """Execute a job on a specific RunPod instance"""
        # Get instance configuration
        instance = settings_manager.get_runpod_instance(instance_name)
        if not instance:
            raise RunPodError(f"RunPod instance '{instance_name}' not found")
        
        if not instance.enabled:
            raise RunPodError(f"RunPod instance '{instance_name}' is disabled")
        
        # Check if RunPod is enabled globally
        settings = settings_manager.load_settings()
        if not settings.runpod.enabled:
            raise RunPodError("RunPod integration is disabled")
        
        # Create request
        request = RunPodRequest(
            input_data=input_data,
            webhook_url=webhook_url
        )
        
        print(f"RunPodManager: Executing job on instance '{instance_name}' (endpoint: {instance.endpoint_id})")
        
        if sync:
            return self.client.run_sync(instance.endpoint_id, request, instance.timeout_seconds)
        else:
            job_id = self.client.run_async(instance.endpoint_id, request)
            return RunPodResponse(id=job_id, status="IN_QUEUE")
    
    def execute_on_default_instance(self, input_data: Dict[str, Any],
                                   webhook_url: Optional[str] = None,
                                   sync: bool = True) -> RunPodResponse:
        """Execute a job on the default RunPod instance"""
        default_instance = settings_manager.get_default_runpod_instance()
        if not default_instance:
            raise RunPodError("No default RunPod instance configured")
        
        return self.execute_on_instance(default_instance.name, input_data, webhook_url, sync)
    
    def get_available_instances(self) -> List[RunPodServerlessInstance]:
        """Get list of available (enabled) RunPod instances"""
        settings = settings_manager.load_settings()
        return [instance for instance in settings.runpod.instances if instance.enabled]
    
    def validate_instance(self, instance_name: str) -> Tuple[bool, str]:
        """Validate a specific RunPod instance"""
        instance = settings_manager.get_runpod_instance(instance_name)
        if not instance:
            return False, f"Instance '{instance_name}' not found"
        
        if not instance.enabled:
            return False, f"Instance '{instance_name}' is disabled"
        
        try:
            health = self.client.get_health(instance.endpoint_id)
            if health.get("status") == "healthy":
                return True, "Instance is healthy"
            else:
                return False, f"Instance health check failed: {health}"
        except RunPodError as e:
            return False, f"Health check failed: {str(e)}"
    
    def validate_all_instances(self) -> Dict[str, Tuple[bool, str]]:
        """Validate all configured RunPod instances"""
        results = {}
        for instance in self.get_available_instances():
            results[instance.name] = self.validate_instance(instance.name)
        return results


# Global RunPod manager instance
runpod_manager = RunPodManager()