from .ollama_nodes import *
from .sdxl_lora_prompter import *
from .generate_image import *
from .lora_discovery import *
from .runpod_config import *
from .runpod_nodes import *

NODE_CLASS_MAPPINGS = {
    "ComfyBros_OllamaConnection": OllamaConnection,
    "ComfyBros_OllamaConfiguration": OllamaConfiguration,
    "ComfyBros_OllamaConverse": OllamaConverse,
    "ComfyBros_SDXLLORAPrompter": SDXLLORAPrompter,
    "ComfyBros_GenerateImage": GenerateImage,
    "ComfyBros_LoraDiscovery": LoraDiscovery,
    # RunPod Configuration Nodes
    "ComfyBros_RunPodConfiguration": RunPodConfiguration,
    "ComfyBros_RunPodInstanceManager": RunPodInstanceManager,
    "ComfyBros_RunPodInstanceSelector": RunPodInstanceSelector,
    # RunPod Execution Nodes
    "ComfyBros_RunPodGenericExecutor": RunPodGenericExecutor,
    "ComfyBros_RunPodImageGenerator": RunPodImageGenerator,
    "ComfyBros_RunPodTextProcessor": RunPodTextProcessor,
    "ComfyBros_RunPodHealthChecker": RunPodHealthChecker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ComfyBros_OllamaConnection": "Ollama Connection",
    "ComfyBros_OllamaConfiguration": "Ollama Configuration",
    "ComfyBros_OllamaConverse": "Ollama Converse",
    "ComfyBros_SDXLLORAPrompter": "SDXL LORA Prompter",
    "ComfyBros_GenerateImage": "Generate Image",
    "ComfyBros_LoraDiscovery": "LORA Discovery",
    # RunPod Configuration Nodes
    "ComfyBros_RunPodConfiguration": "RunPod Configuration",
    "ComfyBros_RunPodInstanceManager": "RunPod Instance Manager",
    "ComfyBros_RunPodInstanceSelector": "RunPod Instance Selector",
    # RunPod Execution Nodes
    "ComfyBros_RunPodGenericExecutor": "RunPod Generic Executor",
    "ComfyBros_RunPodImageGenerator": "RunPod Image Generator",
    "ComfyBros_RunPodTextProcessor": "RunPod Text Processor",
    "ComfyBros_RunPodHealthChecker": "RunPod Health Checker",
}