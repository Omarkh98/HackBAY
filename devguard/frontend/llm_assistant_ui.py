import sys
import site
import os

from devguard.router import route_to_tool

from devguard.router import route_to_tool
from devguard.utils import (load_tool_metadata,
                   build_tool_function_map,
                   extract_any_supported_filename)
from dotenv import load_dotenv
import streamlit as st
import tempfile
import os

load_dotenv()
ALLOWED_FILE_DIR = os.getenv("ALLOWED_FILE_DIR", ".")

# Dynamic function map
tool_metadata = load_tool_metadata("devguard/tool_metadata/")
TOOL_FUNCTIONS = build_tool_function_map(tool_metadata)

def render_chat_interface():
    # Session state variables
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "selected_tool" not in st.session_state:
        st.session_state.selected_tool = None
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "last_file" not in st.session_state:
        st.session_state.last_file = None
    if "last_tool" not in st.session_state:
        st.session_state.last_tool = None

    # Available files list
    with st.sidebar.expander("📁 Available project files", expanded=False):
        ignored_dirs = {"venv", ".venv", "env", "__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".idea", ".vscode"}
        try:
            py_files = []
            for root, dirs, files in os.walk(ALLOWED_FILE_DIR):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if d not in ignored_dirs]

                for file in files:
                    if file.endswith((".py", ".java", ".xml")):
                        relative_path = os.path.relpath(os.path.join(root, file), ALLOWED_FILE_DIR)
                        py_files.append(relative_path)

            if py_files:
                for file in sorted(py_files):
                    st.markdown(f"- `{file}`")
            else:
                st.info("No `.py`, `.java`, or `.xml` files found in the project directory.")
        except Exception as e:
            st.error(f"Error reading directory: {e}")

    # Chat input box
    user_input = st.chat_input("Ask something...")

    if user_input:
        tool_id = route_to_tool(user_input, tool_metadata)
        st.session_state.chat_history.append(("user", user_input))

        if tool_id not in TOOL_FUNCTIONS:
            response = f"❌ Sorry, I couldn't find a matching tool for: `{tool_id}`"
            st.session_state.chat_history.append(("ai", response))
            return

        # Extract filename from chat input
        filename = extract_any_supported_filename(user_input)

        if filename:
            potential_path = os.path.join(ALLOWED_FILE_DIR, filename)
            if os.path.isfile(potential_path):
                st.session_state.last_tool = tool_id
                st.session_state.last_file = filename

                st.session_state.chat_history.append(("ai", f"🔍 Matched tool: `{tool_id}`\n📄 Detected file: `{filename}`\n\nRunning analysis..."))

                with st.spinner(f"Running {tool_id} on {filename}..."):
                    result = TOOL_FUNCTIONS[tool_id](potential_path)

                st.session_state.last_result = result

                # Show result
                st.chat_message("ai").markdown(
                    f"✅ Here's the result:\n\n"
                    f"🔧 Tool used: `{tool_id}`\n"
                    f"📄 File: `{filename}`\n"
                )
                if isinstance(result, str):
                    st.chat_message("ai").markdown(f"```text\n{result}\n```")
                elif isinstance(result, list):
                    if st.session_state.last_tool == "library_license_checker":
                        import pandas as pd
                        df = pd.DataFrame(result)
                        df.columns = [col.capitalize() for col in df.columns]
                        st.chat_message("ai").dataframe(df, use_container_width=True)
                    else:
                        st.chat_message("ai").json(result)
                else:
                    st.chat_message("ai").write(str(result))

                return
            else:
                st.session_state.chat_history.append(("ai", f"⚠️ File `{filename}` not found in `{ALLOWED_FILE_DIR}`. Please upload it below."))
        else:
            st.session_state.chat_history.append(("ai", f"🔍 Matched tool: `{tool_id}`\n\n📎 Please upload your file below to continue."))

        st.session_state.selected_tool = tool_id

    # Render/Show all messages
    for sender, msg in st.session_state.chat_history:
        st.chat_message(sender).write(msg)

    # If there's a recent result from tool run, render it again below the chat
    if st.session_state.last_result is not None:
        st.markdown("---")
        st.subheader("📊 Most Recent Result")
        st.markdown(f"**Tool used:** `{st.session_state.last_tool}`  ")
        st.markdown(f"**File analyzed:** `{st.session_state.last_file}`")
        if isinstance(st.session_state.last_result, str):
            st.markdown(f"```text\n{st.session_state.last_result}\n```")
        elif isinstance(st.session_state.last_result, list):
            st.json(st.session_state.last_result)
        else:
            st.write(str(st.session_state.last_result))

    # Tool matched → enable file upload
    if st.session_state.selected_tool:
        uploaded_files = st.file_uploader(
            "Upload file(s) to analyze",
            type=["py", "java", "xml"],
            accept_multiple_files=True
        )

        if uploaded_files:
            results = []
            with st.spinner(f"Running `{st.session_state.selected_tool}` on {len(uploaded_files)} file(s)..."):
                for uploaded_file in uploaded_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix = os.path.splitext(uploaded_file.name)[-1]) as tmp:
                        tmp.write(uploaded_file.read())
                        temp_path = tmp.name

                    try:
                        result = TOOL_FUNCTIONS[st.session_state.selected_tool](temp_path)
                    except Exception as e:
                        result = f"⚠️ Error running tool on file `{uploaded_file.name}`: {e}"

                    results.append((uploaded_file.name, result))
                    os.remove(temp_path)

            # Display result for each file in chat
            for filename, res in results:
                st.chat_message("ai").markdown(f"### 📂 Results for `{filename}`:")
                if isinstance(res, str):
                    st.chat_message("ai").markdown(f"```text\n{res}\n```")
                elif isinstance(res, list):
                    st.chat_message("ai").json(res)
                else:
                    st.chat_message("ai").write(str(res))

            st.session_state.last_result = res
            st.session_state.last_tool = st.session_state.selected_tool
            st.session_state.last_file = filename

            # Reset selected tool for next round
            st.session_state.selected_tool = None