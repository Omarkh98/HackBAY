import os

def gather_project_files(root_path: str) -> list[str]:
    """Recursively gather all relevant source files in the project directory."""
    supported_extensions = (".py", ".java", ".xml")
    files = []
    for dirpath, _, filenames in os.walk(root_path):
        for fname in filenames:
            if fname.endswith(supported_extensions):
                files.append(os.path.join(dirpath, fname))
    return files