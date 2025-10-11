from .ollama_nodes import *
from .sdxl_lora_prompter import *
from .generate_image import *
from .lora_discovery import *
from .endpoint_config import *
from .text_storage import *

NODE_CLASS_MAPPINGS = {
    "ComfyBros_OllamaConnection": OllamaConnection,
    "ComfyBros_OllamaConfiguration": OllamaConfiguration,
    "ComfyBros_OllamaConverse": OllamaConverse,
    "ComfyBros_SDXLLORAPrompter": SDXLLORAPrompter,
    "ComfyBros_GenerateImage": GenerateImage,
    "ComfyBros_LoraDiscovery": LoraDiscovery,
    "ComfyBros_EndpointConfiguration": EndpointConfiguration,
    "ComfyBros_TextStorage": TextStorage,
    "ComfyBros_TextTemplate": TextTemplate,
    "ComfyBros_TextConcatenate": TextConcatenate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ComfyBros_OllamaConnection": "Ollama Connection",
    "ComfyBros_OllamaConfiguration": "Ollama Configuration",
    "ComfyBros_OllamaConverse": "Ollama Converse",
    "ComfyBros_SDXLLORAPrompter": "SDXL LORA Prompter",
    "ComfyBros_GenerateImage": "Generate Image",
    "ComfyBros_LoraDiscovery": "LORA Discovery",
    "ComfyBros_EndpointConfiguration": "Endpoint Configuration",
    "ComfyBros_TextStorage": "Text Storage",
    "ComfyBros_TextTemplate": "Text Template",
    "ComfyBros_TextConcatenate": "Text Concatenate",
}