"""
File name: config/python_guidelines.py

Description: Defines compliance rules for internal coding standards.
Each rule is a dictionary containing an ID, description, and AST-based checker function.
"""

import ast
from typing import Callable

TREE_LEVEL_RULES = []
NODE_LEVEL_RULES = []

ComplianceRule = dict[str, str | Callable[[ast.FunctionDef], list[str]]]

def rule_no_print_statements(tree: ast.AST) -> list[tuple[int, str]]:
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
            violations.append((node.lineno, "Avoid using print statements."))
    return violations

def rule_has_main_check(tree: ast.AST) -> list[tuple[int, str]]:
    """
    Ensures that the script has an `if __name__ == '__main__'` guard.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            left = node.test.left
            if isinstance(left, ast.Name) and left.id == "__name__":
                return []
    return [(0, "Missing 'if __name__ == \"__main__\"' guard.")]

def rule_todo_comments(_: ast.AST) -> list[tuple[int, str]]:
    """
    Placeholder rule: AST doesn't preserve comments.
    Needs implementation via raw source inspection.
    """
    return []

def rule_function_names_snake_case(node: ast.AST) -> list[tuple[int, str]]:
    """
    Ensures that function names are written in snake_case.
    """
    if isinstance(node, ast.FunctionDef):
        name = node.name
        if name != name.lower() or "-" in name or name != name.strip("_"):
            return [(node.lineno, f"Function '{name}' should be in snake_case.")]
    return []

def rule_limit_function_length(tree: ast.AST, max_lines: int = 50) -> list[tuple[int, str]]:
    """
    Ensures that functions do not exceed a specified number of lines.

    Args:
        tree (ast.AST): The abstract syntax tree of the code.
        max_lines (int): Maximum allowed lines per function.

    Returns:
        list[str]: List of violation messages, if any.
    """
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start_line = node.lineno
            end_line = getattr(node, 'end_lineno', start_line + 1)
            length = end_line - start_line + 1
            if length > max_lines:
                violations.append((node.lineno, f"Function '{node.name}' is too long ({length} lines > {max_lines})."))
    return violations

def rule_function_missing_docstring(node: ast.AST) -> list[tuple[int, str]]:
    if isinstance(node, ast.FunctionDef):
        if not ast.get_docstring(node):
            return [(node.lineno, f"Function '{node.name}' is missing a docstring.")]
    return []


TREE_LEVEL_RULES = [
    {
        "id": "R002",
        "description": "Ensure script has an if __name__ == '__main__' guard.",
        "check": rule_has_main_check,
    },
]

NODE_LEVEL_RULES: list[ComplianceRule] = [
    {
        "id": "R001",
        "description": "Avoid using print statements in production code.",
        "check": rule_no_print_statements,
    },
    {
        "id": "R003",
        "description": "Function names should follow snake_case style.",
        "check": rule_function_names_snake_case,
    },
    {
        "id": "R004",
        "description": "Limit function length to a maintainable number of lines.",
        "check": rule_limit_function_length,
    },
    {
        "id": "R005",
        "description": "Avoid TODO comments in code. (Not yet enforced)",
        "check": rule_todo_comments,
    },
        {
        "id": "R006",
        "description": "Avoid missing docstrings in functions",
        "check": rule_function_missing_docstring,
    }
]