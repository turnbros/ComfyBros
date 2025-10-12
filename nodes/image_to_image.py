"""ComfyBros image-to-image generation node."""

from __future__ import annotations

import base64
import io
import json
import os
import random
from typing import Tuple, Optional, Any

import requests
import torch
from PIL import Image

try:  # pragma: no cover - ComfyUI provides this at runtime
    import folder_paths  # type: ignore
except Exception:  # pragma: no cover - fall back gracefully if unavailable
    folder_paths = None  # type: ignore

from ._instance_utils import instance_config, instance_names


class ImageToImage:
    """Generate an image variation using the ``image_to_image`` workflow."""

    @classmethod
    def INPUT_TYPES(cls):
        names = instance_names()
        return {
            "required": {
                "instance_name": (
                    names,
                    {"default": names[0] if names else "No instances configured"},
                ),
                "input_image": ("IMAGE",),
                "positive_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "a creative variation of the original image",
                    },
                ),
                "negative_prompt": (
                    "STRING",
                    {"multiline": True, "default": ""},
                ),
                "checkpoint": (
                    "STRING",
                    {"default": "checkpoint_name.safetensors"},
                ),
                "steps": (
                    "INT",
                    {"default": 20, "min": 1, "max": 150},
                ),
                "cfg": (
                    "FLOAT",
                    {"default": 7.0, "min": 0.1, "max": 30.0, "step": 0.1},
                ),
                "seed": (
                    "INT",
                    {"default": -1, "min": -1, "max": 2**31 - 1},
                ),
                "sampler_name": ("STRING", {"default": "euler"}),
                "scheduler": ("STRING", {"default": "normal"}),
                "denoise": (
                    "FLOAT",
                    {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
            },
            "optional": {
                "input_image_string": (
                    "STRING",
                    {"multiline": True, "default": ""},
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "metadata")
    FUNCTION = "generate"
    CATEGORY = "ComfyBros/Image Generation"

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    def tensor_to_base64(self, tensor: torch.Tensor) -> str:
        """Convert a ComfyUI tensor to a base64-encoded PNG string."""

        if tensor.dim() == 4:
            tensor = tensor[0]

        tensor = tensor.clamp(0.0, 1.0)
        numpy_image = (tensor.cpu().numpy() * 255).astype("uint8")

        pil_image = Image.fromarray(numpy_image)
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def base64_to_tensor(self, base64_string: str) -> torch.Tensor:
        """Convert a base64 encoded image string to a ComfyUI tensor."""

        image_bytes = base64.b64decode(base64_string)
        pil_image = Image.open(io.BytesIO(image_bytes))

        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        width, height = pil_image.size
        pixel_data = list(pil_image.getdata())

        image_tensor = torch.tensor(pixel_data, dtype=torch.float32)
        image_tensor = image_tensor.view(height, width, 3) / 255.0
        return image_tensor.unsqueeze(0)

    def is_base64(self, value: str) -> bool:
        try:
            base64.b64decode(value, validate=True)
            return True
        except Exception:
            return False

    def file_to_base64(self, file_path: str) -> str:
        if not file_path:
            raise RuntimeError("Input image file path is required")

        potential_paths = []
        if folder_paths and getattr(folder_paths, "get_input_directory", None):
            try:
                potential_paths.append(
                    os.path.join(folder_paths.get_input_directory(), file_path)
                )
            except Exception:
                potential_paths.append(file_path)
        else:
            potential_paths.append(file_path)

        if file_path not in potential_paths:
            potential_paths.append(file_path)

        for path in potential_paths:
            if path and os.path.exists(path):
                with open(path, "rb") as file:
                    return base64.b64encode(file.read()).decode("utf-8")

        raise RuntimeError(f"Image file not found: {file_path}")

    def process_input_image(
        self,
        input_image: torch.Tensor | None,
        input_image_string: Optional[str] = None,
    ) -> str:
        if isinstance(input_image, torch.Tensor):
            return self.tensor_to_base64(input_image)

        if input_image_string and input_image_string.strip():
            candidate = input_image_string.strip()
        else:
            candidate = None

        if candidate:
            if candidate.startswith("data:image/"):
                return candidate.split(",", 1)[1]
            if self.is_base64(candidate):
                return candidate
            return self.file_to_base64(candidate)

        raise RuntimeError("Input image is required for image-to-image generation")

    # ------------------------------------------------------------------
    # Main execution
    # ------------------------------------------------------------------
    def generate(
        self,
        instance_name: str,
        input_image: torch.Tensor,
        positive_prompt: str,
        negative_prompt: str,
        checkpoint: str,
        steps: int,
        cfg: float,
        seed: int,
        sampler_name: str,
        scheduler: str,
        denoise: float,
        input_image_string: Optional[str] = None,
    ) -> Tuple[torch.Tensor, str]:

        processed_image = self.process_input_image(input_image, input_image_string)

        if seed == -1:
            seed = random.randint(1, 2**64)

        try:
            denoise_value = max(0.0, min(1.0, float(denoise)))
        except Exception as exc:  # pragma: no cover - defensive conversion
            raise RuntimeError(f"Invalid denoise value: {exc}") from exc

        config = instance_config(instance_name)
        endpoint = config["endpoint"]
        headers = config["headers"]

        payload = {
            "input": {
                "workflow_name": "image_to_image",
                "workflow_params": {
                    "input_image": processed_image,
                    "positive_prompt": positive_prompt,
                    "negative_prompt": negative_prompt,
                    "checkpoint": checkpoint,
                    "steps": steps,
                    "cfg": cfg,
                    "seed": seed,
                    "sampler_name": sampler_name,
                    "scheduler": scheduler,
                    "denoise": denoise_value,
                },
            }
        }

        try:
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            print(result)
            print(f"Full response from RunPod:{dir(result)}")

            """
              "delayTime": 707,
  "id": "sync-853a97da-3d7f-4659-96b4-4443a603c21b-u1",
  "status": "IN_PROGRESS",
  "workerId": "ljaic2fgukybe3"
}
            """

        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"Request error: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"JSON decode error: {exc}") from exc

        data_block: Any
        if isinstance(result, dict) and "output" in result:
            output = result.get("output", {})
            data_block = output.get("result", output)
        else:
            data_block = result

        images_field = data_block.get("images") if isinstance(data_block, dict) else None
        if not images_field:
            raise RuntimeError(f"Unexpected response structure: {json.dumps(result, indent=2)}")

        images_b64 = []
        for image_entry in images_field:
            if isinstance(image_entry, dict) and "data" in image_entry:
                images_b64.append(image_entry["data"])
            elif isinstance(image_entry, str):
                images_b64.append(image_entry)

        if not images_b64:
            raise RuntimeError("No image data found in response")

        image_tensor = self.base64_to_tensor(images_b64[0])

        metadata = {
            "status": data_block.get("status", "success"),
            "images": images_b64,
            "parameters": {
                "positive_prompt": positive_prompt,
                "negative_prompt": negative_prompt,
                "checkpoint": checkpoint,
                "steps": steps,
                "cfg": cfg,
                "seed": seed,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "denoise": denoise_value,
            },
        }

        return image_tensor, json.dumps(metadata, indent=2)


__all__ = ["ImageToImage"]

