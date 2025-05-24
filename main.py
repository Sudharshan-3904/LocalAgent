import streamlit as st
import os
from dotenv import load_dotenv, set_key, unset_key, find_dotenv
import json
import sys

sys.path.insert(0, './Agents')

from Agents.code_agent import process_agent_request as process_code_request
from Agents.email_agent import process_email_request as process_email_request

load_dotenv()

st.set_page_config(layout="wide", page_title="Local AI Agent System")

st.sidebar.title("Local AI Agents")
st.sidebar.markdown("---")

# Removed the 'icons' parameter as it's not supported in older Streamlit versions
page_selection = st.sidebar.radio(
    "Navigate",
    ["👨🏻‍💻 Code Agent", "📧 Email Agent", "⚙️ Environment Variables"]
)
st.sidebar.markdown("---")
st.sidebar.info("All agents run locally. Ensure Ollama models are pulled and .env is configured.")


if "code_chat_history" not in st.session_state:
    st.session_state.code_chat_history = []
if "email_chat_history" not in st.session_state:
    st.session_state.email_chat_history = []
if "env_vars" not in st.session_state:
    st.session_state.env_vars = {}


def load_env_file():
    env_path = find_dotenv()
    env_dict = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_dict[key] = value
    st.session_state.env_vars = env_dict

load_env_file()


if page_selection == "Code Agent":
    st.header("Code Agent 🐍")
    st.markdown("Generate, analyze, and edit Python code. Generated code will be saved in the `Outputs/` directory.")

    user_query = st.text_input("Your instruction for the Code Agent:", key="code_agent_query")

    uploaded_code_content = st.text_area(
        "Optional: Paste code for analysis/editing (e.g., for 'analyze this code'):",
        height=200,
        key="code_to_analyze"
    )

    if st.button("Run Code Agent", key="run_code_agent_btn"):
        if user_query:
            with st.spinner("Code Agent is processing..."):
                response = process_code_request(user_query, uploaded_code_content)
                st.session_state.code_chat_history.append({"role": "user", "content": user_query})
                if uploaded_code_content:
                    st.session_state.code_chat_history.append({"role": "code_upload", "content": uploaded_code_content})
                st.session_state.code_chat_history.append({"role": "agent", "content": response})
        else:
            st.warning("Please enter an instruction for the Code Agent.")

    st.markdown("---")
    st.subheader("Code Agent Chat History")
    for message in st.session_state.code_chat_history:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        elif message["role"] == "code_upload":
            st.markdown(f"**Uploaded Code:**\n```python\n{message['content']}\n```")
        elif message["role"] == "agent":
            st.markdown(f"**Agent:** {message['content']}")


elif page_selection == "Email Agent":
    st.header("Email Agent 📧")
    st.markdown("Manage your emails: list unread messages or summarize specific emails.")
    st.info("Requires IMAP credentials to be set in the `.env` file.")

    email_query = st.text_input(
        "Your instruction for the Email Agent (e.g., 'list unread emails', 'summarize email 123'):",
        key="email_agent_query"
    )

    if st.button("Run Email Agent", key="run_email_agent_btn"):
        if email_query:
            with st.spinner("Email Agent is processing..."):
                response = process_email_request(email_query)
                st.session_state.email_chat_history.append({"role": "user", "content": email_query})
                st.session_state.email_chat_history.append({"role": "agent", "content": response})
        else:
            st.warning("Please enter an instruction for the Email Agent.")

    st.markdown("---")
    st.subheader("Email Agent Chat History")
    for message in st.session_state.email_chat_history:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        elif message["role"] == "agent":
            st.markdown(f"**Agent:** {message['content']}")


elif page_selection == "⚙️ Environment Variables":
    st.header("Environment Variables (.env) Management 🛠️")
    st.warning("🚨 **Caution:** Changes to environment variables require restarting the Streamlit application to take effect in the agents.")
    st.markdown("---")

    st.subheader("Current `.env` Entries")
    if st.session_state.env_vars:
        for key, value in st.session_state.env_vars.items():
            st.text(f"{key}={value}")
    else:
        st.info("No entries found in .env file or file does not exist.")

    st.markdown("---")
    st.subheader("Add/Update Entry")
    new_key = st.text_input("Key:", key="env_new_key")
    new_value = st.text_input("Value:", key="env_new_value")

    if st.button("Save/Update Entry", key="save_env_entry_btn"):
        if new_key:
            env_path = find_dotenv()
            if not env_path:
                open('.env', 'a').close()
                env_path = find_dotenv()
            set_key(env_path, new_key, new_value)
            load_env_file()
            st.success(f"Entry '{new_key}' saved/updated. Restart app to apply changes.")
        else:
            st.warning("Key cannot be empty.")

    st.markdown("---")
    st.subheader("Remove Entry")
    if st.session_state.env_vars:
        keys_to_remove = list(st.session_state.env_vars.keys())
        selected_key_to_remove = st.selectbox("Select Key to Remove:", options=[""] + keys_to_remove, key="remove_env_key_select")

        if st.button("Remove Selected Entry", key="remove_env_entry_btn"):
            if selected_key_to_remove:
                env_path = find_dotenv()
                if env_path:
                    unset_key(env_path, selected_key_to_remove)
                    load_env_file()
                    st.success(f"Entry '{selected_key_to_remove}' removed. Restart app to apply changes.")
                else:
                    st.error(".env file not found.")
            else:
                st.warning("Please select a key to remove.")
    else:
        st.info("No entries to remove.")