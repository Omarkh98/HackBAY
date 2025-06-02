from tools.internal_guideline_compliance_checker.compliance_checker import (apply_python_compliance_rules,
                                apply_java_compliance_rules,
                                apply_xml_compliance_rules)
import os
import sys

def print_violations(violations: list[dict], file=sys.stdout):
    seen = set()
    for v in violations:
        key = (v["id"], v["message"], v.get("line", 0))
        if key in seen:
            continue
        seen.add(key)
        line_info = f"Line {v.get('line', '?')}"
        print(f"- {v['id']} ({line_info}): {v['message']}", file=file)
        
def apply_compliance_rules_with_count(code: str, filetype: str = "py") -> tuple[list[dict], int]:
    if filetype == "py":
        violations = apply_python_compliance_rules(code)
        function_count = code.count("def ")
    elif filetype == "java":
        violations = apply_java_compliance_rules(code)
        function_count = code.count("void ") + code.count("public ") + code.count("private ")
    elif filetype == "xml":
        violations = apply_xml_compliance_rules(code)
        function_count = 1
    else:
        violations = [{"id": "UNSUPPORTED", "message": f"Unsupported file type: {filetype}", "line": 0}]
        function_count = 0

    return violations, function_count

def gather_supported_files(path: str, extensions: tuple[str, ...] = (".py", ".java", ".xml")) -> list[str]:
    files = []
    if os.path.isfile(path) and path.endswith(extensions):
        files.append(path)
    elif os.path.isdir(path):
        for root, _, filenames in os.walk(path):
            for fname in filenames:
                if fname.endswith(extensions):
                    files.append(os.path.join(root, fname))
    return files
    
def generate_markdown_report(violations: list[dict], py_files, total_functions: int) -> str:
    md = f"# Internal Guidelines Compliance Report\n\n"
    md += f"**Files checked:** {len(py_files)}\n\n"
    md += f"**Functions checked:** {total_functions}\n\n"
    md += f"**Violations found:** {len(violations)}\n\n"
    
    if not violations:
        md += "✅ All checks passed. No violations found.\n"
        return md

    md += "| File | Line | Violation |\n"
    md += "|------|------|-----------|\n"
    for v in violations:
        md += f"| {v.get('file', 'N/A')} | {v['line']} | {v['message']} |\n"
    return md