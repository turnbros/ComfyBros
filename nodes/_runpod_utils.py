import requests
import time
import threading
from urllib3.exceptions import ProtocolError

# Global job tracking
_active_jobs = {}
_job_lock = threading.Lock()

def register_job(job_id: str, endpoint: str, headers: dict):
    """Register an active job for cancellation tracking"""
    with _job_lock:
        _active_jobs[job_id] = {
            "endpoint": endpoint,
            "headers": headers,
            "cancelled": False
        }

def unregister_job(job_id: str):
    """Remove job from active tracking"""
    with _job_lock:
        _active_jobs.pop(job_id, None)

def cancel_job(job_id: str) -> bool:
    """Cancel a RunPod job"""
    with _job_lock:
        if job_id not in _active_jobs:
            return False
        
        job_info = _active_jobs[job_id]
        if job_info["cancelled"]:
            return True
        
        try:
            endpoint = job_info["endpoint"]
            headers = job_info["headers"]
            
            # Send cancellation request to RunPod
            response = requests.post(f"{endpoint}/cancel/{job_id}", headers=headers)
            
            if response.status_code == 200:
                job_info["cancelled"] = True
                print(f"Successfully cancelled RunPod job {job_id}")
                return True
            else:
                print(f"Failed to cancel RunPod job {job_id}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error cancelling RunPod job {job_id}: {str(e)}")
            return False

def is_job_cancelled(job_id: str) -> bool:
    """Check if a job has been cancelled"""
    with _job_lock:
        return _active_jobs.get(job_id, {}).get("cancelled", False)

def send_request(endpoint: str, headers: dict, payload: dict, job_callback=None) -> dict:
    """Send a POST request to the RunPod endpoint and return the JSON response."""
    # Make the request to RunPod with extended timeout for video generation
    response = requests.post(f"{endpoint}/run", headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()

    job_id = result["id"]
    
    # Register job for cancellation tracking
    register_job(job_id, endpoint, headers)
    
    # Notify caller of job ID if callback provided
    if job_callback:
        job_callback(job_id)

    print(f"Job {job_id} Status: {result['status']}")

    max_retries = 5
    retries = 0

    try:
        # 900-second timeout for video generation
        timeout = 900
        start_time = time.time()
        while (result["status"] == "IN_QUEUE"
               or result["status"] == "IN_PROGRESS"):

            # Check if job was cancelled
            if is_job_cancelled(job_id):
                print(f"Job {job_id} was cancelled")
                raise RuntimeError("Job was cancelled")

            if time.time() - start_time > timeout:
                unregister_job(job_id)
                raise RuntimeError("Request timed out waiting for video generation")

            print("Video generation in queue, waiting 4 seconds...")
            time.sleep(4)

            try:
                response = requests.get(f"{endpoint}/status/{job_id}", headers=headers)
                response.raise_for_status()
                result = response.json()
            except Exception as e:
                if retries < max_retries:
                    retries += 1
                    print(f"Request error: {e}")
                    print(f"Exception encountered. Retrying {retries}/{max_retries}...")
                    time.sleep(4)
                    continue
                else:
                    unregister_job(job_id)
                    raise RuntimeError("Max retries reached after ProtocolError") from e

            # Reset retries after a successful request
            retries = 0

    except Exception as e:
        # Don't unregister yet in case we can recover
        if "cancelled" not in str(e):
            time.sleep(4)

            # Try one final time to get the job status
            try:
                response = requests.get(f"{endpoint}/status/{job_id}", headers=headers)
                response.raise_for_status()
                result = response.json()
                print(f"Job {job_id} Status: {result['status']}")
                print(result)
                if result["status"] != "COMPLETED":
                    unregister_job(job_id)
                    raise RuntimeError("Request failed after ProtocolError")
            except:
                unregister_job(job_id)
                raise
        else:
            unregister_job(job_id)
            raise

    # Job completed successfully
    unregister_job(job_id)
    print(f"Job {job_id} Status: {result['status']}")
    print(f"Media generation job {job_id} complete!")
    return result