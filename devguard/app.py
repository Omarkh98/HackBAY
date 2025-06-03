# app.py

import streamlit as st
import threading
import os
import pandas as pd

from utils import load_tool_metadata, build_tool_render_map
from frontend.llm_assistant_ui import render_chat_interface
from tools.library_license_checker.main import check_licenses
from tools.internal_guideline_compliance_checker.main import check_compliance
from file_watcher import start_file_watcher
from file_event_queue import file_event_queue  # Shared queue between thread and UI

# --- Streamlit Page Setup ---
st.set_page_config(page_title="🧠 AI Dev Toolkit", layout="wide")

st.markdown("""
    <style>
        html { font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

st.title("DevHero 🦸🏼‍♀️")

# --- Start Watcher Thread ONCE ---
if "watcher_started" not in st.session_state:
    threading.Thread(target=start_file_watcher, daemon=True).start()
    st.session_state["watcher_started"] = True

# --- Check for file changes from Queue ---
if not file_event_queue.empty():
    file_path = file_event_queue.get()
    file_ext = os.path.splitext(file_path)[1]
    print(f"📂 Processing changed file: {file_path}")

    results = [("📜 Library License Check", check_licenses(file_path))]

    if file_ext in [".py", ".xml", ".java"]:
        compliance = check_compliance(file_path, output_format="json")
        results.append(("📏 Guideline Compliance Check", compliance))

    st.session_state["latest_tool_outputs"] = {
        "file": file_path,
        "results": results
    }

    st.experimental_rerun()

# --- Load Metadata and Tool UIs ---
tool_metadata = load_tool_metadata("devguard/tool_metadata/")
TOOL_RENDER = build_tool_render_map(tool_metadata)

tool_options = {
    tool_id: meta["display_name"]
    for tool_id, meta in tool_metadata.items()
}

# --- Tool selection pills ---
options = list(tool_options.values())
selection = st.pills("Available Agents", options, selection_mode="multi")

if selection:
    selected_tool_id = next(
        tid for tid, dname in tool_options.items() if dname == selection[0]
    )

# --- Layout: LLM + Tool UI ---
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🤖 LLM Assistant")
    render_chat_interface()

with col2:
    if selection:
        st.markdown(f"### 🚀 {tool_options[selected_tool_id]}")
        TOOL_RENDER[selected_tool_id]()
    else:
        st.info("👈 Select an agent to activate its tools.")

# --- Display Auto Results from Watcher ---
if "latest_tool_outputs" in st.session_state:
    file_path = st.session_state["latest_tool_outputs"]["file"]
    st.markdown("### 🕵️ Auto Check: File Changed")
    st.success(f"📄 `{file_path}` changed")

    for label, result in st.session_state["latest_tool_outputs"]["results"]:
        st.markdown(f"#### {label}")
        if isinstance(result, list) and result:
            st.dataframe(pd.DataFrame(result), use_container_width=True)
        else:
            st.warning("⚠️ No data found or invalid format.")