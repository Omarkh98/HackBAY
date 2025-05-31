import os
from io import StringIO
import sys
import pandas as pd
from tools.library_license_checker.helpers import (extract_imports,
                                                   print_license_report)
from tools.library_license_checker.license_api import fetch_license

def check_licenses(file_path: str, export: bool = False, output_path: str = "license_report.xlsx"):
    """
    Analyze a Python file and print license info for all imported packages.
    
    Args:
        file_path (str): Path to the Python file to analyze.
        export (bool): Whether to export the results to an Excel file.
        output_path (str): Path to save the Excel report (if export is True).
    """
    if not os.path.isfile(file_path):
        print(f"[ERROR] File does not exist: {file_path}")
        return

    print(f"[INFO] Analyzing file: {file_path}")

    packages = extract_imports(file_path)
    if not packages:
        print("[INFO] No packages found in the file.")
        return

    results = []
    for pkg in packages:
        result = fetch_license(pkg)
        results.append(result)

    print("\n[RESULT] License Check Report:\n")
    print_license_report(results)

    buffer = StringIO()
    original_stdout = sys.stdout
    sys.stdout = buffer
    try:
        print_license_report(results)
    finally:
        sys.stdout = original_stdout

    report = buffer.getvalue()

    if export:
        df = pd.DataFrame(results)
        df.to_excel(output_path, index=False)
        report += f"\n[INFO] Report exported to: {output_path}"
        print(f"\n[INFO] Report exported to: {output_path}")

    return report

if __name__ == "__main__":
    import argparse
    from helpers import print_license_report

    parser = argparse.ArgumentParser(description="Library License Checker")
    parser.add_argument("file", help="Path to the Python file to check")
    parser.add_argument("--export", action="store_true", help="Export results to Excel")
    parser.add_argument("--output", default="license_report.xlsx", help="Path for the Excel output file")
    args = parser.parse_args()

    try:
        results = check_licenses(args.file, export=args.export, output_path=args.output)
        if results:
            print("\n[RESULT] License Check Report:\n")
            print_license_report(results)
            if args.export:
                print(f"\n[INFO] Report exported to: {args.output}")
        else:
            print("[INFO] No packages found in the file.")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")