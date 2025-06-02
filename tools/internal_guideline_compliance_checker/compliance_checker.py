import ast
import xml.etree.ElementTree as ET
from tools.internal_guideline_compliance_checker.config.python_guidelines import NODE_LEVEL_RULES, TREE_LEVEL_RULES
from tools.internal_guideline_compliance_checker.config.java_guidelines import JAVA_NODE_LEVEL_RULES, JAVA_TREE_LEVEL_RULES
from tools.internal_guideline_compliance_checker.config.xml_guidelines import XML_TREE_LEVEL_RULES, XML_NODE_LEVEL_RULES

def apply_python_compliance_rules(code: str) -> list[dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [{"id": "SYNTAX", "message": f"SyntaxError: {e}", "line": 0}]

    violations = []

    # Tree-level rules
    for rule in TREE_LEVEL_RULES:
        raw_results = rule["check"](tree)
        for res in raw_results:
            if isinstance(res, tuple):
                line, message = res
            elif isinstance(res, dict):
                line = res.get("line", 0)
                message = res.get("message", rule["description"])
            else:
                continue

            violations.append({
                "id": rule["id"],
                "message": message,
                "line": line,
            })

    # Node-level rules
    for node in ast.walk(tree):
        for rule in NODE_LEVEL_RULES:
            raw_results = rule["check"](node)
            for res in raw_results:
                if isinstance(res, tuple):
                    line, message = res
                elif isinstance(res, dict):
                    line = res.get("line", 0)
                    message = res.get("message", rule["description"])
                else:
                    continue

                violations.append({
                    "id": rule["id"],
                    "message": message,
                    "line": line,
                })
                
    return violations

def apply_java_compliance_rules(code: str) -> list[dict]:
    violations = []

    for rule_fn in JAVA_TREE_LEVEL_RULES:
        results = rule_fn(code)
        for line, message in results:
            violations.append({
                "id": rule_fn.__name__,
                "message": message,
                "line": line,
            })

    for rule_fn in JAVA_NODE_LEVEL_RULES:
        results = rule_fn(code)
        for line, message in results:
            violations.append({
                "id": rule_fn.__name__,
                "message": message,
                "line": line,
            })

    return violations

def apply_xml_compliance_rules(code: str) -> list[dict]:
    violations = []

    try:
        tree = ET.ElementTree(ET.fromstring(code))
    except ET.ParseError as e:
        return [{"id": "XML_SYNTAX", "message": f"XML ParseError: {e}", "line": 0}]

    for rule_fn in XML_TREE_LEVEL_RULES:
        results = rule_fn(tree)
        for line, message in results:
            violations.append({
                "id": rule_fn.__name__,
                "message": message,
                "line": line,
            })

    for rule_fn in XML_NODE_LEVEL_RULES:
        results = rule_fn(code)
        for line, message in results:
            violations.append({
                "id": rule_fn.__name__,
                "message": message,
                "line": line,
            })

    return violations