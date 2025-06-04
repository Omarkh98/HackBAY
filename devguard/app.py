# app.py

import streamlit as st
import threading
import pandas as pd
import time

from utils import load_tool_metadata, build_tool_render_map
from frontend.llm_assistant_ui import render_chat_interface
from file_watcher import start_file_watcher
from file_event_queue import file_event_queue # shared queue

# --- Streamlit Setup ---
st.set_page_config(page_title="🧠 AI Dev Toolkit", layout="wide")
st.title("DevHero 🦸🏼‍♀️")

# Style tweaks
st.markdown("""
    <style>
        html { font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

# --- Start Watcher Thread Once ---
if "watcher_started" not in st.session_state:
    threading.Thread(target=start_file_watcher, daemon=True).start()
    st.session_state["watcher_started"] = True

# --- Load Tools ---
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

# --- Display Auto Results from Watcher (using a placeholder for dynamic updates) ---
st.markdown("### 🕵️ Auto Check: File Changed")
output_placeholder = st.empty() # Create an empty placeholder

# This loop will continuously try to update the content
while True:
    if not file_event_queue.empty():
        event_data = file_event_queue.get()
        st.session_state["latest_tool_outputs"] = event_data
        
        with output_placeholder.container(): # Update the content within the placeholder
            file_path = event_data["file"] # Use event_data directly
            st.success(f"📄 {file_path} changed")

            for label, result in event_data["results"]:
                st.markdown(f"#### {label}")
                if isinstance(result, list) and result:
                    st.dataframe(pd.DataFrame(result), use_container_width=True)
                else:
                    st.warning("⚠️ No data found or invalid format.")
    
    time.sleep(1) # Poll every 1 second. Adjust as needed.