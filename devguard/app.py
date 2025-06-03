# app.py

import streamlit as st
from utils import load_tool_metadata
from utils import build_tool_render_map
from frontend.llm_assistant_ui import render_chat_interface

# Load metadata and tool UIs dynamically
tool_metadata = load_tool_metadata("devguard/tool_metadata/")
TOOL_RENDER = build_tool_render_map(tool_metadata)

# Sidebar: display_name mapping
tool_options = {
    tool_id: meta["display_name"]
    for tool_id, meta in tool_metadata.items()
}

# Sidebar selection
st.set_page_config(page_title="🧠 AI Dev Toolkit", layout="wide")

st.markdown("""
    <style>
        html {
            font-size: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Page layout
st.title("DevHero 🦸🏼‍♀️")


options = list(tool_options.values())
selection = st.pills("Available Agents", options, selection_mode="multi")
if selection:
    selected_tool_id = (tid for tid, dname in tool_options.items() if dname == selection)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🤖 LLM Assistant")
    render_chat_interface()
    