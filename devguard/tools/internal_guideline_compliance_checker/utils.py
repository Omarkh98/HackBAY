from devguard.tools.internal_guideline_compliance_checker.compliance_checker import apply_compliance_rules
import ast
import os
import json
import importlib

def print_violations(violations: list[dict], file=None):
    """
    Prints formatted compliance violations to stdout or a file-like object.
    
    Args:
        violations (list[dict]): List of violation dictionaries.
        file: Optional file-like object (e.g., StringIO) to write to.
    """
    seen = set()
    for v in violations:
        key = (v["id"], v["message"], v.get("line", 0))
        if key in seen:
            continue
        seen.add(key)
        line_info = f"Line {v.get('line', '?')}"
        print(f"- {v['id']} ({line_info}): {v['message']}", file=file)

def apply_compliance_rules_with_count(code: str):
    tree = ast.parse(code)
    # Count functions in the code
    function_count = sum(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
    violations = apply_compliance_rules(code)
    return violations, function_count


def gather_py_files(path: str) -> list[str]:
    if os.path.isfile(path) and path.endswith(".py"):
        return [path]
    elif os.path.isdir(path):
        py_files = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    py_files.append(os.path.join(root, file))
        return py_files
    else:
        return []
    
def generate_markdown_report(violations: list[dict], py_files, total_functions: int) -> str:
    md = f"# Internal Guidelines Compliance Report\n\n"
    md += f"**Files checked:** {len(py_files)}\n\n"
    md += f"**Functions checked:** {total_functions}\n\n"
    md += f"**Violations found:** {len(violations)}\n\n"
    
    if not violations:
        md += "✅ All checks passed. No violations found.\n"
        return md

    md += "| File | Line | Violation |\n"
    md += "|------|------|-----------|\n"
    for v in violations:
        md += f"| {v.get('file', 'N/A')} | {v['line']} | {v['message']} |\n"
    return md

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