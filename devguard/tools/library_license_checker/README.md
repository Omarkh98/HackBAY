# Library License Checker

A multi-language tool to analyze third-party libraries or dependencies used in your source code, retrieve their license information, and rate them based on legal risk. Useful for legal audits, open-source compliance, and responsible code usage.

---

## Features

- Parses `.py`, `.java`, and `.xml` files to extract imported libraries or declared dependencies.
- Queries license information using:
  - PyPI for Python packages
  - Maven Central for Java dependencies (if defined)
  - XML parsing for dependencies declared in config files (e.g., Maven POMs)
- Normalizes and rates licenses by legal risk:
  - ✅ **Trusted** – Safe for most uses (MIT, BSD, Apache)
  - ⚠️ **Caution** – Use carefully, may impose conditions (LGPL, MPL)
  - ❌ **Risky** – Strong copyleft or unknown terms (GPL, AGPL, Unknown)
- CLI and Streamlit-based interface for flexible usage.
- Supports Excel export for legal documentation or compliance sharing.
- Easily integrates with LLMs or CI/CD pipelines.
- CLI-invokable and Python-callable.

## Supported Languages & File Types

| Language | File Types   | Parsed Dependencies                          |
|----------|--------------|-----------------------------------------------|
| Python   | `.py`        | `import` and `from ... import ...` statements |
| Java     | `.java`      | `import` statements                           |
| XML      | `.xml`       | `<dependency>`, `<groupId>`, `<artifactId>` from Maven-style XML |


## Usage
Run the checker from the command line:

```bash
python main.py <path.py> [options]
```

Where `<path>` is a path to a .py, .java, or .xml file.

### Command Line Options
1. **--export**, **-e**: Export license results to an Excel file named `license_check_results.xlsx`.

## Examples
1. Check a Python, Java, or XML file and print results:
```bash
python main.py path/to/file.py
python main.py path/to/file.java
python main.py path/to/pom.xml
```
2. Check a file and export results to Excel:
```bash
python main.py path/to/file.py --export
```

## Streamlit Interface
Use the visual frontend to upload and check `.py` files interactively:
```bash
streamlit run app.py
streamlit run app.py --server.enableXsrfProtection=false
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