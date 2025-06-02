"""
File name: license_map.py

Description: This module defines mappings and constants used for normalizing and identifying
software licenses and library package aliases in the context of license checking.

Goal: These mappings facilitate consistent license identification and handling across
different libraries and naming conventions.
"""

LICENSE_NORMALIZATION_MAP = {
    "bsd": "BSD-3-Clause",
    "bsd license": "BSD-3-Clause",
    "bsd-3-clause": "BSD-3-Clause",
    "mit": "MIT",
    "apache": "Apache-2.0",
    "apache license 2.0": "Apache-2.0",
    "apache 2": "Apache-2.0",
    "apache-2.0": "Apache-2.0",
    "gpl": "GPL",
    "lgpl": "LGPL",
    "lgplv2.1": "LGPL-2.1",
    "mpl": "MPL-2.0",
    "mozilla public license 2.0": "MPL-2.0",
    "unknown": "Unknown",
    "other": "Other",
    "python-2.0": "PSF-2.0",
    "psf": "PSF-2.0",

    "apache license, version 2.0": "Apache-2.0",
    "the apache software license, version 2.0": "Apache-2.0",
    "apache license version 2.0": "Apache-2.0",
    "eclipse public license": "EPL-2.0",
    "epl": "EPL-2.0",
    "epl-2.0": "EPL-2.0",
    "eclipse public license - v 2.0": "EPL-2.0",
    "gnu general public license v2": "GPL-2.0",
    "gnu general public license v3": "GPL-3.0",
    "gnu lesser general public license v2.1": "LGPL-2.1",
    "gnu lesser general public license v3": "LGPL-3.0",
}

STANDARD_LIBS = {
    "hashlib": "PSF-2.0",
    "os": "PSF-2.0",
    "sys": "PSF-2.0",
    "math": "PSF-2.0",
    "datetime": "PSF-2.0",
    "xml": "PSF-2.0",
    "json": "PSF-2.0",
    "re": "PSF-2.0",
    "logging": "PSF-2.0",
    "itertools": "PSF-2.0",
    "functools": "PSF-2.0",
}

PACKAGE_ALIASES = {
    "sklearn": "scikit-learn",
    "dateutil": "python-dateutil",
}