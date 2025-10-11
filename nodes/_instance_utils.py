"""Shared helpers for working with ComfyUI serverless instance settings."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List


try:  # pragma: no cover - ComfyUI provides this at runtime
    import folder_paths  # type: ignore
except Exception:  # pragma: no cover - fall back gracefully if unavailable
    folder_paths = None  # type: ignore


_EMPTY_LABEL = "No instances configured"


def _settings_path() -> str:
    if folder_paths is None or not getattr(folder_paths, "base_path", None):
        raise RuntimeError("ComfyUI folder paths are not available")

    return os.path.join(folder_paths.base_path, "user", "default", "comfy.settings.json")


def _load_instances() -> List[Dict[str, Any]]:
    settings_file = _settings_path()

    if not os.path.exists(settings_file):
        return []

    with open(settings_file, "r", encoding="utf-8") as file:
        settings = json.load(file)

    instances = settings.get("serverlessConfig.instances", [])
    if not isinstance(instances, list):
        raise RuntimeError("'serverlessConfig.instances' must be a list in comfy.settings.json")

    return instances


def instance_names(empty_label: str | None = None) -> List[str]:
    """Return the configured serverless instance names or a fallback label."""

    fallback = empty_label or _EMPTY_LABEL

    try:
        instances = _load_instances()
    except Exception as exc:  # pragma: no cover - defensive logging only
        print(f"Error reading instance configuration: {exc}")
        return [fallback]

    names = [instance.get("name") for instance in instances if instance.get("name")]
    return names or [fallback]


def instance_config(instance_name: str) -> Dict[str, Any]:
    """Return the configuration dictionary for ``instance_name``."""

    if not instance_name or instance_name == _EMPTY_LABEL:
        raise RuntimeError("Instance name is required")

    try:
        instances = _load_instances()
    except Exception as exc:
        raise RuntimeError(f"Error loading instance configuration: {exc}") from exc

    for instance in instances:
        if instance.get("name") == instance_name:
            return {
                "endpoint": instance.get("endpoint", ""),
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {instance.get('auth_token', '')}",
                },
            }

    raise RuntimeError(f"Instance '{instance_name}' not found in configuration")

