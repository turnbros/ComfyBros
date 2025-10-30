import torch
import aiohttp
import asyncio
import io
import os
import json
import numpy as np
import threading
import mimetypes
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
                "media_metadata": ("STRING", {
                    "default": "{}",
                    "multiline": True,
                    "forceInput": True
                }),
                "api_endpoint": ("STRING", {
                    "default": "http://localhost:8000",
                    "multiline": False
                }),
            },
            "optional": {
                "user_id": ("STRING", {
                    "default": "",
                    "placeholder": "user123"
                }),
                "filename": ("STRING", {"default": ""}),
                "tags": ("STRING", {
                    "default": "",
                    "placeholder": "portrait, anime, highres"
                }),
                "additional_metadata": ("STRING", {
                    "default": "{}",
                    "multiline": True
                }),
                "verify_ssl": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("IMAGE,VIDEO", "STRING", "INT", "STRING")
    RETURN_NAMES = ("media", "upload_status", "file_id", "file_url")
    FUNCTION = "upload"
    CATEGORY = "ComfyBros/Storage"
    OUTPUT_NODE = True

    def upload(self, media, media_metadata: str, api_endpoint: str,
               user_id: str = "", filename: str = "", tags: str = "", 
               additional_metadata: str = "{}", verify_ssl: bool = True) -> Tuple[Any, str, int, str]:
        """
        Upload media to Gallerina media gallery API

        Returns:
            Tuple of (media passthrough, upload_status JSON, file_id, file_url)
        """

        # Run async upload in sync context
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, we need to use a different approach
                import concurrent.futures
                import threading
                
                # Create a new thread with its own event loop
                result_container = {}
                exception_container = {}
                
                def run_upload():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result = new_loop.run_until_complete(
                            self._upload_async(
                                media, media_metadata, api_endpoint, user_id,
                                filename, tags, additional_metadata, verify_ssl
                            )
                        )
                        result_container['result'] = result
                    except Exception as e:
                        exception_container['exception'] = e
                    finally:
                        new_loop.close()
                
                # Run in separate thread
                thread = threading.Thread(target=run_upload)
                thread.start()
                thread.join()
                
                if 'exception' in exception_container:
                    raise exception_container['exception']
                
                return result_container['result']
            else:
                # No loop running, we can use run_until_complete
                return loop.run_until_complete(
                    self._upload_async(
                        media, media_metadata, api_endpoint, user_id,
                        filename, tags, additional_metadata, verify_ssl
                    )
                )
        except RuntimeError:
            # No event loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self._upload_async(
                        media, media_metadata, api_endpoint, user_id,
                        filename, tags, additional_metadata, verify_ssl
                    )
                )
            finally:
                loop.close()

    async def _upload_async(self, media, media_metadata, api_endpoint,
                           user_id, filename, tags, additional_metadata, verify_ssl):
        """Async upload implementation"""

        try:
            # Validate inputs
            if not api_endpoint or not api_endpoint.strip():
                raise ValueError("API endpoint is required")

            # Parse media metadata
            parsed_metadata = self._parse_media_metadata(media_metadata)
            
            # Detect media type and convert to bytes
            media_type = self._detect_media_type(media)

            if media_type == "image":
                file_bytes = self._tensor_to_image_bytes(media)
                if not filename:
                    # Use batch info if available
                    batch_size = parsed_metadata.get('batch_size', 1)
                    if batch_size > 1:
                        filename = f"comfyui_batch_{batch_size}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    else:
                        filename = f"comfyui_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                
            else:  # video
                if not isinstance(media, str) or not os.path.exists(media):
                    raise ValueError("Video input must be a valid file path")
                
                with open(media, 'rb') as f:
                    file_bytes = f.read()
                
                if not filename:
                    # Use frame count info if available
                    frame_count = parsed_metadata.get('frame_count', 0)
                    original_filename = os.path.basename(media)
                    base_name, ext = os.path.splitext(original_filename)
                    
                    if frame_count > 0:
                        filename = f"comfyui_video_{frame_count}frames_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext or '.mp4'}"
                    else:
                        filename = f"comfyui_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext or '.mp4'}"
            
            # Detect content type using the new helper method
            content_type = self._detect_content_type(filename, media_type)

            # Parse tags
            tag_list = [t.strip() for t in tags.split(',') if t.strip()] if tags else []

            # Build complete metadata
            try:
                additional_meta = json.loads(additional_metadata) if additional_metadata else {}
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid additional metadata JSON, ignoring: {e}")
                additional_meta = {}
            
            # Combine all metadata
            complete_metadata = {
                'uploaded_at': datetime.now().isoformat(),
                'source': 'ComfyUI',
                'node': 'MediaUpload',
                **parsed_metadata,
                **additional_meta
            }

            # Upload
            result = await self._upload_to_api(
                file_bytes, filename, content_type, api_endpoint,
                user_id, tag_list, complete_metadata, verify_ssl
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
        elif isinstance(media, str):
            if os.path.exists(media):
                # Additional validation for video files
                extension = media.lower().split('.')[-1] if '.' in media else ''
                video_extensions = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'm4v', '3gp', 'ogv'}
                
                if extension in video_extensions:
                    return "video"
                else:
                    print(f"Warning: File '{media}' has extension '{extension}' which may not be a supported video format")
                    return "video"  # Still try to process as video
            else:
                raise ValueError(f"Video file path does not exist: {media}")
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

    def _detect_content_type(self, filename: str, media_type: str) -> str:
        """Detect proper content type for the file"""
        # First try to guess from filename using mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        
        if mime_type:
            print(f"Detected MIME type: {mime_type} for file: {filename}")
            return mime_type
        
        # Fallback based on file extension and media type
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if media_type == "image":
            # Image format fallbacks
            image_types = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'gif': 'image/gif',
                'webp': 'image/webp',
                'bmp': 'image/bmp',
                'tiff': 'image/tiff',
                'tif': 'image/tiff'
            }
            content_type = image_types.get(extension, 'image/png')  # Default to PNG for images
            if extension and extension not in image_types:
                print(f"Warning: Unknown image extension '{extension}', defaulting to image/png")
            return content_type
        
        else:  # video
            # Video format fallbacks
            video_types = {
                'mp4': 'video/mp4',
                'avi': 'video/x-msvideo',
                'mov': 'video/quicktime',
                'mkv': 'video/x-matroska',
                'webm': 'video/webm',
                'flv': 'video/x-flv',
                'wmv': 'video/x-ms-wmv',
                'm4v': 'video/x-m4v',
                '3gp': 'video/3gpp',
                'ogv': 'video/ogg'
            }
            content_type = video_types.get(extension, 'video/mp4')  # Default to MP4 for videos
            if extension and extension not in video_types:
                print(f"Warning: Unknown video extension '{extension}', defaulting to video/mp4")
            return content_type

    def _parse_media_metadata(self, media_metadata: str) -> dict:
        """Parse media metadata JSON from generation nodes"""
        try:
            if not media_metadata or media_metadata.strip() == "":
                return {}
            
            metadata = json.loads(media_metadata)
            
            # Extract key information for Gallerina
            parsed = {}
            
            # Common fields
            if 'parameters' in metadata:
                params = metadata['parameters']
                parsed.update({
                    'generation_parameters': params,
                    'positive_prompt': params.get('positive_prompt', ''),
                    'negative_prompt': params.get('negative_prompt', ''),
                    'seed': params.get('seed'),
                    'steps': params.get('steps'),
                    'cfg': params.get('cfg'),
                    'sampler_name': params.get('sampler_name', ''),
                    'scheduler': params.get('scheduler', ''),
                })
                
                # Add model/checkpoint info
                if 'checkpoint' in params:
                    parsed['model'] = params['checkpoint']
                
            # Image-specific fields
            if 'batch_size' in metadata:
                parsed.update({
                    'batch_size': metadata['batch_size'],
                    'image_count': metadata.get('image_count'),
                    'format': metadata.get('format', 'PNG')
                })
                
            # Video-specific fields  
            if 'frame_count' in metadata:
                parsed.update({
                    'frame_count': metadata['frame_count'],
                    'video_info': metadata.get('video_info', {})
                })
                
            # Tensor shape info
            if 'tensor_shape' in metadata:
                shape = metadata['tensor_shape']
                parsed['tensor_shape'] = shape
                if len(shape) >= 3:
                    parsed.update({
                        'height': shape[-3],
                        'width': shape[-2],
                        'channels': shape[-1]
                    })
                    
            # Performance info
            parsed.update({
                'execution_time': metadata.get('execution_time'),
                'delay_time': metadata.get('delay_time'),
                'status': metadata.get('status')
            })
            
            # R2 info if available
            if 'r2_info' in metadata:
                parsed['r2_info'] = metadata['r2_info']
                
            # Original metadata for reference
            parsed['original_metadata'] = metadata
            
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid media metadata JSON: {e}")
            return {}
        except Exception as e:
            print(f"Warning: Error parsing media metadata: {e}")
            return {}

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
                             api_endpoint: str, user_id: str, tags: list, metadata: dict, verify_ssl: bool) -> dict:
        """Upload file to Gallerina API without authentication"""
        
        # Clean endpoint URL
        api_endpoint = api_endpoint.rstrip('/')
        url = f"{api_endpoint}/files/upload"

        # Create form data
        data = aiohttp.FormData()
        data.add_field('file', file_bytes, filename=filename, content_type=content_type)
        
        # Add user_id if provided
        if user_id and user_id.strip():
            data.add_field('user_id', user_id.strip())
        
        # Add metadata as JSON field if provided
        if metadata:
            data.add_field('metadata', json.dumps(metadata), content_type='application/json')
            
        # Add tags as comma-separated string if provided
        if tags:
            data.add_field('tags', ','.join(tags))

        ssl_context = None if verify_ssl else False

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, ssl=ssl_context) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Handle different possible response formats
                        if 'file' in result:
                            file_id = result['file']['id']
                        elif 'id' in result:
                            file_id = result['id']
                        else:
                            # Fallback - generate a fake ID for compatibility
                            file_id = int(datetime.now().timestamp())

                        return {
                            'file_id': file_id,
                            'file_url': f"{api_endpoint}/files/{file_id}/download",
                            'message': result.get('message', 'Upload successful')
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Upload failed ({response.status}): {error_text}")
                        
        except aiohttp.ClientConnectorError:
            raise Exception("Cannot connect to API. Check endpoint URL and network.")
        except asyncio.TimeoutError:
            raise Exception("Upload timed out. File may be too large or network is slow.")
        except aiohttp.ClientSSLError as e:
            raise Exception(f"SSL verification failed. Set verify_ssl=False for self-signed certs. Error: {e}")

