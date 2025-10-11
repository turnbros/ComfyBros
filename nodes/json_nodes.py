"""Nodes for working with JSON data in ComfyBros."""

from __future__ import annotations

import json
from typing import Any, Dict, Tuple


def _coerce_to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except (ValueError, AttributeError):
            return None
    return None


def _coerce_to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except (ValueError, AttributeError):
            return None
    return None


def _coerce_to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
        return None
    if isinstance(value, (int, float)):
        return bool(value)
    return None


class JsonParseNode:
    """Parse a JSON string into a Python dictionary."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": '{\n    "key": "value"\n}',
                        "placeholder": "Enter JSON here or connect another STRING input",
                    },
                )
            },
            "optional": {
                "json_input": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("PYDICT",)
    RETURN_NAMES = ("py_dict",)
    FUNCTION = "parse_json"
    CATEGORY = "ComfyBros/JSON"

    def parse_json(self, json_text: str, json_input: str | None = None) -> Tuple[Dict[str, Any]]:
        text_source = json_input if json_input and json_input.strip() else json_text
        try:
            data = json.loads(text_source)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse JSON: {exc.msg} (line {exc.lineno}, column {exc.colno})") from exc

        if not isinstance(data, dict):
            raise ValueError("JSON root must be an object that can be represented as a Python dict.")

        return (data,)


class DictGetNode:
    """Retrieve a value from a Python dictionary using a key (supports dot notation)."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "py_dict": ("PYDICT",),
                "key": (
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "Key or dotted path (e.g. settings.width)",
                    },
                ),
            },
            "optional": {
                "default": (
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "Optional default value if key is missing",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "INT", "FLOAT", "BOOLEAN", "PYDICT", "PYLIST")
    RETURN_NAMES = ("as_string", "as_int", "as_float", "as_bool", "as_dict", "as_list")
    FUNCTION = "get_value"
    CATEGORY = "ComfyBros/JSON"

    def _resolve_key(self, data: Dict[str, Any], key: str) -> Any:
        if not key:
            raise ValueError("Key is required to retrieve a value from the dictionary.")

        current: Any = data
        parts = key.split(".")
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise KeyError(part)
        return current

    def _parse_default(self, default: str) -> Any:
        if default == "":
            return None
        try:
            return json.loads(default)
        except json.JSONDecodeError:
            return default

    def get_value(self, py_dict: Dict[str, Any], key: str, default: str = "") -> Tuple[Any, ...]:
        try:
            value = self._resolve_key(py_dict, key)
        except (KeyError, ValueError):
            value = self._parse_default(default)

        if isinstance(value, (dict, list)):
            string_value = json.dumps(value)
        else:
            string_value = "" if value is None else str(value)

        int_value = _coerce_to_int(value)
        float_value = _coerce_to_float(value)
        bool_value = _coerce_to_bool(value)

        dict_value = value if isinstance(value, dict) else None
        list_value = value if isinstance(value, list) else None

        return (
            string_value,
            int_value,
            float_value,
            bool_value,
            dict_value,
            list_value,
        )
