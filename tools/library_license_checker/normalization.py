"""
File name: normalization.py

Description: This module provides functions for normalizing and processing license information.
"""

import difflib
from tools.library_license_checker.config.license_map import LICENSE_NORMALIZATION_MAP

def normalize_license_text(license_str: str) -> str:
    """
    Normalize a given license string to a standardized license identifier.

    Tries exact substring matches first, then fuzzy matching on keys to handle typos or variants.

    Args:
        license_str (str): The raw license string to normalize.

    Returns:
        str: A normalized license string, or "Unknown" if normalization fails.
    """
    try:
        if not license_str:
            return "Unknown"

        norm = license_str.strip().lower()

        # 1. Exact substring match
        for key in LICENSE_NORMALIZATION_MAP:
            if key in norm:
                return LICENSE_NORMALIZATION_MAP[key]

        # 2. Fuzzy match - find closest keys
        keys = list(LICENSE_NORMALIZATION_MAP.keys())
        close_matches = difflib.get_close_matches(norm, keys, n=1, cutoff=0.7)
        if close_matches:
            return LICENSE_NORMALIZATION_MAP[close_matches[0]]

        return "Unknown"
    except Exception:
        return "Unknown"