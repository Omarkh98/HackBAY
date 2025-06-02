"""
File name: config/xml_guidelines.py

Description: Defines compliance rules for internal coding standards.
Each rule is a dictionary containing an ID, description, and AST-based checker function.
"""

import xml.etree.ElementTree as ET

XML_TREE_LEVEL_RULES = []
XML_NODE_LEVEL_RULES = []

def xml_rule_no_duplicate_dependencies(tree: ET.ElementTree) -> list[tuple[int, str]]:
    """
    Ensure there are no duplicate dependencies in pom.xml.
    """
    violations = []
    seen = set()
    for dep in tree.findall(".//{*}dependency"):
        group_id = dep.findtext("{*}groupId", default="").strip()
        artifact_id = dep.findtext("{*}artifactId", default="").strip()
        line_number = dep.sourceline if hasattr(dep, 'sourceline') else 0
        key = (group_id, artifact_id)
        if key in seen:
            violations.append((line_number, f"Duplicate dependency: {group_id}:{artifact_id}"))
        else:
            seen.add(key)
    return violations

def xml_rule_has_project_metadata(tree: ET.ElementTree) -> list[tuple[int, str]]:
    """
    Ensure Maven-style <project> files contain basic metadata like <name>, <description>, <url>.
    Only applies to Maven POM-style XML.
    """
    violations = []
    root = tree.getroot()

    if root.tag != "project":
        return []  # Skip non-Maven-style XML

    required_tags = ["name", "description", "url"]
    for tag in required_tags:
        if root.find(tag) is None:
            line = 1  # ET doesn’t preserve line numbers
            violations.append((line, f"Missing <{tag}> tag in project metadata."))

    return violations

def xml_rule_no_snapshot_versions(tree: ET.ElementTree) -> list[tuple[int, str]]:
    """
    Ensure that no dependencies use SNAPSHOT versions.
    """
    violations = []
    for dep in tree.findall(".//{*}dependency"):
        version = dep.findtext("{*}version", default="")
        line_number = dep.sourceline if hasattr(dep, 'sourceline') else 0
        if version.endswith("SNAPSHOT"):
            violations.append((line_number, f"Dependency uses SNAPSHOT version: {version}"))
    return violations

def xml_node_level_line_rules(xml_text: str) -> list[tuple[int, str]]:
    """
    Basic formatting rules at line level (e.g., indentation, spacing).
    """
    violations = []
    for i, line in enumerate(xml_text.splitlines(), 1):
        if "\t" in line:
            violations.append((i, "Avoid using tabs; use spaces for indentation."))
        if line.strip().startswith("<!--") and not line.strip().endswith("-->"):
            violations.append((i, "Multiline comments should be closed properly."))
    return violations

# Register rules
XML_TREE_LEVEL_RULES.extend([
    xml_rule_no_duplicate_dependencies,
    xml_rule_has_project_metadata,
    xml_rule_no_snapshot_versions,
])

XML_NODE_LEVEL_RULES.append(xml_node_level_line_rules)