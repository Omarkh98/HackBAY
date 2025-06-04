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
import hydralit_components as hc

# --- Streamlit Page Setup ---
st.set_page_config(page_title="🧠 AI Dev Toolkit", layout="wide")

st.markdown("""
    <style>
        html { font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

st.title("DevHero 🦸🏼‍♀️")

def on_file_change(file_path):
    print(f"📂 Detected file change: {file_path}")
    file_ext = os.path.splitext(file_path)[1]
    results = []

    # Run compliance check for supported files
    if file_ext in [".py", ".xml", ".java"]:
        compliance_result = check_compliance(file_path, output_format="json")
        print("📏 Guideline Compliance Check", compliance_result)
        results.append(("📏 Guideline Compliance Check", compliance_result))
        # Run license checker
        license_result = check_licenses(file_path)
        print("📜 Library License Check", license_result)
        results.append(("📜 Library License Check", license_result))

    # Add result to shared queue for Streamlit to pick up
    file_event_queue.put({
        "file": file_path,
        "results": results
    })
    print("file event queue", file_event_queue) 

# --- Start Watcher Thread ONCE ---
if "watcher_started" not in st.session_state:
    threading.Thread(target=start_file_watcher, args=(on_file_change,), daemon=True).start()
    st.session_state["watcher_started"] = True

# --- Check for file changes from Queue ---
if not file_event_queue.empty():
    results_from_queue = file_event_queue.get() # Renamed for clarity
    print("🚨 get file event queue", results_from_queue)
    # Now, update the UI using results_from_queue
    # Option 1: Simple markdown (as you had)
    # st.markdown(results_from_queue)

    # Option 2: Store in session_state to use your existing display logic
    st.session_state["latest_tool_outputs"] = results_from_queue
    st.rerun() # if you want to force an immediate refresh to show changes

### HERE WE NEED TO PUT THE CODE CHECK RESULTS
def show_inforcards(code_check_results):

    #can apply customisation to almost all the properties of the card, including the progress bar
    theme_bad = {'bgcolor': '#FFF0F0','title_color': 'red','content_color': 'red','icon_color': 'red', 'icon': 'fa fa-times-circle'}
    theme_neutral = {'bgcolor': '#f9f9f9','title_color': 'orange','content_color': 'orange','icon_color': 'orange', 'icon': 'fa fa-question-circle'}
    theme_good = {'bgcolor': '#EFF8F7','title_color': 'green','content_color': 'green','icon_color': 'green', 'icon': 'fa fa-check-circle'}

    cc = st.columns(4)

    with cc[0]:
        # can just use 'good', 'bad', 'neutral' sentiment to auto color the card
        hc.info_card(title='Some heading GOOD', content='All good!', sentiment='good',bar_value=77)

    with cc[1]:
        hc.info_card(title='Some BAD BAD', content='This is really bad',bar_value=12,theme_override=theme_bad)

    with cc[2]:
        hc.info_card(title='Some NEURAL', content='Oh yeah, sure.', sentiment='neutral',bar_value=55)

    with cc[3]:
        #customise the the theming for a neutral content
        hc.info_card(title='Some NEURAL',content='Maybe...',key='sec',bar_value=5,theme_override=theme_neutral)

show_inforcards(None)

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