import base64
import io
from typing import List
import torch
from PIL import Image


def images_to_tensor_batch(images: List[dict]) -> torch.Tensor:
    """Convert list of base64 frame data to batched tensor for ComfyUI"""

    image_tensors = []
    for image in images:
        image_data = image.get('data', '')
        if not image_data:
            continue

        # Decode base64 to image bytes
        image_bytes = base64.b64decode(image_data)

        # Create PIL Image from bytes
        pil_image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if needed
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Convert PIL to tensor [H, W, C] format
        width, height = pil_image.size
        pixel_data = list(pil_image.getdata())

        # Convert to torch tensor and reshape
        image_tensor = torch.tensor(pixel_data, dtype=torch.float32)
        image_tensor = image_tensor.view(height, width, 3) / 255.0  # Normalize to 0-1

        image_tensors.append(image_tensor)

    if not image_tensors:
        raise RuntimeError("No valid frames found to create tensor batch")

    # Stack all frames into a batch [B, H, W, C] format
    batched_tensor = torch.stack(image_tensors, dim=len(image_tensors[0].shape))
    return batched_tensor

    return batched_tensor