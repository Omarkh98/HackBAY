"""
File name: license_api.py

Description: This module provides the main logic to retrieve license information for given packages
by querying the Libraries.io API and fallback methods, as well as to check licenses
of imported packages against known standard libraries and aliases.
"""

import os
import requests
from dotenv import load_dotenv
from tools.library_license_checker.helpers import (normalize_license_text,
                             rate_license,
                             fetch_license_from_pypi)

from tools.library_license_checker.config.license_map import (STANDARD_LIBS,
                                PACKAGE_ALIASES)

load_dotenv()

API_KEY = os.getenv("LIBRARIES_IO_API_KEY")
BASE_URL = "https://libraries.io/api"

def fetch_license(package_name: str, platform = "pypi"):
    """
    Fetch license information for a given package from Libraries.io API, with fallback
    to PyPI and normalization.

    Args:
        package_name (str): The name of the package to fetch the license for.
        platform (str, optional): The platform to query on Libraries.io (default is "pypi").

    Returns:
        dict: A dictionary containing:
            - 'name': The original package name.
            - 'license': The normalized license name or "Unknown" if not found.
            - 'rating': A rating value derived from the license.
    """
    actual_package = PACKAGE_ALIASES.get(package_name, package_name)
    url = f"{BASE_URL}/{platform}/{actual_package}?api_key={API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()

            norm = data.get("normalized_licenses")
            if norm and isinstance(norm, list) and len(norm) > 0 and norm[0] != "Other":
                license_name = norm[0]
            else:
                raw_license = data.get("licenses")
                license_name = normalize_license_text(raw_license) if raw_license else "Unknown"

            if license_name == "Unknown":
                declared = data.get("declared_licenses", [])
                if declared and isinstance(declared, list):
                    license_name = normalize_license_text(declared[0])

            if license_name == "Unknown":
                license_name = fetch_license_from_pypi(actual_package)

            return {
                "name": package_name,
                "license": license_name,
                "rating": rate_license(license_name),
            }
        else:
            return {
                "name": package_name,
                "license": "Unknown",
                "rating": rate_license("Unknown"),
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "name": package_name,
            "license": "Unknown",
            "rating": rate_license("Unknown"),
            "error": str(e)
        }
    
def check_imported_packages_licenses(imports: list[str]) -> list[dict]:
    """
    Check license information for a list of imported packages.

    For each package, this function resolves aliases, checks if it is a standard
    library (with known license), or fetches license info using `fetch_license`.

    Args:
        imports (list[str]): List of imported package names as strings.

    Returns:
        list[dict]: A list of dictionaries, each containing:
            - 'name': The original package name.
            - 'license': The license name.
            - 'rating': The license rating.
    """
    results = []
    for package in imports:
        actual_pkg = PACKAGE_ALIASES.get(package, package)
        
        if actual_pkg in STANDARD_LIBS:
            license_name = STANDARD_LIBS[actual_pkg]
            license_info = {
                "name": package,
                "license": license_name,
                "rating": rate_license(license_name)
            }
        else:
            license_info = fetch_license(actual_pkg)
            license_info["name"] = package
        results.append(license_info)
    return results