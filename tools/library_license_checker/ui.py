import streamlit as st
import pandas as pd
import tempfile
import os
import io

from tools.library_license_checker.helpers import extract_imports
from tools.library_license_checker.license_api import fetch_license

def render():
    uploaded_file = st.file_uploader("Upload a Python (.py) file", type = ["py"])

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete = False, suffix = ".py") as temp_file:
            temp_file.write(uploaded_file.read())
            temp_path = temp_file.name
        st.success("File uploaded successfully!")

        with st.spinner("Extracting Imports..."):
            packages  = extract_imports(temp_path)

        if not packages:
            st.warning("No packages found in this file.")
        else:
            st.subheader("Detected packages and license Info")
            results = []
            for pkg in packages:
                res = fetch_license(pkg)
                results.append(res)

                result_table = [
                    {"Package": r["name"], "License": r["license"], "Rating": r["rating"]}
                    for r in results
                ]
            st.table(result_table)

            df = pd.DataFrame(result_table)

            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine = "xlsxwriter") as writer:
                df.to_excel(writer, index = False, sheet_name = "Licenses")

            st.download_button(
                label = "📥 Download results as Excel",
                data = excel_buffer.getvalue(),
                file_name = "license_check_results.xlsx",
                mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        os.remove(temp_path)