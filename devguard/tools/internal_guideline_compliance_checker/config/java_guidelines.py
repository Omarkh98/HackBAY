"""
File name: config/java_guidelines.py

Description: Defines compliance rules for internal coding standards.
Each rule is a dictionary containing an ID, description, and AST-based checker function.
"""

JAVA_TREE_LEVEL_RULES = []
JAVA_NODE_LEVEL_RULES = []

def java_rule_uses_logger(java_code: str) -> list[tuple[int, str]]:
    """
    Ensure that the code uses a logger instead of System.out.println().
    """
    violations = []
    for i, line in enumerate(java_code.splitlines(), 1):
        if "System.out.println" in line:
            violations.append((i, "Avoid using System.out.println(); use a logger instead."))
    return violations

def java_rule_class_javadoc(java_code: str) -> list[tuple[int, str]]:
    """
    Ensure every class has a Javadoc comment within the 3 lines above it.
    """
    violations = []
    lines = java_code.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("public class") or stripped.startswith("class"):
            has_javadoc = False
            # Look back up to 3 lines before class
            for j in range(max(i - 3, 0), i):
                if lines[j].strip().startswith("/**"):
                    has_javadoc = True
                    break
            if not has_javadoc:
                violations.append((i + 1, "Missing Javadoc comment before class declaration."))
    return violations

def java_rule_no_wildcard_imports(java_code: str) -> list[tuple[int, str]]:
    """
    Disallow wildcard imports like import java.util.*;
    """
    violations = []
    for i, line in enumerate(java_code.splitlines(), 1):
        if "import " in line and "*" in line:
            violations.append((i, "Avoid using wildcard imports."))
    return violations

def java_rule_package_declaration_present(java_code: str) -> list[tuple[int, str]]:
    """
    Ensure that the package declaration is present.
    """
    if not any(line.strip().startswith("package ") for line in java_code.splitlines()):
        return [(1, "Missing package declaration.")]
    return []

def java_rule_method_length_limit(java_code: str) -> list[tuple[int, str]]:
    """
    Warn if any method is longer than 50 lines.
    """
    violations = []
    lines = java_code.splitlines()
    in_method = False
    start_line = 0
    brace_count = 0

    for i, line in enumerate(lines):
        if (" void " in line or " int " in line or " String " in line) and ("(" in line and ")" in line) and "{" in line:
            in_method = True
            start_line = i
            brace_count = line.count("{") - line.count("}")

        elif in_method:
            brace_count += line.count("{") - line.count("}")
            if brace_count <= 0:
                in_method = False
                if i - start_line > 50:
                    violations.append((start_line + 1, "Method exceeds 50 lines. Consider refactoring."))

    return violations

JAVA_NODE_LEVEL_RULES.extend([
    java_rule_uses_logger,
    java_rule_no_wildcard_imports,
    java_rule_class_javadoc,
])

JAVA_TREE_LEVEL_RULES.extend([
    java_rule_package_declaration_present,
    java_rule_method_length_limit,
])