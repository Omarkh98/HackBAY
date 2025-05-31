"""
File name: helpers.py

Description: This module provides utility functions for normalizing and processing license information.
It is used by the Library License Checker tool to standardize license naming conventions
across different sources before evaluating their trustworthiness.
"""

import ast
import requests

from tools.library_license_checker.config.license_map import LICENSE_NORMALIZATION_MAP

def normalize_license_text(license_str: str) -> str:
    """
    Normalize a given license string to a standardized license identifier.

    This function compares a raw license string to a predefined mapping of known 
    license formats (e.g., "bsd license", "apache 2") and returns a canonical 
    license name (e.g., "BSD-3-Clause", "Apache-2.0"). If the license string is 
    empty, unknown, or cannot be matched, it returns "Unknown".

    Args:
        license_str (str): The raw license string to normalize.

    Returns:
        str: A normalized license string, or "Unknown" if normalization fails.
    """
    try:
        if not license_str:
            return "Unknown"

        norm = license_str.strip().lower()
        for key in LICENSE_NORMALIZATION_MAP:
            if key in norm:
                return LICENSE_NORMALIZATION_MAP[key]
        return "Unknown"
    except Exception:
        return "Unknown"

def rate_license(license_name: str):
    """
    Categorize a software license into a trustworthiness rating.

    This function classifies a given license name as one of the following categories:
    - ✅ Trusted: Common permissive licenses like MIT, Apache, BSD, or PSF.
    - ⚠️ Caution: Less permissive licenses like LGPL or MPL.
    - ❌ Risky: Restrictive licenses like GPL, AGPL, or unknown/ambiguous types.
    - ⚠️ Unknown: If the license does not match any known patterns.

    The classification is based on substring matches in the uppercase form 
    of the license name.

    Args:
        license_name (str): The normalized license name to rate.

    Returns:
        str: A visual indicator and label of the license rating.
    """
    trusted = ["MIT", "APACHE", "BSD", "PSF"]
    caution = ["LGPL", "MPL"]
    risky = ["GPL", "AGPL", "UNKNOWN", "OTHER"]

    license_upper = license_name.upper()

    if any(t in license_upper for t in trusted):
        return "✅ Trusted"
    elif any(c in license_upper for c in caution):
        return "⚠️ Caution"
    elif any(r in license_upper for r in risky):
        return "❌ Risky"
    else:
        return "⚠️ Unknown"
    
def fetch_license_from_pypi(package_name: str) -> str:
    """
    Fetch and normalize the license of a Python package from the PyPI registry.

    This function queries the PyPI JSON API for the specified package and attempts to
    extract and normalize the license string using a predefined normalization map.

    If the license is successfully fetched and recognized, it returns the normalized license name.
    If not found or if any error occurs, it returns "Unknown".

    Args:
        package_name (str): The name of the Python package to query.

    Returns:
        str: The normalized license name if found, otherwise "Unknown".
    """
    FALLBACK_PYPI_URL = "https://pypi.org/pypi"
    try:
        url = f"{FALLBACK_PYPI_URL}/{package_name}/json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            license_str = data.get("info", {}).get("license", "").strip()
            if license_str:
                return normalize_license_text(license_str)
    except Exception:
        pass
    return "Unknown"

def extract_imports(file_path):
    """
    Extract the top-level imported package names from a Python (.py) file.

    This function parses the Python source code to identify all `import` and
    `from ... import ...` statements, and collects the top-level module names

    Args:
        file_path (str): The path to the Python file from which to extract imports.

    Returns:
        List[str]: A sorted list of unique top-level imported package names.
                   Returns an empty list if parsing fails due to syntax errors.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        code_str = f.read()

    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        print("Syntax error while parsing:", e)
        return []

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    return sorted(list(imports))

def read_code_file(file_path: str) -> str:
    """
    Read the contents of a Python (.py) source code file.

    Opens the specified file using UTF-8 encoding and returns its entire content
    as a string. This function is useful for preparing source code for analysis,
    extraction, or inspection.

    Args:
        file_path (str): The absolute or relative path to the Python file.

    Returns:
        str: The contents of the file as a single string.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def print_license_report(results: list[dict]):
    """
    Print a formatted license report to the console.

    Displays a table with aligned columns showing each package's name,
    its detected license, and the assigned rating (e.g., Trusted, Caution, Risky).

    This function is primarily used for CLI-based usage or debugging, offering
    a quick summary of license evaluation results.

    Args:
        results (list[dict]): A list of dictionaries, each containing:
            - 'name' (str): The package name.
            - 'license' (str): The normalized license name.
            - 'rating' (str): The license risk rating.
    """
    print(f"{'Package':20} {'License':15} {'Rating'}")
    print("-" * 50)
    for res in results:
        print(f"{res['name']:20} {res['license']:15} {res['rating']}")

def parse_requirements_text(file_path: str):
    """
    Parse a requirements file to extract package names without version specifiers.

    Args:
        file_path (str): Path to the requirements text file (e.g., requirements.txt).

    Returns:
        list[str]: A list of package names as strings, with version specifiers removed.
    """
    packages = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                pkg = line.split("==")[0].split(">=")[0].split("<=")[0]
                packages.append(pkg)
    return packages