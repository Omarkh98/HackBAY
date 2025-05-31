import argparse
import json
import os
from datetime import datetime

from tools.internal_guideline_compliance_checker.utils import (
    apply_compliance_rules_with_count,
    print_violations,
    gather_py_files,
    generate_markdown_report,
)

def check_compliance(
    path: str,
    output_format: str = "text",  # Options: "text", "json", "summary", "markdown"
) -> str | list[dict]:
    py_files = gather_py_files(path)
    if not py_files:
        return f"No Python files found at path: {path}"

    all_violations = []
    total_functions = 0

    for file_path in py_files:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        violations, function_count = apply_compliance_rules_with_count(code)
        for v in violations:
            v["file"] = file_path
        all_violations.extend(violations)
        total_functions += function_count

    if output_format == "json":
        return all_violations

    elif output_format == "summary":
        return (
            f"Files checked: {len(py_files)}\n"
            f"Functions checked: {total_functions}\n"
            f"Violations found: {len(all_violations)}"
        )

    elif output_format == "markdown":
        return generate_markdown_report(all_violations, py_files, total_functions)

    else:  # default to human-readable text
        if all_violations:
            from io import StringIO
            buffer = StringIO()
            print_violations(all_violations, file=buffer)
            return buffer.getvalue()
        else:
            return "✅ All checks passed. No violations found."


def main():
    parser = argparse.ArgumentParser(
        description="Check internal guideline compliance for Python file(s)."
    )
    parser.add_argument("path", type=str, help="Path to Python file or directory to check.")
    parser.add_argument("--json", "-j", action="store_true", help="Output violations as JSON")
    parser.add_argument("--summary", "-s", action="store_true", help="Output a summary only")
    parser.add_argument("--md", "-m", action="store_true", help="Output a Markdown report")

    args = parser.parse_args()

    # Determine output format
    if args.json:
        output_format = "json"
    elif args.summary:
        output_format = "summary"
    elif args.md:
        output_format = "markdown"
    else:
        output_format = "text"

    # Run compliance check
    result = check_compliance(args.path, output_format)

    # Create reports folder and base filename
    os.makedirs("reports", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"reports/report_{timestamp}"

    # Output handling
    if output_format == "json":
        output = json.dumps(result, indent=2)
        print(output)
        with open(base_path + ".json", "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\n✅ JSON report saved to {base_path}.json")

    elif output_format == "markdown":
        print(result)
        with open(base_path + ".md", "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\n✅ Markdown report saved to {base_path}.md")

    elif output_format == "summary":
        print(result)
        with open(base_path + "_summary.txt", "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\n✅ Summary report saved to {base_path}_summary.txt")

    else:  # text
        print(result)

if __name__ == "__main__":
    main()