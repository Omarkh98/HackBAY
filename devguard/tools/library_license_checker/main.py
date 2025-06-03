"""
File name: main.py

Description: Entry point for the Library License Checker tool.
Supports Python and Java files. Determines packages, fetches license info,
rates licenses by trust level, and optionally exports results.

Designed to be CLI-invokable and LLM-callable.
"""

import os
import argparse
import pandas as pd
from devguard.tools.library_license_checker.helpers import (print_license_report,
                                                            check_java_import_file,
                                                            check_java_licenses,
                                                            check_python_licenses,
                                                            deduplicate_license_results)
from devguard.tools.library_license_checker.pom_parser import is_parent_pom

def check_licenses(file_path: str, export: bool = False, output_path: str = "license_report.xlsx"):
    """
    Dispatch license checking logic based on file type.

    Args:
        file_path (str): Path to the file (Python or Java).
        export (bool): Whether to export to Excel.
        output_path (str): Path to output Excel report.

    Returns:
        list of dicts: License info per package.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File does not exist: {file_path}")

    print(f"[INFO] Analyzing file: {file_path}")

    file_ext = os.path.splitext(file_path)[-1].lower()

    if file_ext == ".py":
        results = check_python_licenses(file_path)
    elif file_ext == ".xml" and "pom" in os.path.basename(file_path).lower():
        if is_parent_pom(file_path):
            print(f"[INFO] Skipping parent POM file: {file_path}")
            return []
        results = check_java_licenses(file_path)
    elif file_ext == ".java":
        results = check_java_import_file(file_path)
    elif file_ext == ".gradle":
        raise NotImplementedError("Gradle support coming soon.")
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    deduped_results = deduplicate_license_results(results)

    if not results:
        print("[INFO] No packages or dependencies found.")
        return []
    
    print("\n[RESULT] License Check Report:\n")
    print_license_report(deduped_results)

    if export:
        df = pd.DataFrame(results)
        df.to_excel(output_path, index=False)
        print(f"\n[INFO] Report exported to: {output_path}")

    return deduped_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Library License Checker for Python (.py), Java (.java), and Maven (.xml)")
    parser.add_argument("file", help="Path to a .py or pom.xml file to check")
    parser.add_argument("--export", action="store_true", help="Export results to Excel")
    parser.add_argument("--output", default="license_report.xlsx", help="Path for Excel export")
    args = parser.parse_args()

    try:
        check_licenses(args.file, export=args.export, output_path=args.output)
    except Exception as e:
        print(f"[ERROR] {e}")