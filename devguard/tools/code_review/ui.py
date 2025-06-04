# devguard/tools/code_review/ui.py

import streamlit as st
import os
import pandas as pd
from tools.code_review.main import code_review

def render():
    path = st.text_input("Enter path to file or folder", value="devguard")
    if st.button("🔍 Run Code Review"):
        if not os.path.exists(path):
            st.error(f"❌ Path not found: `{path}`")
            return

        with st.spinner(f"Analyzing all supported files in `{path}`..."):
            results = code_review(path, output_format="json")

        st.success("✅ Code review complete!")

        for entry in results:
            st.markdown("---")
            st.markdown(f"### 📄 `{entry['file']}`")

            if "licenses" in entry:
                st.markdown("#### 📜 License Analysis")
                if isinstance(entry["licenses"], list) and entry["licenses"] and isinstance(entry["licenses"][0], dict):
                    st.dataframe(pd.DataFrame(entry["licenses"]))
                else:
                    for err in entry["licenses"]:
                        st.warning(err)

            if "compliance" in entry:
                st.markdown("#### 📏 Compliance Analysis")
                if isinstance(entry["compliance"], list) and entry["compliance"] and isinstance(entry["compliance"][0], dict):
                    st.dataframe(pd.DataFrame(entry["compliance"]))
                else:
                    for err in entry["compliance"]:
                        st.warning(err)