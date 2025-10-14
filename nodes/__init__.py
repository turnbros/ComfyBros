from .ollama_nodes import *
from .sdxl_lora_prompter import *
from .generate_image import *
from .generate_image_api import *
from .image_to_image import *
from .generate_video import *
from .lora_discovery import *
from .endpoint_config import *
from .text_storage import *
from .json_nodes import *
from .math_nodes import *
from .image_batch_utils import *

NODE_CLASS_MAPPINGS = {
    "ComfyBros_OllamaConnection": OllamaConnection,
    "ComfyBros_OllamaConfiguration": OllamaConfiguration,
    "ComfyBros_OllamaConverse": OllamaConverse,
    "ComfyBros_SDXLLORAPrompter": SDXLLORAPrompter,
    "ComfyBros_GenerateImage": GenerateImage,
    "ComfyBros_GenerateImageAPI": GenerateImageAPI,
    "ComfyBros_ImageToImage": ImageToImage,
    "ComfyBros_WAN22GenerateVideo": WAN22GenerateVideo,
    "ComfyBros_LoraDiscovery": LoraDiscovery,
    "ComfyBros_EndpointConfiguration": EndpointConfiguration,
    "ComfyBros_TextStorage": TextStorage,
    "ComfyBros_TextTemplate": TextTemplate,
    "ComfyBros_TextConcatenate": TextConcatenate,
    "ComfyBros_JsonParse": JsonParseNode,
    "ComfyBros_DictGet": DictGetNode,
    "ComfyBros_IntegerMath": IntegerMath,
    "ComfyBros_IntegerCompare": IntegerCompare,
    "ComfyBros_IntegerConstant": IntegerConstant,
    "ComfyBros_ImageBatchCombiner": ImageBatchCombiner,
    "ComfyBros_ImageBatchToGIF": ImageBatchToGIF,
    "ComfyBros_ImageBatchSplitter": ImageBatchSplitter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ComfyBros_OllamaConnection": "Ollama Connection",
    "ComfyBros_OllamaConfiguration": "Ollama Configuration",
    "ComfyBros_OllamaConverse": "Ollama Converse",
    "ComfyBros_SDXLLORAPrompter": "SDXL LORA Prompter",
    "ComfyBros_GenerateImage": "Generate Image",
    "ComfyBros_GenerateImageAPI": "Generate Image API",
    "ComfyBros_ImageToImage": "Image To Image",
    "ComfyBros_WAN22GenerateVideo": "WAN22 Generate Video",
    "ComfyBros_LoraDiscovery": "LORA Discovery",
    "ComfyBros_EndpointConfiguration": "Endpoint Configuration",
    "ComfyBros_TextStorage": "Text Storage",
    "ComfyBros_TextTemplate": "Text Template",
    "ComfyBros_TextConcatenate": "Text Concatenate",
    "ComfyBros_JsonParse": "JSON Parse",
    "ComfyBros_DictGet": "Dict Get",
    "ComfyBros_IntegerMath": "Integer Math",
    "ComfyBros_IntegerCompare": "Integer Compare",
    "ComfyBros_IntegerConstant": "Integer Constant",
    "ComfyBros_ImageBatchCombiner": "Image Batch Combiner",
    "ComfyBros_ImageBatchToGIF": "Image Batch to GIF",
    "ComfyBros_ImageBatchSplitter": "Image Batch Splitter",
}