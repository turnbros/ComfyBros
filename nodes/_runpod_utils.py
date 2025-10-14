import requests
import time
from urllib3.exceptions import ProtocolError

def send_request(endpoint: str, headers: dict, payload: dict) -> dict:
    """Send a POST request to the RunPod endpoint and return the JSON response."""
    # Make the request to RunPod with extended timeout for video generation
    response = requests.post(f"{endpoint}/run", headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()

    job_id = result["id"]

    print(f"Job {job_id} Status: {result['status']}")

    max_retries = 5
    retries = 0

    try:
        # 900-second timeout for video generation
        timeout = 900
        start_time = time.time()
        while (result["status"] == "IN_QUEUE"
               or result["status"] == "IN_PROGRESS"):

            if time.time() - start_time > timeout:
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
                    raise RuntimeError("Max retries reached after ProtocolError") from e

            # Reset retries after a successful request
            retries = 0

    except Exception:
        time.sleep(4)

        # Try one final time to get the job status
        response = requests.get(f"{endpoint}/status/{job_id}", headers=headers)
        response.raise_for_status()
        result = response.json()
        print(f"Job {job_id} Status: {result['status']}")
        print(result)
        if result["status"] != "COMPLETED":
            raise RuntimeError("Request failed after ProtocolError")

    print(f"Job {job_id} Status: {result['status']}")
    print(f"Media generation job {job_id} complete!")
    return result