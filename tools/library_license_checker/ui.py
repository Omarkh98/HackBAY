import streamlit as st
import pandas as pd
import tempfile
import os
import io

from tools.library_license_checker.helpers import (
    extract_python_imports,
    extract_java_imports,
    parse_pom_xml,
    deduplicate_license_results,
    get_latest_version
)
from tools.library_license_checker.license_utils import rate_license
from tools.library_license_checker.license_api import fetch_license, fetch_java_license
from tools.library_license_checker.config.java_aliases import JAVA_IMPORT_ALIASES

def render():
    uploaded_file = st.file_uploader(
        "Upload a file to analyze",
        type=["py", "java", "xml", "gradle"]
    )

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[-1]) as temp_file:
            temp_file.write(uploaded_file.read())
            temp_path = temp_file.name

        st.success("File uploaded successfully!")
        st.info(f"📄 File: `{uploaded_file.name}`")
        
        ext = os.path.splitext(uploaded_file.name)[-1].lower()

        with st.spinner("Analyzing file and retrieving license info..."):
            results = []

            if ext == ".py":
                packages = extract_python_imports(temp_path)
                results = [fetch_license(pkg) for pkg in packages]

            elif ext == ".java":
                imports = extract_java_imports(temp_path)
                for imp in imports:
                    # Find best matching alias prefix
                    matched = next((key for key in JAVA_IMPORT_ALIASES if imp.startswith(key)), None)
                    if not matched:
                        results.append({
                            "name": imp,
                            "version": "?",
                            "license": "Unknown",
                            "rating": rate_license("Unknown")
                        })
                        continue

                    group, artifact = JAVA_IMPORT_ALIASES[matched]
                    license_name = fetch_java_license(group, artifact, "latest")
                    results.append({
                        "name": f"{group}:{artifact}",
                        "version": "latest",
                        "license": license_name,
                        "rating": rate_license(license_name)
                    })

            elif ext == ".xml" and "pom" in uploaded_file.name.lower():
                deps = parse_pom_xml(temp_path)
                for group, artifact, version in deps:
                    resolved_version = version or get_latest_version(group, artifact)
                    if not resolved_version:
                        print(f"[WARN] Could not resolve version for {group}:{artifact}")
                        license_name = "Unknown"
                    else:
                        license_name = fetch_java_license(group, artifact, resolved_version)
                    results.append({
                        "name": f"{group}:{artifact}",
                        "version": resolved_version,
                        "license": license_name,
                        "rating": rate_license(license_name)
                    })
            
            elif ext == ".gradle":
                st.warning("Gradle support is not yet implemented. Stay tuned!")
                os.remove(temp_path)
                st.stop()

            else:
                st.warning("❌ Unsupported file type or structure.")
                os.remove(temp_path)
                st.stop()

        results = deduplicate_license_results(results)
        if not results:
            st.warning("No packages or dependencies found.")
        else:
            st.subheader("📦 Detected Packages and License Info")

            result_table = [
                {
                    "Package": r["name"],
                    "License": r["license"],
                    "Rating": r["rating"]
                }
                for r in results
            ]

            st.table(result_table)

            # Export to Excel
            df = pd.DataFrame(result_table)
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Licenses")

            st.download_button(
                label="📥 Download results as Excel",
                data=excel_buffer.getvalue(),
                file_name="license_check_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        os.remove(temp_path)