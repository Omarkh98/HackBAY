# app.py

import streamlit as st
from utils import load_tool_metadata
from utils import build_tool_render_map
from frontend.llm_assistant_ui import render_chat_interface

# Load metadata and tool UIs dynamically
tool_metadata = load_tool_metadata("tool_metadata/")
TOOL_RENDER = build_tool_render_map(tool_metadata)

# Sidebar: display_name mapping
tool_options = {
    tool_id: meta["display_name"]
    for tool_id, meta in tool_metadata.items()
}

# Sidebar selection
st.set_page_config(page_title="🧠 AI Dev Toolkit", layout="wide")
st.sidebar.title("🧰 Tool Selector")
selected_display_name = st.sidebar.radio("Choose a tool:", list(tool_options.values()))
selected_tool_id = next(tid for tid, dname in tool_options.items() if dname == selected_display_name)

# Page layout
st.title("🧠 Developer Productivity Toolkit")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🤖 LLM Assistant")
    render_chat_interface()
    
with col2:
    st.markdown(f"### 🚀 {tool_options[selected_tool_id]}")
    st.info(f"🛠 Currently using: `{selected_tool_id}`")
    TOOL_RENDER[selected_tool_id]()