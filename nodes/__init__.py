from .ollama_nodes import *
from .sdxl_lora_prompter import *

NODE_CLASS_MAPPINGS = {
    "ComfyBros_OllamaConnection": OllamaConnection,
    "ComfyBros_OllamaConfiguration": OllamaConfiguration,
    "ComfyBros_OllamaConverse": OllamaConverse,
    "ComfyBros_SDXLLORAPrompter": SDXLLORAPrompter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ComfyBros_OllamaConnection": "Ollama Connection",
    "ComfyBros_OllamaConfiguration": "Ollama Configuration",
    "ComfyBros_OllamaConverse": "Ollama Converse",
    "ComfyBros_SDXLLORAPrompter": "SDXL LORA Prompter",
}