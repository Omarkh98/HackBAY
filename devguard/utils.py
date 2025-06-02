import os
import json
import importlib
import re

def load_tool_metadata(folder_path):
    metadata = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            path = os.path.join(folder_path, filename)
            with open(path, "r") as f:
                data = json.load(f)
                tool_id = data["name"]
                metadata[tool_id] = data
    return metadata

def load_function(module_path: str, func_name: str):
    """Dynamically import and return a function from a module."""
    module = importlib.import_module(module_path)
    return getattr(module, func_name)

def build_tool_function_map(metadata_dict):
    tool_functions = {}
    for tool_id, meta in metadata_dict.items():
        module_path = meta["entry_point"].replace(".py", "").replace("/", ".")
        fn_name = meta["functions"][0]["name"]  # assuming one main function per tool
        tool_functions[tool_id] = load_function(module_path, fn_name)
    return tool_functions

def build_tool_render_map(metadata_dict: dict) -> dict:
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