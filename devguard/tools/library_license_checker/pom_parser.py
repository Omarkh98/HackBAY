import xml.etree.ElementTree as ET

def is_parent_pom(file_path: str) -> bool:
    """
    Detects if the given POM file is a parent POM with modules (not an actual dependency file).

    Args:
        file_path (str): Path to the POM file.

    Returns:
        bool: True if it's a parent POM, False otherwise.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        ns = {'m': 'http://maven.apache.org/POM/4.0.0'}

        packaging = root.find("m:packaging", ns)
        modules = root.find("m:modules", ns)
        if packaging is not None and packaging.text == "pom" and modules is not None:
            return True
    except Exception as e:
        print(f"[ERROR] Failed to parse POM file for parent detection: {e}")
    return False