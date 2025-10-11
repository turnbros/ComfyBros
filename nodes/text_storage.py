from typing import Tuple


class TextStorage:
    """A node for storing and retrieving blocks of text"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_block": ("STRING", {
                    "multiline": True, 
                    "default": "",
                    "placeholder": "Enter your text block here..."
                }),
                "label": ("STRING", {
                    "default": "Stored Text",
                    "placeholder": "Optional label for this text block"
                }),
            },
            "optional": {
                "input_text": ("STRING", {"forceInput": True}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "store_text"
    CATEGORY = "ComfyBros/Text"
    
    def store_text(self, text_block: str, label: str, input_text: str = None) -> Tuple[str]:
        """
        Store and return a text block. Can use either the built-in text area or input from another node.
        """
        # If input_text is provided, use it instead of text_block
        if input_text is not None and input_text.strip():
            output_text = input_text
        else:
            output_text = text_block
        
        return (output_text,)


class TextTemplate:
    """A node for creating text templates with placeholder substitution"""
    
    @classmethod  
    def INPUT_TYPES(cls):
        return {
            "required": {
                "template": ("STRING", {
                    "multiline": True,
                    "default": "Hello {name}, welcome to {place}!",
                    "placeholder": "Use {variable_name} for placeholders"
                }),
            },
            "optional": {
                "var1": ("STRING", {"default": "", "placeholder": "Variable 1"}),
                "var2": ("STRING", {"default": "", "placeholder": "Variable 2"}),
                "var3": ("STRING", {"default": "", "placeholder": "Variable 3"}),
                "var4": ("STRING", {"default": "", "placeholder": "Variable 4"}),
                "var5": ("STRING", {"default": "", "placeholder": "Variable 5"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "process_template"
    CATEGORY = "ComfyBros/Text"
    
    def process_template(self, template: str, var1: str = "", var2: str = "", 
                        var3: str = "", var4: str = "", var5: str = "") -> Tuple[str]:
        """
        Process a text template by replacing placeholders with provided variables.
        Supports {var1} through {var5} as well as custom named placeholders.
        """
        result = template
        
        # Replace numbered variables
        variables = {
            "var1": var1,
            "var2": var2, 
            "var3": var3,
            "var4": var4,
            "var5": var5
        }
        
        for var_name, var_value in variables.items():
            if var_value:  # Only replace if value is provided
                result = result.replace(f"{{{var_name}}}", var_value)
        
        return (result,)


class TextConcatenate:
    """A node for concatenating multiple text inputs"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "separator": ("STRING", {
                    "default": "\n",
                    "placeholder": "Text to insert between inputs"
                }),
            },
            "optional": {
                "text1": ("STRING", {"forceInput": True}),
                "text2": ("STRING", {"forceInput": True}),
                "text3": ("STRING", {"forceInput": True}),
                "text4": ("STRING", {"forceInput": True}),
                "text5": ("STRING", {"forceInput": True}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)  
    FUNCTION = "concatenate"
    CATEGORY = "ComfyBros/Text"
    
    def concatenate(self, separator: str, text1: str = None, text2: str = None,
                   text3: str = None, text4: str = None, text5: str = None) -> Tuple[str]:
        """
        Concatenate multiple text inputs with a separator.
        """
        texts = []
        
        # Collect non-empty text inputs
        for text in [text1, text2, text3, text4, text5]:
            if text is not None and text.strip():
                texts.append(text)
        
        # Join with separator
        result = separator.join(texts)
        
        return (result,)