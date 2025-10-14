from typing import Tuple


class IntegerMath:
    """A node for performing basic integer math operations"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "operation": (["add", "subtract", "multiply", "divide", "modulo", "power"], {
                    "default": "add"
                }),
                "a": ("INT", {
                    "default": 0,
                    "min": -2147483648,
                    "max": 2147483647,
                    "step": 1
                }),
                "b": ("INT", {
                    "default": 0,
                    "min": -2147483648,
                    "max": 2147483647,
                    "step": 1
                }),
            }
        }
    
    RETURN_TYPES = ("INT", "STRING")
    RETURN_NAMES = ("result", "expression")
    FUNCTION = "calculate"
    CATEGORY = "ComfyBros/Math"
    
    def calculate(self, operation: str, a: int, b: int) -> Tuple[int, str]:
        """
        Perform the specified math operation on two integers.
        Returns both the numeric result and a string representation of the expression.
        """
        if operation == "add":
            result = a + b
            expression = f"{a} + {b} = {result}"
        elif operation == "subtract":
            result = a - b
            expression = f"{a} - {b} = {result}"
        elif operation == "multiply":
            result = a * b
            expression = f"{a} × {b} = {result}"
        elif operation == "divide":
            if b == 0:
                raise ValueError("Cannot divide by zero")
            result = a // b  # Integer division
            expression = f"{a} ÷ {b} = {result}"
        elif operation == "modulo":
            if b == 0:
                raise ValueError("Cannot modulo by zero")
            result = a % b
            expression = f"{a} % {b} = {result}"
        elif operation == "power":
            result = a ** b
            expression = f"{a} ^ {b} = {result}"
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return (result, expression)


class IntegerCompare:
    """A node for comparing integers and returning boolean results"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "comparison": (["equal", "not_equal", "greater_than", "less_than", "greater_equal", "less_equal"], {
                    "default": "equal"
                }),
                "a": ("INT", {
                    "default": 0,
                    "min": -2147483648,
                    "max": 2147483647,
                    "step": 1
                }),
                "b": ("INT", {
                    "default": 0,
                    "min": -2147483648,
                    "max": 2147483647,
                    "step": 1
                }),
            }
        }
    
    RETURN_TYPES = ("BOOLEAN", "STRING")
    RETURN_NAMES = ("result", "expression")
    FUNCTION = "compare"
    CATEGORY = "ComfyBros/Math"
    
    def compare(self, comparison: str, a: int, b: int) -> Tuple[bool, str]:
        """
        Compare two integers using the specified comparison operation.
        Returns both the boolean result and a string representation of the expression.
        """
        if comparison == "equal":
            result = a == b
            expression = f"{a} == {b} = {result}"
        elif comparison == "not_equal":
            result = a != b
            expression = f"{a} != {b} = {result}"
        elif comparison == "greater_than":
            result = a > b
            expression = f"{a} > {b} = {result}"
        elif comparison == "less_than":
            result = a < b
            expression = f"{a} < {b} = {result}"
        elif comparison == "greater_equal":
            result = a >= b
            expression = f"{a} >= {b} = {result}"
        elif comparison == "less_equal":
            result = a <= b
            expression = f"{a} <= {b} = {result}"
        else:
            raise ValueError(f"Unknown comparison: {comparison}")
        
        return (result, expression)


class IntegerConstant:
    """A node for providing integer constant values"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("INT", {
                    "default": 0,
                    "min": -2147483648,
                    "max": 2147483647,
                    "step": 1
                }),
            }
        }
    
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("value",)
    FUNCTION = "get_value"
    CATEGORY = "ComfyBros/Math"
    
    def get_value(self, value: int) -> Tuple[int]:
        """
        Return the constant integer value.
        """
        return (value,)