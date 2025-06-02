# Library License Checker

A Python tool to analyze third-party libraries imported in your code, retrieve their license information, and rate them based on legal risk. Useful for legal audits, open-source compliance, and responsible code usage.

---

## Features

- Parses `.py` files to extract all imported libraries.
- Queries license info using PyPI and fallback mechanisms.
- Normalizes and rates licenses by legal risk:
  - ✅ Trusted - Safe for most uses (MIT, BSD, Apache)
  - ⚠️ Caution - Use carefully, may impose conditions (LGPL, MPL)
  - ❌ Risky - Strong copyleft or unknown terms (GPL, AGPL, Unknown)
- CLI and Streamlit-based interface for flexible usage.
- Supports Excel export for legal documentation or compliance sharing.
- Easily integrates with LLMs or CI/CD pipelines.
- CLI-invokable and Python-callable.

## Usage
Run the checker from the command line:

```bash
python main.py <python_file.py> [options]
```

Where `<python_file.py>` is the Python file to scan.

### Command Line Options
1. **--export**, **-e**: Export license results to an Excel file named `license_check_results.xlsx`.

## Examples
1. Check a file and print library license results:
```bash
python main.py path/to/file.py
```
2. Check a file and export results to Excel:
```bash
python main.py path/to/file.py --export
```

## Streamlit Interface
Use the visual frontend to upload and check `.py` files interactively:
```bash
streamlit run app.py
```

## LLM Calable Function
`check_licenses`
```bash
from main import check_licenses
report = check_licenses("path/to/file.py")
for item in report:
    print(item["name"], item["license"], item["rating"])
```

## Report Example
```
Package              License         Rating
--------------------------------------------------
flask                BSD-3-Clause    ✅ Trusted
requests             Apache-2.0      ✅ Trusted
some-lib             Unknown         ❌ Risky
```

## Project Metadata
Tool metadata available in `tool_metadata.json`

## Testing
Run all tests:
```bash
pytest tests/
```