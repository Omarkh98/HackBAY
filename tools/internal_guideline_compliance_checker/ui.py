# tools/internal_guideline_compliance_checker/ui.py

import streamlit as st
import tempfile
import os
from datetime import datetime
import pandas as pd
from tools.internal_guideline_compliance_checker.main import check_compliance

def render():
    uploaded_file = st.file_uploader("Upload a Python (.py) file", type=["py"])
    output_format = st.selectbox("Select output format:", ["json", "summary", "markdown"])

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
            tmp.write(uploaded_file.read())
            temp_path = tmp.name

        with st.spinner("Analyzing for guideline compliance..."):
            result = check_compliance(temp_path, output_format=output_format)

        os.remove(temp_path)

        st.markdown(f"### 📄 Output: {output_format.upper()}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("reports", exist_ok=True)

        if output_format == "json":
            # Remove 'file' key from JSON results
            for item in result:
                item.pop("file", None)

            file_path = f"reports/compliance_report_{timestamp}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(pd.DataFrame(result).to_json(indent=2, orient="records"))

            st.success("✅ JSON report generated.")
            st.download_button(
                label="📥 Download JSON",
                data=open(file_path, "rb"),
                file_name="compliance_report.json",
                mime="application/json"
            )

        elif output_format == "markdown":
            file_path = f"reports/compliance_report_{timestamp}.md"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(result)

            st.success("✅ Markdown report generated.")
            st.download_button(
                label="📥 Download Markdown",
                data=open(file_path, "rb"),
                file_name="compliance_report.md",
                mime="text/markdown"
            )

        elif output_format == "summary":
            st.code(result)

        else:  # text output
            # Clean output by removing any "file: ..." lines
            clean_lines = [line for line in result.splitlines() if not line.strip().startswith("File:")]
            st.text("\n".join(clean_lines))