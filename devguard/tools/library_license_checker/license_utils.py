"""
File name: normalization.py

Description: This module provides utility functions for rating licenses and fetching
license information from pypi.
"""

import requests
from tools.library_license_checker.normalization import normalize_license_text

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
    caution = ["LGPL", "MPL", "EPL"]
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