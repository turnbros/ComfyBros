import os
import json
from typing import Tuple, List, Dict, Any


class LoraDiscovery:
    """Discover and load metadata from LORA files in a directory"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {"default": ""}),
                "recursive": ("BOOLEAN", {"default": True}),
                "include_extensions": ("STRING", {"default": ".safetensors,.ckpt,.pt,.pth"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("metadata_json",)
    FUNCTION = "discover_loras"
    CATEGORY = "ComfyBros/LORA Management"
    
    def extract_safetensors_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from safetensors files"""
        try:
            # Try to read safetensors metadata
            with open(file_path, 'rb') as f:
                # Read the header length (first 8 bytes)
                header_length_bytes = f.read(8)
                if len(header_length_bytes) != 8:
                    return {"error": "Invalid safetensors file - header too short"}
                
                header_length = int.from_bytes(header_length_bytes, byteorder='little')
                
                # Read the header
                header_bytes = f.read(header_length)
                if len(header_bytes) != header_length:
                    return {"error": "Invalid safetensors file - header incomplete"}
                
                # Parse the header JSON
                header = json.loads(header_bytes.decode('utf-8'))
                
                # Extract metadata if present
                metadata = header.get('__metadata__', {})
                
                # Add tensor information
                tensor_info = {}
                for key, value in header.items():
                    if key != '__metadata__':
                        tensor_info[key] = {
                            'dtype': value.get('dtype'),
                            'shape': value.get('shape'),
                            'data_offsets': value.get('data_offsets')
                        }
                
                return {
                    "metadata": metadata,
                    "tensor_count": len(tensor_info),
                    "tensor_info": tensor_info,
                    "format": "safetensors"
                }
                
        except json.JSONDecodeError as e:
            return {"error": f"JSON decode error in safetensors header: {str(e)}"}
        except Exception as e:
            return {"error": f"Error reading safetensors file: {str(e)}"}
    
    def extract_pytorch_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract basic info from PyTorch checkpoint files"""
        try:
            # For PyTorch files, we can only get basic file info without loading the model
            # Loading large model files would be too expensive for discovery
            return {
                "format": "pytorch",
                "note": "PyTorch checkpoint - metadata extraction requires model loading",
                "file_extension": os.path.splitext(file_path)[1]
            }
        except Exception as e:
            return {"error": f"Error analyzing PyTorch file: {str(e)}"}
    
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive metadata for a LORA file"""
        try:
            # Basic file information
            stat = os.stat(file_path)
            base_metadata = {
                "filename": os.path.basename(file_path),
                "full_path": file_path,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified_time": stat.st_mtime,
                "extension": os.path.splitext(file_path)[1].lower()
            }
            
            # Extract format-specific metadata
            extension = base_metadata["extension"]
            if extension == ".safetensors":
                format_metadata = self.extract_safetensors_metadata(file_path)
            elif extension in [".ckpt", ".pt", ".pth"]:
                format_metadata = self.extract_pytorch_metadata(file_path)
            else:
                format_metadata = {"format": "unknown", "note": f"Unsupported extension: {extension}"}
            
            # Combine metadata
            combined_metadata = {**base_metadata, **format_metadata}
            
            # Look for companion files (txt, json, etc.)
            base_name = os.path.splitext(file_path)[0]
            companion_files = []
            
            for companion_ext in ['.txt', '.json', '.yaml', '.yml', '.md']:
                companion_path = base_name + companion_ext
                if os.path.exists(companion_path):
                    companion_files.append({
                        "type": companion_ext[1:],  # Remove the dot
                        "path": companion_path,
                        "size": os.path.getsize(companion_path)
                    })
            
            if companion_files:
                combined_metadata["companion_files"] = companion_files
            
            return combined_metadata
            
        except Exception as e:
            return {
                "filename": os.path.basename(file_path),
                "full_path": file_path,
                "error": f"Error processing file: {str(e)}"
            }
    
    def discover_loras(self, directory_path: str, recursive: bool, include_extensions: str) -> Tuple[str]:
        """Discover LORA files and extract their metadata"""
        
        if not directory_path or not os.path.exists(directory_path):
            error_result = {
                "error": f"Directory path does not exist: {directory_path}",
                "discovered_files": [],
                "total_count": 0
            }
            return (json.dumps(error_result, indent=2),)
        
        # Parse extensions
        extensions = [ext.strip().lower() for ext in include_extensions.split(',')]
        if not any(ext.startswith('.') for ext in extensions):
            extensions = ['.' + ext for ext in extensions]
        
        discovered_files = []
        
        try:
            if recursive:
                # Walk through all subdirectories
                for root, dirs, files in os.walk(directory_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_ext = os.path.splitext(file)[1].lower()
                        
                        if file_ext in extensions:
                            print(f"LoraDiscovery: Processing {file_path}")
                            metadata = self.get_file_metadata(file_path)
                            discovered_files.append(metadata)
            else:
                # Only scan the specified directory
                for file in os.listdir(directory_path):
                    file_path = os.path.join(directory_path, file)
                    if os.path.isfile(file_path):
                        file_ext = os.path.splitext(file)[1].lower()
                        
                        if file_ext in extensions:
                            print(f"LoraDiscovery: Processing {file_path}")
                            metadata = self.get_file_metadata(file_path)
                            discovered_files.append(metadata)
            
            # Sort by filename for consistent output
            discovered_files.sort(key=lambda x: x.get('filename', ''))
            
            # Create summary
            result = {
                "discovery_summary": {
                    "directory_path": directory_path,
                    "recursive": recursive,
                    "extensions_searched": extensions,
                    "total_files_found": len(discovered_files),
                    "successful_extractions": len([f for f in discovered_files if 'error' not in f]),
                    "failed_extractions": len([f for f in discovered_files if 'error' in f])
                },
                "discovered_files": discovered_files
            }
            
            print(f"LoraDiscovery: Found {len(discovered_files)} LORA files in {directory_path}")
            
            return (json.dumps(result, indent=2),)
            
        except Exception as e:
            error_result = {
                "error": f"Error during discovery: {str(e)}",
                "discovery_summary": {
                    "directory_path": directory_path,
                    "recursive": recursive,
                    "extensions_searched": extensions,
                    "total_files_found": 0
                },
                "discovered_files": []
            }
            return (json.dumps(error_result, indent=2),)