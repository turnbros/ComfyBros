import re
import os
from typing import Tuple, Optional


class SDXLLORAPrompter:
    """SDXL LORA Prompter node similar to RgthreeSDXLPowerPromptPositive"""
    
    @classmethod
    def INPUT_TYPES(cls):
        try:
            import folder_paths
            lora_files = folder_paths.get_filename_list('loras')
            lora_choices = ['CHOOSE', 'DISABLE LORAS'] + [os.path.splitext(x)[0] for x in lora_files]
            embedding_files = folder_paths.get_filename_list('embeddings')
            embedding_choices = ['CHOOSE'] + [os.path.splitext(x)[0] for x in embedding_files]
        except ImportError:
            lora_choices = ['CHOOSE', 'DISABLE LORAS']
            embedding_choices = ['CHOOSE']
        
        try:
            from nodes import MAX_RESOLUTION
            max_res = MAX_RESOLUTION
        except ImportError:
            max_res = 8192
            
        return {
            "required": {
                "prompt_g": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "prompt_l": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
            },
            "optional": {
                "opt_model": ("MODEL",),
                "opt_clip": ("CLIP",),
                "opt_clip_width": ("INT", {
                    "default": 1024,
                    "min": 0,
                    "max": max_res
                }),
                "opt_clip_height": ("INT", {
                    "default": 1024,
                    "min": 0,
                    "max": max_res
                }),
                "insert_lora": (lora_choices,),
                "insert_embedding": (embedding_choices,),
                "target_width": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": max_res
                }),
                "target_height": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": max_res
                }),
                "crop_width": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": max_res
                }),
                "crop_height": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": max_res
                }),
            }
        }
    
    RETURN_TYPES = ("CONDITIONING", "MODEL", "CLIP", "STRING", "STRING")
    RETURN_NAMES = ("CONDITIONING", "MODEL", "CLIP", "TEXT_G", "TEXT_L")
    FUNCTION = "main"
    CATEGORY = "ComfyBros/Prompting"
    
    def get_and_strip_loras(self, prompt, silent=False):
        """Extract and strip LORA tags from prompt"""
        pattern = r'<lora:([^:>]*?)(?::(-?\d*(?:\.\d*)?))?>'
        matches = re.findall(pattern, prompt)
        
        loras = []
        unfound_loras = []
        skipped_loras = []
        
        try:
            import folder_paths
            lora_paths = folder_paths.get_filename_list('loras')
        except ImportError:
            lora_paths = []
        
        for match in matches:
            tag_path = match[0]
            strength = float(match[1] if len(match) > 1 and len(match[1]) else 1.0)
            
            if strength == 0:
                if not silent:
                    print(f"SDXLLORAPrompter: Skipping '{tag_path}' with strength of zero")
                skipped_loras.append({'lora': tag_path, 'strength': strength})
                continue
            
            lora_path = self.get_lora_by_filename(tag_path, lora_paths)
            if lora_path is None:
                unfound_loras.append({'lora': tag_path, 'strength': strength})
                continue
            
            loras.append({'lora': lora_path, 'strength': strength})
        
        cleaned_prompt = re.sub(pattern, '', prompt).strip()
        return cleaned_prompt, loras, skipped_loras, unfound_loras
    
    def get_lora_by_filename(self, file_path, lora_paths):
        """Find LORA file by filename with fuzzy matching"""
        if not lora_paths:
            return None
            
        if file_path in lora_paths:
            return file_path
        
        lora_paths_no_ext = [os.path.splitext(x)[0] for x in lora_paths]
        
        if file_path in lora_paths_no_ext:
            return lora_paths[lora_paths_no_ext.index(file_path)]
        
        file_path_no_ext = os.path.splitext(file_path)[0]
        if file_path_no_ext in lora_paths_no_ext:
            return lora_paths[lora_paths_no_ext.index(file_path_no_ext)]
        
        lora_filenames_only = [os.path.basename(x) for x in lora_paths]
        if file_path in lora_filenames_only:
            return lora_paths[lora_filenames_only.index(file_path)]
        
        file_path_filename = os.path.basename(file_path)
        if file_path_filename in lora_filenames_only:
            return lora_paths[lora_filenames_only.index(file_path_filename)]
        
        lora_filenames_no_ext = [os.path.splitext(os.path.basename(x))[0] for x in lora_paths]
        if file_path in lora_filenames_no_ext:
            return lora_paths[lora_filenames_no_ext.index(file_path)]
        
        file_path_filename_no_ext = os.path.splitext(os.path.basename(file_path))[0]
        if file_path_filename_no_ext in lora_filenames_no_ext:
            return lora_paths[lora_filenames_no_ext.index(file_path_filename_no_ext)]
        
        for lora_path in lora_paths:
            if file_path in lora_path:
                print(f"SDXLLORAPrompter: Fuzzy-matched LORA input '{file_path}' to '{lora_path}'")
                return lora_path
        
        print(f"SDXLLORAPrompter: LORA '{file_path}' not found")
        return None
    
    def get_conditioning(self, prompt_g, prompt_l, opt_clip, opt_clip_width, opt_clip_height,
                        target_width, target_height, crop_width, crop_height):
        """Generate conditioning from prompts"""
        conditioning = None
        if opt_clip is not None:
            try:
                from comfy_extras.nodes_clip_sdxl import CLIPTextEncodeSDXL
                from nodes import CLIPTextEncode
                
                do_sdxl_encode = opt_clip_width and opt_clip_height
                if do_sdxl_encode:
                    target_width = target_width if target_width and target_width > 0 else opt_clip_width
                    target_height = target_height if target_height and target_height > 0 else opt_clip_height
                    crop_width = crop_width if crop_width and crop_width > 0 else 0
                    crop_height = crop_height if crop_height and crop_height > 0 else 0
                    
                    try:
                        conditioning = CLIPTextEncodeSDXL().encode(
                            opt_clip, opt_clip_width, opt_clip_height,
                            crop_width, crop_height, target_width, target_height,
                            prompt_g, prompt_l
                        )[0]
                    except Exception:
                        do_sdxl_encode = False
                        print("SDXLLORAPrompter: Exception with CLIPTextEncodeSDXL, falling back to standard encoding")
                
                if not do_sdxl_encode:
                    combined_prompt = f"{prompt_g if prompt_g else ''}\n{prompt_l if prompt_l else ''}"
                    conditioning = CLIPTextEncode().encode(opt_clip, combined_prompt)[0]
                    
            except ImportError:
                print("SDXLLORAPrompter: Could not import CLIP encoding classes")
                
        return conditioning
    
    def main(self, prompt_g, prompt_l, opt_model=None, opt_clip=None, 
             opt_clip_width=None, opt_clip_height=None, insert_lora=None,
             insert_embedding=None, target_width=-1, target_height=-1,
             crop_width=-1, crop_height=-1):
        
        # Handle LORA processing
        if insert_lora == 'DISABLE LORAS':
            prompt_g, loras_g, _, _ = self.get_and_strip_loras(prompt_g, True)
            prompt_l, loras_l, _, _ = self.get_and_strip_loras(prompt_l, True)
            loras = loras_g + loras_l
            print(f"SDXLLORAPrompter: Disabling all found loras ({len(loras)}) and stripping LORA tags for TEXT output")
        elif opt_model is not None and opt_clip is not None:
            prompt_g, loras_g, _, _ = self.get_and_strip_loras(prompt_g)
            prompt_l, loras_l, _, _ = self.get_and_strip_loras(prompt_l)
            loras = loras_g + loras_l
            
            if len(loras) > 0:
                try:
                    from nodes import LoraLoader
                    lora_loader = LoraLoader()
                    print(f"SDXLLORAPrompter: Processing {len(loras)} LORAs...")
                    
                    for lora in loras:
                        print(f"SDXLLORAPrompter: Loading LORA '{lora['lora']}' with strength {lora['strength']}")
                        try:
                            result = lora_loader.load_lora(
                                opt_model, opt_clip, lora['lora'],
                                lora['strength'], lora['strength']
                            )
                            if result and len(result) >= 2:
                                opt_model, opt_clip = result[0], result[1]
                                print(f"SDXLLORAPrompter: Successfully loaded '{lora['lora']}'")
                            else:
                                print(f"SDXLLORAPrompter: Warning - unexpected return from load_lora for '{lora['lora']}'")
                        except Exception as e:
                            print(f"SDXLLORAPrompter: Error loading LORA '{lora['lora']}': {str(e)}")
                            # Continue with other LORAs even if one fails
                            
                    print(f"SDXLLORAPrompter: Finished processing LORAs, stripping tags for TEXT output")
                except ImportError as e:
                    print(f"SDXLLORAPrompter: Could not import LoraLoader: {str(e)}")
                except Exception as e:
                    print(f"SDXLLORAPrompter: Unexpected error during LORA processing: {str(e)}")
        elif '<lora:' in prompt_g or '<lora:' in prompt_l:
            _, loras_g, _, _ = self.get_and_strip_loras(prompt_g, True)
            _, loras_l, _, _ = self.get_and_strip_loras(prompt_l, True)
            loras = loras_g + loras_l
            if len(loras):
                print(f"SDXLLORAPrompter: Found {len(loras)} LORA tags in prompt but model & clip were not supplied!")
                print("SDXLLORAPrompter: LORAs not processed, keeping for TEXT output")
        
        # Generate conditioning
        conditioning = self.get_conditioning(
            prompt_g, prompt_l, opt_clip, opt_clip_width, opt_clip_height,
            target_width, target_height, crop_width, crop_height
        )
        
        return (conditioning, opt_model, opt_clip, prompt_g, prompt_l)