"""
File name: license_api.py

Description: This module provides the main logic to retrieve license information for given packages
by querying the Libraries.io API and fallback methods, as well as to check licenses
of imported packages against known standard libraries and aliases.
"""

import os
import requests
from dotenv import load_dotenv
from devguard.tools.library_license_checker.license_utils import (rate_license,
                           fetch_license_from_pypi)
from devguard.tools.library_license_checker.normalization import normalize_license_text

from devguard.tools.library_license_checker.config.license_map import (STANDARD_LIBS,
                                PACKAGE_ALIASES)

from tools.library_license_checker.config.java_aliases import (KNOWN_GOOD_JAVA_VERSIONS,
                                 TRUSTED_LICENSES)

import xml.etree.ElementTree as ET

load_dotenv()

API_KEY = os.getenv("LIBRARIES_IO_API_KEY")
BASE_URL = "https://libraries.io/api"

def fetch_java_license(group: str, artifact: str, version: str) -> str:
    """
    Fetch license info for a Java dependency by downloading and parsing its POM file from Maven Central.
    Falls back to a known stable version if the 'latest' version does not contain license info.

    Args:
        group (str): Maven groupId (e.g., "com.fasterxml.jackson.core")
        artifact (str): Maven artifactId (e.g., "jackson-databind")
        version (str): Version string (e.g., "2.19.0" or "latest")

    Returns:
        str: Normalized license name or "Unknown"
    """
    # Resolve latest version if needed
    original_version = version
    if version == "latest":
        try:
            url = f"https://search.maven.org/solrsearch/select?q=g:{group}+AND+a:{artifact}&rows=1&wt=json"
            response = requests.get(url)
            data = response.json()
            docs = data.get("response", {}).get("docs", [])
            if docs:
                version = docs[0].get("latestVersion", "Unknown")
            else:
                return "Unknown"
        except Exception as e:
            print(f"[ERROR] Failed to fetch latest version for {group}:{artifact}: {e}")
            return "Unknown"

    def fetch_license_for_version(ver: str) -> str:
        group_path = group.replace('.', '/')
        pom_url = f"https://repo1.maven.org/maven2/{group_path}/{artifact}/{ver}/{artifact}-{ver}.pom"

        try:
            response = requests.get(pom_url)
            if response.status_code != 200:
                return "Unknown"
            
            root = ET.fromstring(response.content)
            # Strip namespaces
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]
            licenses = root.findall('.//licenses/license/name')
            if licenses:
                print("[DEBUG] Raw license names found:", [lic.text for lic in licenses if lic.text])
                license_names = [normalize_license_text(lic.text) for lic in licenses if lic.text]
                known_licenses = [lic for lic in license_names if lic != "Unknown"]
                
                if known_licenses:
                    return " / ".join(sorted(set(known_licenses)))
                else:
                    return "Unknown"
            else:
                coord = f"{group}:{artifact}"
                if coord in TRUSTED_LICENSES:
                    return normalize_license_text(TRUSTED_LICENSES[coord])
                return "Unknown"

        except Exception as e:
            print(f"[ERROR] Failed to fetch/parse POM for {group}:{artifact}:{ver}: {e}")
            return "Unknown"

    # First attempt
    license_name = fetch_license_for_version(version)
    if license_name != "Unknown":
        return license_name

    # Try fallback if defined
    coord = f"{group}:{artifact}"
    fallback_version = KNOWN_GOOD_JAVA_VERSIONS.get(coord)
    if fallback_version and fallback_version != version:
        return fetch_license_for_version(fallback_version)

    return "Unknown"

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

        base_pkg = get_base_module_name(actual_pkg)
        
        if base_pkg in STANDARD_LIBS:
            license_name = STANDARD_LIBS[base_pkg]
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

def get_base_module_name(name: str) -> str:
    """Return the top-level module name (e.g., 'os.path' → 'os')"""
    return name.split('.')[0]