import argparse
import json
import os
from datetime import datetime
from tools.library_license_checker.main import check_licenses
from tools.internal_guideline_compliance_checker.main import check_compliance
from tools.code_review.helpers import gather_project_files
from devguard.tools.internal_guideline_compliance_checker.utils import gather_supported_files

def code_review(path: str, output_format: str = "text") -> list[dict]:
    """
    Run all analysis tools on each supported file in the given path.

    Args:
        path (str): File or directory path.
        output_format (str): Output format ("text", "json", etc.)

    Returns:
        list[dict]: List of per-file analysis results.
    """
    files = gather_supported_files(path)
    report = []

    for file in files:
        print(f"\n📂 Analyzing: {file}")
        file_result = {"file": file}

        # License analysis
        try:
            licenses = check_licenses(file)
            file_result["licenses"] = licenses
        except Exception as e:
            file_result["licenses"] = [f"❌ License check error: {e}"]

        # Compliance analysis
        try:
            compliance = check_compliance(file, output_format="json")
            file_result["compliance"] = compliance if isinstance(compliance, list) else []
        except Exception as e:
            file_result["compliance"] = [f"❌ Compliance check error: {e}"]

        # TODO: Add future tools here (e.g. tech stack)
        report.append(file_result)

    return report

def main():
    parser = argparse.ArgumentParser(description="Run full code review across your project.")
    parser.add_argument("path", type=str, help="Path to directory containing source code.")
    parser.add_argument("--json", "-j", action="store_true", help="Output results as JSON")
    parser.add_argument("--md", "-m", action="store_true", help="Export results as Markdown")
    args = parser.parse_args()

    output_format = "json" if args.json else "markdown" if args.md else "text"
    result = code_review(args.path, output_format)

    # Output
    os.makedirs("reports", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"reports/code_review_{timestamp}"

    if output_format == "json":
        with open(base_path + ".json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"\n✅ JSON report saved to {base_path}.json")

    elif output_format == "markdown":
        md_lines = ["# Code Review Report\n"]
        for section, content in result.items():
            md_lines.append(f"## {section.capitalize()}")
            if isinstance(content, list):
                for entry in content:
                    md_lines.append(f"- {json.dumps(entry)}")
            else:
                md_lines.append(f"{content}")
        with open(base_path + ".md", "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
        print(f"\n✅ Markdown report saved to {base_path}.md")

    else:
        print("\n[RESULT] 🧾 Code Review Summary")
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()