import streamlit as st
import os
from dotenv import load_dotenv, set_key, unset_key, find_dotenv
import json
import sys
import io

sys.path.insert(0, './Agents')

from Agents.code_agent import process_agent_request as process_code_request
from Agents.email_agent import process_email_request as process_email_request
from Agents.rag_agent import load_and_process_document, process_rag_request
from Agents.blog_writer import process_blog_request as process_blog_request

load_dotenv()

st.set_page_config(layout="wide", page_title="Local AI Agent System")

st.sidebar.title("Local AI Agents")
st.sidebar.markdown("---")

page_selection = st.sidebar.radio(
    "Navigate",
    ["🤖 Code Agent", "📧 Email Agent", "📎 Blog Agent", "📚 RAG Agent", "⚙️ Environment Variables"]
)
st.sidebar.markdown("---")
st.sidebar.info("All agents run locally. Ensure Ollama models are pulled and .env is configured.")


if "code_chat_history" not in st.session_state:
    st.session_state.code_chat_history = []
if "email_chat_history" not in st.session_state:
    st.session_state.email_chat_history = []
if "rag_chat_history" not in st.session_state:
    st.session_state.rag_chat_history = []
if "rag_document_chunks" not in st.session_state:
    st.session_state.rag_document_chunks = None
if "rag_is_document_loaded" not in st.session_state:
    st.session_state.rag_is_document_loaded = False
if "rag_uploaded_file_name" not in st.session_state:
    st.session_state.rag_uploaded_file_name = None
if "blog_chat_history" not in st.session_state:
    st.session_state.blog_chat_history = []
if "latest_blog" not in st.session_state:
    st.session_state.latest_blog = None
if "blogs_latest_n" not in st.session_state:
    st.session_state.last_n_blog_list = []
if "env_vars" not in st.session_state:
    st.session_state.env_vars = {}
if "generated_code_output" not in st.session_state:
    st.session_state.generated_code_output = ""
if "generated_file_name" not in st.session_state:
    st.session_state.generated_file_name = "generated_file.txt"


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


if page_selection == "🤖 Code Agent":
    st.header("Code Agent 🤖")
    st.markdown("Generate, analyze, and edit any file content. Generated content will be available for download.")

    user_query = st.text_input("Your instruction for the Code Agent:", key="code_agent_query")

    uploaded_file = st.file_uploader("Optional: Upload a file for analysis/editing:", type=None, key="code_file_upload")
    uploaded_code_content = None
    uploaded_file_extension = None
    if uploaded_file is not None:
        uploaded_code_content = uploaded_file.read().decode("utf-8")
        file_name_parts = uploaded_file.name.split('.')
        if len(file_name_parts) > 1:
            uploaded_file_extension = file_name_parts[-1]
        st.code(uploaded_code_content, language=uploaded_file_extension if uploaded_file_extension else "plaintext")


    if st.button("Run Code Agent", key="run_code_agent_btn"):
        if user_query:
            with st.spinner("Code Agent is processing..."):
                response = process_code_request(user_query, uploaded_content=uploaded_code_content, uploaded_file_extension=uploaded_file_extension)
                st.session_state.code_chat_history.append({"role": "user", "content": user_query})
                if uploaded_code_content:
                    st.session_state.code_chat_history.append({"role": "code_upload", "content": uploaded_code_content})
                st.session_state.code_chat_history.append({"role": "agent", "content": response})

                if response.startswith("```") and "\n" in response:
                    first_line = response.split('\n')[0]
                    language_tag = first_line.strip('`').strip()
                    if language_tag:
                        st.session_state.generated_file_name = f"generated_file.{language_tag}"
                        st.session_state.generated_code_output = response.lstrip(first_line).rstrip('`').strip()
                    else:
                        st.session_state.generated_file_name = "generated_file.txt"
                        st.session_state.generated_code_output = response.strip("```\n").strip("```")
                else:
                    st.session_state.generated_file_name = "generated_file.txt"
                    st.session_state.generated_code_output = response
        else:
            st.warning("Please enter an instruction for the Code Agent.")

    if st.session_state.generated_code_output:
        st.markdown("---")
        st.subheader("Download Generated File")
        st.download_button(
            label=f"Download {st.session_state.generated_file_name}",
            data=st.session_state.generated_code_output,
            file_name=st.session_state.generated_file_name,
            mime="application/octet-stream",
            key="download_generated_file_btn"
        )


    st.markdown("---")
    st.subheader("Code Agent Chat History")
    for message in st.session_state.code_chat_history:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        elif message["role"] == "code_upload":
            st.markdown(f"**Uploaded Content:**\n```\n{message['content']}\n```")
        elif message["role"] == "agent":
            st.markdown(f"**Agent:** {message['content']}")


elif page_selection == "📧 Email Agent":
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


elif page_selection == "📎 Blog Agent":
    st.header("Blog Writer Agent 📎")
    st.markdown("Write and publish blog posts, or retrieve recent posts.")

    st.info(
        "Your instruction for the Blogger Agent (e.g., 'get last n blogs', 'create blog', etc)"
    )

    blog_title_input = st.text_input("Blog Title ( Required ):", key="blog_title_input")
    blog_instruction_input = st.text_area(
        "Blog Content/Instruction ( Optional ):",
        key="blog_instruction_input",
        placeholder="Write your blog content or instructions here..."
    )

    blog_query = f"Title: {blog_title_input} Instructions: {blog_instruction_input}" if blog_title_input else ""

    if st.button("Run Blog Agent", key="blog_agent_query_btn"):
        if blog_query:
            with st.spinner("Blog Agent is working..."):
                response = process_blog_request(blog_query)
                st.session_state.blog_chat_history.append({"role": "user", "content": blog_query})
                st.session_state.blog_chat_history.append({"role": "agent", "content": response})
        else:
            st.warning("Please enter an instruction for the Blog Agent.")
    
    latest_blog_markdown = st.session_state.blog_chat_history[-1]['content'] if st.session_state.blog_chat_history else "No blog content available."

    st.markdown("---")
    st.subheader("Current Blog")
    st.markdown(latest_blog_markdown if latest_blog_markdown else "No blog generated yet.")
    st.markdown("---")

    # st.subheader("Blog Agent Chat History")
    # for message in st.session_state.email_chat_history:
    #     if message["role"] == "user":
    #         st.markdown(f"**You:** {message['content']}")
    #     elif message["role"] == "agent":
    #         st.markdown(f"**Agent:** {message['content']}")


elif page_selection == "📚 RAG Agent": # New RAG Agent Tab
    st.header("RAG Agent 📚")
    st.markdown("Upload a document (PDF, DOCX, TXT) and ask questions based on its content.")
    st.info("Requires Ollama 'nomic-embed-text' and a chat model (e.g., 'qwen3:8B') to be pulled locally.")

    uploaded_rag_file = st.file_uploader(
        "Upload a document for RAG:",
        type=["pdf", "docx", "txt"],
        key="rag_file_upload"
    )

    if st.button("Process Document", key="process_rag_doc_btn"):
        if uploaded_rag_file is not None:
            with st.spinner(f"Processing '{uploaded_rag_file.name}'... This may take a moment."):
                try:
                    file_bytes = uploaded_rag_file.read()
                    file_type = uploaded_rag_file.name.split('.')[-1]
                    st.session_state.rag_document_chunks = load_and_process_document(file_bytes, file_type)
                    st.session_state.rag_is_document_loaded = True
                    st.session_state.rag_uploaded_file_name = uploaded_rag_file.name
                    st.session_state.rag_chat_history.append({"role": "system", "content": f"Document '{uploaded_rag_file.name}' processed successfully. You can now ask questions."})
                    st.success(f"Document '{uploaded_rag_file.name}' processed and ready for questions!")
                except Exception as e:
                    st.error(f"Error processing document: {e}")
                    st.session_state.rag_is_document_loaded = False
                    st.session_state.rag_document_chunks = None
        else:
            st.warning("Please upload a document first.")

    if st.session_state.rag_is_document_loaded:
        st.markdown(f"---")
        st.subheader(f"Ask Questions about: {st.session_state.rag_uploaded_file_name}")
        rag_question = st.text_input("Your question about the document:", key="rag_question_input")

        if st.button("Ask RAG Agent", key="run_rag_agent_btn"):
            if rag_question:
                with st.spinner("RAG Agent is thinking..."):
                    try:
                        response = process_rag_request(rag_question, st.session_state.rag_document_chunks)
                        st.session_state.rag_chat_history.append({"role": "user", "content": rag_question})
                        st.session_state.rag_chat_history.append({"role": "agent", "content": response})
                    except Exception as e:
                        st.error(f"Error asking question: {e}")
            else:
                st.warning("Please enter a question.")
    else:
        st.info("Upload a document and click 'Process Document' to enable question answering.")

    st.markdown("---")
    st.subheader("RAG Agent Chat History")
    for message in st.session_state.rag_chat_history:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        elif message["role"] == "agent":
            st.markdown(f"**Agent:** {message['content']}")
        elif message["role"] == "system":
            st.info(message['content'])


elif page_selection == "⚙️ Environment Variables":
    st.header("Environment Variables (.env) Management 🛠️")
    st.warning("🚨 **Caution:** Changes to environment variables require restarting the Streamlit application to take effect in the agents.")
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

    st.subheader("Current `.env` Entries")
    if st.session_state.env_vars:
        for key, _ in st.session_state.env_vars.items():
            st.markdown(f"- {key}")
    else:
        st.info("No entries found in .env file or file does not exist.")

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
