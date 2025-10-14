import torch
import io
import base64
import json
from typing import Tuple, List
from PIL import Image, ImageDraw, ImageFont
import numpy as np


class ImageBatchCombiner:
    """Combine multiple image batches into a single batch for creating animations or sequences"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "batch1": ("IMAGE",),
            },
            "optional": {
                "batch2": ("IMAGE",),
                "batch3": ("IMAGE",),
                "batch4": ("IMAGE",),
                "batch5": ("IMAGE",),
                "batch6": ("IMAGE",),
                "batch7": ("IMAGE",),
                "batch8": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("combined_batch", "info")
    FUNCTION = "combine_batches"
    CATEGORY = "ComfyBros/Image Utils"
    
    def combine_batches(self, batch1: torch.Tensor, batch2: torch.Tensor = None, 
                       batch3: torch.Tensor = None, batch4: torch.Tensor = None,
                       batch5: torch.Tensor = None, batch6: torch.Tensor = None,
                       batch7: torch.Tensor = None, batch8: torch.Tensor = None) -> Tuple[torch.Tensor, str]:
        """
        Combine multiple image batches into a single batch.
        All batches must have the same height, width, and channels.
        """
        batches = [batch1]
        batch_names = ["batch1"]
        
        # Collect all non-None batches
        for i, batch in enumerate([batch2, batch3, batch4, batch5, batch6, batch7, batch8], 2):
            if batch is not None:
                batches.append(batch)
                batch_names.append(f"batch{i}")
        
        if len(batches) == 1:
            total_frames = batch1.shape[0]
            info = {
                "total_batches": 1,
                "total_frames": total_frames,
                "batch_info": [{"name": "batch1", "frames": total_frames}],
                "dimensions": f"{batch1.shape[2]}x{batch1.shape[1]}",
                "channels": batch1.shape[3]
            }
            return (batch1, json.dumps(info, indent=2))
        
        # Validate dimensions
        reference_shape = batch1.shape[1:]  # [height, width, channels]
        for i, batch in enumerate(batches[1:], 1):
            if batch.shape[1:] != reference_shape:
                raise ValueError(f"Batch {i+1} dimensions {batch.shape[1:]} don't match reference {reference_shape}")
        
        # Combine all batches
        combined_batch = torch.cat(batches, dim=0)
        
        # Create info about the combination
        batch_info = []
        total_frames = 0
        for i, (batch, name) in enumerate(zip(batches, batch_names)):
            frames = batch.shape[0]
            batch_info.append({
                "name": name,
                "frames": frames,
                "start_frame": total_frames,
                "end_frame": total_frames + frames - 1
            })
            total_frames += frames
        
        info = {
            "total_batches": len(batches),
            "total_frames": total_frames,
            "batch_info": batch_info,
            "dimensions": f"{reference_shape[1]}x{reference_shape[0]}",
            "channels": reference_shape[2]
        }
        
        return (combined_batch, json.dumps(info, indent=2))


class ImageBatchToGIF:
    """Convert an image batch to an animated GIF"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "frame_duration": ("INT", {
                    "default": 100,
                    "min": 10,
                    "max": 5000,
                    "step": 10,
                    "tooltip": "Duration of each frame in milliseconds"
                }),
                "filename": ("STRING", {
                    "default": "animation",
                    "tooltip": "Filename for the GIF (without extension)"
                }),
            },
            "optional": {
                "loop": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Whether the GIF should loop"
                }),
                "add_frame_numbers": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Add frame numbers to each frame"
                }),
                "optimize": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Optimize GIF file size"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("gif_data",)
    FUNCTION = "create_gif"
    CATEGORY = "ComfyBros/Image Utils"
    
    def tensor_to_pil(self, tensor: torch.Tensor) -> Image.Image:
        """Convert a single tensor frame to PIL Image"""
        # tensor should be [height, width, channels]
        if len(tensor.shape) == 4:
            tensor = tensor[0]  # Take first image if batch
        
        # Convert to numpy and scale to 0-255
        image_np = (tensor.cpu().numpy() * 255).astype('uint8')
        
        # Convert to PIL Image
        if image_np.shape[2] == 3:
            return Image.fromarray(image_np, 'RGB')
        elif image_np.shape[2] == 4:
            return Image.fromarray(image_np, 'RGBA')
        else:
            raise ValueError(f"Unsupported number of channels: {image_np.shape[2]}")
    
    def add_frame_number_to_image(self, pil_image: Image.Image, frame_num: int) -> Image.Image:
        """Add frame number text to the image"""
        # Create a copy to avoid modifying the original
        img_with_text = pil_image.copy()
        draw = ImageDraw.Draw(img_with_text)
        
        # Try to use a default font, fall back to basic if not available
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        # Position text in top-left corner
        text = f"Frame {frame_num}"
        text_color = "white"
        outline_color = "black"
        
        # Draw text with outline for better visibility
        x, y = 10, 10
        if font:
            # Draw outline
            for adj in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,-1), (1,-1), (-1,1)]:
                draw.text((x+adj[0], y+adj[1]), text, font=font, fill=outline_color)
            # Draw main text
            draw.text((x, y), text, font=font, fill=text_color)
        else:
            # Fallback without font
            draw.text((x, y), text, fill=text_color)
        
        return img_with_text
    
    def create_gif(self, images: torch.Tensor, frame_duration: int, filename: str,
                   loop: bool = True, add_frame_numbers: bool = False, 
                   optimize: bool = True) -> Tuple[str]:
        """
        Create an animated GIF from a batch of images.
        Returns base64 encoded GIF data.
        """
        if len(images.shape) != 4:
            raise ValueError(f"Expected 4D tensor [batch, height, width, channels], got shape {images.shape}")
        
        batch_size = images.shape[0]
        if batch_size < 1:
            raise ValueError("Need at least 1 frame to create a GIF")
        
        # Convert all frames to PIL Images
        pil_frames = []
        for i in range(batch_size):
            frame_tensor = images[i]
            pil_frame = self.tensor_to_pil(frame_tensor)
            
            # Add frame number if requested
            if add_frame_numbers:
                pil_frame = self.add_frame_number_to_image(pil_frame, i + 1)
            
            pil_frames.append(pil_frame)
        
        # Create GIF in memory
        gif_buffer = io.BytesIO()
        
        # Save as animated GIF
        pil_frames[0].save(
            gif_buffer,
            format='GIF',
            save_all=True,
            append_images=pil_frames[1:],
            duration=frame_duration,
            loop=0 if loop else 1,
            optimize=optimize
        )
        
        # Get GIF data as base64
        gif_buffer.seek(0)
        gif_data = base64.b64encode(gif_buffer.getvalue()).decode('utf-8')
        
        # Create metadata
        metadata = {
            "filename": f"{filename}.gif",
            "format": "GIF",
            "frames": batch_size,
            "frame_duration_ms": frame_duration,
            "dimensions": f"{images.shape[2]}x{images.shape[1]}",
            "channels": images.shape[3],
            "looping": loop,
            "optimized": optimize,
            "frame_numbers_added": add_frame_numbers,
            "data": gif_data
        }
        
        return (json.dumps(metadata, indent=2),)


class ImageBatchSplitter:
    """Split an image batch into smaller batches or extract specific frames"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "split_mode": (["chunk_size", "num_chunks", "frame_range"], {
                    "default": "chunk_size"
                }),
            },
            "optional": {
                "chunk_size": ("INT", {
                    "default": 8,
                    "min": 1,
                    "max": 1000,
                    "tooltip": "Number of frames per chunk (for chunk_size mode)"
                }),
                "num_chunks": ("INT", {
                    "default": 2,
                    "min": 1,
                    "max": 100,
                    "tooltip": "Number of chunks to create (for num_chunks mode)"
                }),
                "start_frame": ("INT", {
                    "default": 0,
                    "min": 0,
                    "tooltip": "Start frame index (for frame_range mode)"
                }),
                "end_frame": ("INT", {
                    "default": -1,
                    "tooltip": "End frame index, -1 for last frame (for frame_range mode)"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("split_batch", "info")
    FUNCTION = "split_batch"
    CATEGORY = "ComfyBros/Image Utils"
    
    def split_batch(self, images: torch.Tensor, split_mode: str, chunk_size: int = 8,
                   num_chunks: int = 2, start_frame: int = 0, 
                   end_frame: int = -1) -> Tuple[torch.Tensor, str]:
        """
        Split an image batch based on the specified mode.
        Returns the first split/chunk and info about all splits.
        """
        batch_size = images.shape[0]
        
        if split_mode == "frame_range":
            if end_frame == -1:
                end_frame = batch_size - 1
            
            if start_frame < 0 or start_frame >= batch_size:
                raise ValueError(f"start_frame {start_frame} out of range [0, {batch_size-1}]")
            if end_frame < start_frame or end_frame >= batch_size:
                raise ValueError(f"end_frame {end_frame} out of range [{start_frame}, {batch_size-1}]")
            
            result_batch = images[start_frame:end_frame+1]
            
            info = {
                "mode": "frame_range",
                "original_frames": batch_size,
                "extracted_frames": end_frame - start_frame + 1,
                "start_frame": start_frame,
                "end_frame": end_frame,
                "dimensions": f"{images.shape[2]}x{images.shape[1]}",
                "channels": images.shape[3]
            }
            
        elif split_mode == "chunk_size":
            if chunk_size <= 0 or chunk_size > batch_size:
                raise ValueError(f"chunk_size {chunk_size} must be between 1 and {batch_size}")
            
            # Return first chunk
            result_batch = images[:chunk_size]
            
            # Calculate all chunks info
            num_full_chunks = batch_size // chunk_size
            remainder = batch_size % chunk_size
            total_chunks = num_full_chunks + (1 if remainder > 0 else 0)
            
            chunks_info = []
            for i in range(total_chunks):
                start_idx = i * chunk_size
                end_idx = min(start_idx + chunk_size, batch_size)
                chunks_info.append({
                    "chunk": i + 1,
                    "start_frame": start_idx,
                    "end_frame": end_idx - 1,
                    "frames": end_idx - start_idx
                })
            
            info = {
                "mode": "chunk_size",
                "original_frames": batch_size,
                "chunk_size": chunk_size,
                "total_chunks": total_chunks,
                "returned_chunk": 1,
                "returned_frames": result_batch.shape[0],
                "chunks": chunks_info,
                "dimensions": f"{images.shape[2]}x{images.shape[1]}",
                "channels": images.shape[3]
            }
            
        elif split_mode == "num_chunks":
            if num_chunks <= 0 or num_chunks > batch_size:
                raise ValueError(f"num_chunks {num_chunks} must be between 1 and {batch_size}")
            
            # Calculate chunk sizes (distribute frames as evenly as possible)
            base_chunk_size = batch_size // num_chunks
            extra_frames = batch_size % num_chunks
            
            # Return first chunk
            first_chunk_size = base_chunk_size + (1 if extra_frames > 0 else 0)
            result_batch = images[:first_chunk_size]
            
            # Calculate all chunks info
            chunks_info = []
            current_idx = 0
            for i in range(num_chunks):
                chunk_size = base_chunk_size + (1 if i < extra_frames else 0)
                chunks_info.append({
                    "chunk": i + 1,
                    "start_frame": current_idx,
                    "end_frame": current_idx + chunk_size - 1,
                    "frames": chunk_size
                })
                current_idx += chunk_size
            
            info = {
                "mode": "num_chunks",
                "original_frames": batch_size,
                "requested_chunks": num_chunks,
                "returned_chunk": 1,
                "returned_frames": result_batch.shape[0],
                "chunks": chunks_info,
                "dimensions": f"{images.shape[2]}x{images.shape[1]}",
                "channels": images.shape[3]
            }
        
        else:
            raise ValueError(f"Unknown split_mode: {split_mode}")
        
        return (result_batch, json.dumps(info, indent=2))