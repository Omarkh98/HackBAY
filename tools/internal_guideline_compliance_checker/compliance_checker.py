import ast
from tools.internal_guideline_compliance_checker.config.guidelines import NODE_LEVEL_RULES, TREE_LEVEL_RULES

def apply_compliance_rules(code: str) -> list[dict]:
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