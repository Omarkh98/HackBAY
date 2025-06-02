# tools/internal_guideline_compliance_checker/ui.py

import streamlit as st
import tempfile
import os
from datetime import datetime
from tools.internal_guideline_compliance_checker.main import check_compliance

def render():
    uploaded_file = st.file_uploader("Upload a Python (.py), Java (.java), or XML (.xml) file", type=["py", "java", "xml"])
    output_format = st.selectbox("Select output format:", ["json", "summary", "markdown"])

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[-1]) as tmp:
            tmp.write(uploaded_file.read())
            temp_path = tmp.name

        with st.spinner("Analyzing for guideline compliance..."):
            result = check_compliance(temp_path, output_format=output_format)

        os.remove(temp_path)

        st.markdown(f"### 📄 Output: {output_format.upper()}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("reports", exist_ok=True)

        if output_format == "json":
            import json
            file_path = f"reports/compliance_report_{timestamp}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

            st.success("✅ JSON report generated.")
            with open(file_path, "rb") as f:
                st.download_button(
                    label="📥 Download JSON",
                    data=f,
                    file_name="compliance_report.json",
                    mime="application/json"
                )
            st.json(result)

        elif output_format == "markdown":
            file_path = f"reports/compliance_report_{timestamp}.md"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(result)

            st.success("✅ Markdown report generated.")
            with open(file_path, "rb") as f:
                st.download_button(
                    label="📥 Download Markdown",
                    data=f,
                    file_name="compliance_report.md",
                    mime="text/markdown"
                )
            st.markdown(result)

        elif output_format == "summary":
            file_path = f"reports/compliance_report_{timestamp}_summary.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(result)

            st.success("✅ Summary report generated.")
            with open(file_path, "rb") as f:
                st.download_button(
                    label="📥 Download Summary",
                    data=f,
                    file_name="compliance_summary.txt",
                    mime="text/plain"
                )
            st.code(result)

        else:
            st.text(result)