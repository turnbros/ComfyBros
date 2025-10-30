import torch
import aiohttp
import asyncio
import io
import os
import json
import numpy as np
from PIL import Image
from datetime import datetime
from typing import Tuple, Dict, Any, Optional, Union


class MediaUpload:
    """Upload generated images/videos to Gallerina media gallery API"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "media": ("IMAGE,VIDEO",),  # Accepts both IMAGE and VIDEO
                "api_endpoint": ("STRING", {
                    "default": "https://localhost:8443",
                    "multiline": False
                }),
                "auth_token": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            },
            "optional": {
                "filename": ("STRING", {"default": ""}),
                "tags": ("STRING", {
                    "default": "",
                    "placeholder": "portrait, anime, highres"
                }),
                "metadata_json": ("STRING", {
                    "default": "{}",
                    "multiline": True
                }),
                "include_workflow_data": ("BOOLEAN", {"default": True}),
                "verify_ssl": ("BOOLEAN", {"default": True}),

                # Workflow parameters (optional passthrough)
                "positive_prompt": ("STRING", {"default": "", "forceInput": True}),
                "negative_prompt": ("STRING", {"default": "", "forceInput": True}),
                "model_name": ("STRING", {"default": "", "forceInput": True}),
                "seed": ("INT", {"default": -1, "forceInput": True}),
                "steps": ("INT", {"default": -1, "forceInput": True}),
                "cfg": ("FLOAT", {"default": -1.0, "forceInput": True}),
                "sampler": ("STRING", {"default": "", "forceInput": True}),
                "scheduler": ("STRING", {"default": "", "forceInput": True}),
                "width": ("INT", {"default": -1, "forceInput": True}),
                "height": ("INT", {"default": -1, "forceInput": True}),
                "denoise": ("FLOAT", {"default": -1.0, "forceInput": True}),
            }
        }

    RETURN_TYPES = ("IMAGE,VIDEO", "STRING", "INT", "STRING")
    RETURN_NAMES = ("media", "upload_status", "file_id", "file_url")
    FUNCTION = "upload"
    CATEGORY = "ComfyBros/Storage"
    OUTPUT_NODE = True

    def upload(self, media, api_endpoint: str, auth_token: str,
               filename: str = "", tags: str = "", metadata_json: str = "{}",
               include_workflow_data: bool = True, verify_ssl: bool = True,
               **workflow_params) -> Tuple[Any, str, int, str]:
        """
        Upload media to Gallerina media gallery API

        Returns:
            Tuple of (media passthrough, upload_status JSON, file_id, file_url)
        """

        # Run async upload in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                self._upload_async(
                    media, api_endpoint, auth_token, filename,
                    tags, metadata_json, include_workflow_data,
                    verify_ssl, **workflow_params
                )
            )
            return result
        finally:
            loop.close()

    async def _upload_async(self, media, api_endpoint, auth_token,
                           filename, tags, metadata_json, include_workflow_data,
                           verify_ssl, **workflow_params):
        """Async upload implementation"""

        try:
            # Validate inputs
            if not api_endpoint or not api_endpoint.strip():
                raise ValueError("API endpoint is required")
            if not auth_token or not auth_token.strip():
                raise ValueError("Authentication token is required")

            # Detect media type and convert to bytes
            media_type = self._detect_media_type(media)

            if media_type == "image":
                file_bytes = self._tensor_to_image_bytes(media)
                if not filename:
                    filename = f"comfyui_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                content_type = "image/png"
            else:  # video
                with open(media, 'rb') as f:
                    file_bytes = f.read()
                if not filename:
                    filename = os.path.basename(media)
                content_type = "video/mp4"

            # Parse tags
            tag_list = [t.strip() for t in tags.split(',') if t.strip()] if tags else []

            # Build metadata
            try:
                metadata = json.loads(metadata_json) if metadata_json else {}
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid metadata JSON, using empty metadata: {e}")
                metadata = {}
                
            if include_workflow_data:
                workflow_meta = self._capture_workflow_metadata(**workflow_params)
                metadata.update(workflow_meta)

            # Upload
            result = await self._upload_to_api(
                file_bytes, filename, content_type, api_endpoint, auth_token,
                tag_list, metadata, verify_ssl
            )

            upload_status = json.dumps({
                'success': True,
                'file_id': result['file_id'],
                'message': result['message']
            })

            return (media, upload_status, result['file_id'], result['file_url'])

        except Exception as e:
            print(f"Upload error: {str(e)}")
            error_status = json.dumps({
                'success': False,
                'error': str(e)
            })
            return (media, error_status, -1, "")

    def _detect_media_type(self, media) -> str:
        """Detect if input is IMAGE or VIDEO"""
        if isinstance(media, torch.Tensor):
            return "image"
        elif isinstance(media, str) and os.path.exists(media):
            return "video"
        else:
            raise ValueError("Invalid media input. Must be IMAGE tensor or valid video file path.")

    def _tensor_to_image_bytes(self, image_tensor: torch.Tensor) -> bytes:
        """Convert ComfyUI image tensor to PNG bytes"""
        # Handle batch - take first image if batch
        if len(image_tensor.shape) == 4:
            image_tensor = image_tensor[0]

        # Convert from [H, W, C] to numpy array
        numpy_array = (image_tensor.cpu().numpy() * 255).astype(np.uint8)
        pil_image = Image.fromarray(numpy_array)

        # Convert to bytes
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG', optimize=True)
        return img_byte_arr.getvalue()

    def _capture_workflow_metadata(self, **kwargs) -> dict:
        """Capture workflow parameters"""
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'generator': 'ComfyUI',
            'node': 'MediaUpload',
            'node_version': '1.0.0'
        }

        # Add workflow parameters that have meaningful values
        for key, value in kwargs.items():
            if value and value != -1 and value != -1.0 and value != "":
                metadata[key] = value

        return metadata

    async def _upload_to_api(self, file_bytes: bytes, filename: str, content_type: str,
                             api_endpoint: str, auth_token: str, tags: list, 
                             metadata: dict, verify_ssl: bool) -> dict:
        """Upload file to Gallerina API"""
        
        # Clean endpoint URL
        api_endpoint = api_endpoint.rstrip('/')
        url = f"{api_endpoint}/files/upload"

        headers = {"Authorization": f"Bearer {auth_token}"}

        # Create form data
        data = aiohttp.FormData()
        data.add_field('file', file_bytes, filename=filename, content_type=content_type)

        ssl_context = None if verify_ssl else False

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data, ssl=ssl_context) as response:
                    if response.status == 200:
                        result = await response.json()
                        file_id = result['file']['id']

                        # Update metadata and tags if provided
                        if tags or metadata:
                            await self._update_metadata(
                                file_id, api_endpoint, auth_token,
                                tags, metadata, ssl_context
                            )

                        return {
                            'file_id': file_id,
                            'file_url': f"{api_endpoint}/files/{file_id}/download",
                            'message': result.get('message', 'Upload successful')
                        }
                    elif response.status == 401:
                        raise Exception("Authentication failed. Check your auth token.")
                    elif response.status == 403:
                        raise Exception("Access denied. User does not have upload permissions.")
                    else:
                        error_text = await response.text()
                        raise Exception(f"Upload failed ({response.status}): {error_text}")
                        
        except aiohttp.ClientConnectorError:
            raise Exception("Cannot connect to API. Check endpoint URL and network.")
        except asyncio.TimeoutError:
            raise Exception("Upload timed out. File may be too large or network is slow.")
        except aiohttp.ClientSSLError as e:
            raise Exception(f"SSL verification failed. Set verify_ssl=False for self-signed certs. Error: {e}")

    async def _update_metadata(self, file_id: int, api_endpoint: str, auth_token: str,
                              tags: list, metadata: dict, ssl_context):
        """Update file metadata and tags"""
        url = f"{api_endpoint}/files/{file_id}"
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

        payload = {}
        if tags:
            payload['tags'] = tags
        if metadata:
            payload['metadata'] = metadata

        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, headers=headers, json=payload, ssl=ssl_context) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Warning: Metadata update failed ({response.status}): {error_text}")
        except Exception as e:
            print(f"Warning: Failed to update metadata: {str(e)}")