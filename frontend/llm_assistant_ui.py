import streamlit as st
import tempfile
import os
from router import route_to_tool
from utils import load_tool_metadata, build_tool_function_map

# Load metadata and build tool map
tool_metadata = load_tool_metadata("tool_metadata/")
TOOL_FUNCTIONS = build_tool_function_map(tool_metadata)

# Initialize session state variables if missing
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_tool" not in st.session_state:
    st.session_state.selected_tool = None

def render_chat_interface():
    user_input = st.chat_input("Ask something...")

    if user_input:
        # Route user input to a tool id
        tool_id = route_to_tool(user_input, tool_metadata)
        st.session_state.chat_history.append(("user", user_input))

        if tool_id not in TOOL_FUNCTIONS:
            response = f"❌ Sorry, I couldn't find a matching tool for: `{tool_id}`"
            st.session_state.selected_tool = None
        else:
            st.session_state.selected_tool = tool_id
            response = (
                f"🔍 Matched tool: `{tool_id}`\n\n"
                "📎 Please upload your Python file(s) to analyze. "
                "You can upload multiple files if needed."
            )
        st.session_state.chat_history.append(("ai", response))

    # Render chat messages
    for sender, msg in st.session_state.chat_history:
        st.chat_message(sender).write(msg)

    # If a tool is selected, show file uploader with multiple files allowed
    if st.session_state.selected_tool:
        uploaded_files = st.file_uploader(
            "Upload Python file(s) to analyze",
            type=["py"],
            accept_multiple_files=True
        )

        if uploaded_files:
            results = []
            with st.spinner(f"Running `{st.session_state.selected_tool}` on {len(uploaded_files)} file(s)..."):
                for uploaded_file in uploaded_files:
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
                        tmp.write(uploaded_file.read())
                        temp_path = tmp.name

                    # Call the corresponding tool function with temp file path
                    try:
                        result = TOOL_FUNCTIONS[st.session_state.selected_tool](temp_path)
                    except Exception as e:
                        result = f"⚠️ Error running tool on file: {e}"

                    results.append((uploaded_file.name, result))

                    os.remove(temp_path)

            # Display results per file
            for filename, res in results:
                st.chat_message("ai").markdown(f"### Results for `{filename}`:")
                if isinstance(res, str):
                    st.chat_message("ai").markdown(f"```text\n{res}\n```")
                elif isinstance(res, list):
                    st.chat_message("ai").json(res)
                else:
                    st.chat_message("ai").write(str(res))

            # Reset selected tool for next interaction
            st.session_state.selected_tool = None