"""File system utilities for safe loading, saving, and YAML/JSON serialization."""

import json
from pathlib import Path
from typing import Dict, Any, Union
import yaml


def ensure_directory(dir_path: Union[str, Path]) -> Path:
    """Creates a directory if it does not already exist."""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Loads a YAML configuration file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_json(data: Any, file_path: Union[str, Path], indent: int = 2) -> None:
    """Saves serializable data to JSON."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)


def save_text(text: str, file_path: Union[str, Path]) -> None:
    """Saves raw text content (e.g. Markdown report) to file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
