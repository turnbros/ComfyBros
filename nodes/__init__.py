from .text_nodes import *
from .image_nodes import *
from .ollama_nodes import *

NODE_CLASS_MAPPINGS = {
    "ComfyBros_TextProcessor": TextProcessor,
    "ComfyBros_TextCombiner": TextCombiner,
    "ComfyBros_ImageResize": ImageResize,
    "ComfyBros_ImageBlend": ImageBlend,
    "ComfyBros_OllamaConnection": OllamaConnection,
    "ComfyBros_OllamaConfiguration": OllamaConfiguration,
    "ComfyBros_OllamaConverse": OllamaConverse,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ComfyBros_TextProcessor": "Text Processor",
    "ComfyBros_TextCombiner": "Text Combiner", 
    "ComfyBros_ImageResize": "Image Resize",
    "ComfyBros_ImageBlend": "Image Blend",
    "ComfyBros_OllamaConnection": "Ollama Connection",
    "ComfyBros_OllamaConfiguration": "Ollama Configuration",
    "ComfyBros_OllamaConverse": "Ollama Converse",
}