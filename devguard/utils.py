import os
import json
import importlib
import re
from typing import Optional, Dict, Callable


def load_tool_metadata(folder_path: str) -> Dict[str, dict]:
    metadata = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            path = os.path.join(folder_path, filename)
            with open(path, "r") as f:
                data = json.load(f)
                tool_id = data["name"]
                metadata[tool_id] = data
    return metadata

def load_function(module_path: str, func_name: str) -> Callable:
    """Dynamically import and return a function from a module."""
    module = importlib.import_module(module_path)
    return getattr(module, func_name)

def build_tool_function_map(metadata_dict: dict) -> dict:
    tool_functions = {}
    for tool_id, meta in metadata_dict.items():
        entry_point = meta.get("entry_point", "")
        
        # Only proceed if it's a valid Python module path
        if not entry_point.endswith(".py"):
            print(f"[WARN] Skipping '{tool_id}': Entry point '{entry_point}' is not a Python file.")
            continue

        module_path = entry_point.replace(".py", "").replace("/", ".")
        fn_name = meta["functions"][0]["name"]  # assumes one main callable

        try:
            tool_functions[tool_id] = load_function(module_path, fn_name)
        except Exception as e:
            print(f"[ERROR] Could not load function for '{tool_id}': {e}")
    return tool_functions

def build_tool_render_map(metadata_dict: Dict[str, dict]) -> Dict[str, Callable]:
    renders = {}
    for tool_id in metadata_dict:
        try:
            render_func = load_function(f"tools.{tool_id}.ui", "render")
            renders[tool_id] = render_func
        except (ImportError, AttributeError, ModuleNotFoundError) as e:
            print(f"[WARN] Skipping render for {tool_id}: {e}")
    return renders

def extract_python_filename(text: str) -> str | None:
    """
    Extracts a .py filename or relative path from user input.

    Supports:
    - filenames like `main.py`
    - relative paths like `tools/some_tool/main.py`
    """
    # Match either "main.py" or "tools/some_tool/main.py"
    pattern = r"([\w\-/\\]+\.py)"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return None

def extract_xml_filename(text: str) -> Optional[str]:
    """Extract a .xml filename or path from user input."""
    pattern = r"([\w\-/\\]+\.xml)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None

def extract_java_filename(text: str) -> Optional[str]:
    """Extract a .java filename or path from user input."""
    pattern = r"([\w\-/\\]+\.java)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None

def extract_any_supported_filename(text: str) -> Optional[str]:
    """
    Tries to extract a supported filename (.py, .java, .xml) from the input text.
    Gives priority based on file extension.
    """
    for extractor in [extract_python_filename, extract_java_filename, extract_xml_filename]:
        filename = extractor(text)
        if filename:
            return filename
    return None