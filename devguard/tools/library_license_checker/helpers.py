"""
File name: helpers.py

Description: This module provides utility functions for normalizing and processing license information.
It is used by the Library License Checker tool to standardize license naming conventions
across different sources before evaluating their trustworthiness.
"""

import ast
import os
from devguard.tools.library_license_checker.config.java_aliases import JAVA_IMPORT_ALIASES
import xml.etree.ElementTree as ET
import requests

from devguard.tools.library_license_checker.license_api import fetch_license, fetch_java_license

from devguard.tools.library_license_checker.license_utils import rate_license

from typing import Union
from pathlib import Path

def extract_python_imports(file_path):
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

def parse_pom_xml(path: str) -> list[tuple[str, str, str]]:
    """
    Parses a Maven `pom.xml` file to extract dependencies.

    Args:
        path (str): Path to the pom.xml file.

    Returns:
        List[Tuple[str, str, str]]: A list of (groupId, artifactId, version) tuples.
    """
    deps = []
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        ns = {'m': 'http://maven.apache.org/POM/4.0.0'}

        for dep in root.findall(".//m:dependency", ns):
            group_el = dep.find("m:groupId", ns)
            artifact_el = dep.find("m:artifactId", ns)
            version_el = dep.find("m:version", ns)

            group = group_el.text.strip() if group_el is not None and group_el.text else None
            artifact = artifact_el.text.strip() if artifact_el is not None and artifact_el.text else None
            version = version_el.text.strip() if version_el is not None and version_el.text else None

            if group and artifact:
                deps.append((group, artifact, version))
            else:
                print(f"[WARNING] Skipping incomplete dependency in pom.xml: group={group}, artifact={artifact}")
    except Exception as e:
        print(f"[ERROR] Failed to parse pom.xml: {e}")
    return deps

def extract_java_imports(input_data: Union[str, Path]) -> list[str]:
    if isinstance(input_data, (str, Path)) and os.path.exists(str(input_data)):
        # Treat as file path
        with open(input_data, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        # Treat as raw string content
        content = input_data

    imports = set()
    try:
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("import ") and line.endswith(";"):
                pkg = line[len("import "):].rstrip(";").strip()
                parts = pkg.split(".")
                if len(parts) >= 2:
                    imports.add(".".join(parts[:3]))
    except Exception as e:
        print(f"[ERROR] Failed to parse Java imports: {e}")
    return sorted(list(imports))

def find_java_alias_for_import(java_import: str):
    # Find the longest matching prefix key in JAVA_IMPORT_ALIASES
    candidates = [key for key in JAVA_IMPORT_ALIASES if java_import.startswith(key)]
    if not candidates:
        return None, None
    # Return the alias for the longest prefix match
    best_match = max(candidates, key=len)
    return JAVA_IMPORT_ALIASES[best_match]

def check_java_import_file(file_path: str):
    raw_imports = extract_java_imports(file_path)
    results = []

    for imp in raw_imports:
        group, artifact = find_java_alias_for_import(imp)
        if not group or not artifact:
            results.append({
                "name": imp,
                "version": "?",
                "license": "Unknown",
                "rating": rate_license("Unknown")
            })
            continue

        license_name = fetch_java_license(group, artifact, "latest")  # assume latest for now
        rating = rate_license(license_name)

        results.append({
            "name": f"{group}:{artifact}",
            "version": "latest",
            "license": license_name,
            "rating": rating
        })
    return results

def check_python_licenses(file_path: str):
    packages = extract_python_imports(file_path)
    if not packages:
        return []

    results = []
    for pkg in packages:
        result = fetch_license(pkg)
        results.append(result)
    return results

def check_java_licenses(file_path: str):
    deps = parse_pom_xml(file_path)
    results = []
    for group, artifact, version in deps:
        license_name = fetch_java_license(group, artifact, version)
        rating = rate_license(license_name)
        results.append({
            "name": f"{group}:{artifact}",
            "version": version,
            "license": license_name,
            "rating": rating
        })
    return results

def deduplicate_license_results(results: list[dict]) -> list[dict]:
    """
    Deduplicate license scan results based on unique package coordinates.
    For Java, uses 'group:artifact'. For Python, uses 'name'.

    Args:
        results (list of dict): Raw license results.

    Returns:
        list of dict: Deduplicated license results.
    """
    unique_results = {}

    for r in results:
        if "group" in r and "artifact" in r:
            key = f"{r['group']}:{r['artifact']}"
        else:
            key = r.get("name")  # For Python packages

        if key not in unique_results:
            unique_results[key] = r
        else:
            # Prefer a result with a known license over "Unknown"
            if unique_results[key]["license"] == "Unknown" and r["license"] != "Unknown":
                unique_results[key] = r

    return list(unique_results.values())

def get_latest_version(group: str, artifact: str) -> str | None:
    """
    Fetches the latest version of a Maven artifact from Maven Central.

    Args:
        group (str): Group ID of the artifact.
        artifact (str): Artifact ID.

    Returns:
        str or None: Latest version string if found.
    """
    try:
        group_path = group.replace(".", "/")
        url = f"https://repo1.maven.org/maven2/{group_path}/{artifact}/maven-metadata.xml"
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print(f"[WARN] Failed to fetch maven-metadata.xml for {group}:{artifact}")
            return None

        tree = ET.fromstring(response.text)
        latest = tree.find("versioning/latest")
        if latest is not None and latest.text:
            return latest.text.strip()
    except Exception as e:
        print(f"[ERROR] Failed to get latest version for {group}:{artifact}: {e}")
    return None