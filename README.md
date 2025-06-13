# Local AI Agent System

This repository hosts a local AI agent system, providing a versatile platform for code generation, analysis, and email management through an intuitive Streamlit-based user interface. All agents run locally on your system, ensuring data privacy and control.

---

## ✨ Features

* Streamlit User Interface: A user-friendly web interface for seamless interaction with the AI agents.
* **Code Agent**:
  * Code Generation: Generate Python scripts based on natural language descriptions.
  * Code Analysis & Editing: Analyze existing Python code and suggest improvements or perform edits as instructed.
  * Local File Saving: Automatically save generated or edited code to a designated Outputs directory on your local machine.

* **Email Agent**:
  * Unread Email Listing: Retrieve and display a bulleted list of unread emails, including subject, sender, and date.
  * Email Summarization: Get concise summaries of specific emails by providing their unique ID.
  * Secure IMAP Integration: Connects to your IMAP server using securely configured environment variables.

* **RAG Agent**:
  * Context Retieval: Retireoves relevant chunks from a document that is relevat to the user query.
  * Question Answering: Based on the retireved context answers the user query.

* **Blog Agent**:
  * Create Blog: This creates a structured blog with markdown formatiing to be edited based ion user query.
  * Post Blog: A placeholder function to potray the posting of a blog to a bloggin site like Blogger.
  * Get Last 'N' Blogs: Retrieves the last N blogs posted from a user's accoount for context if needed.

---

## 🚀 Prerequisites

Before you begin, ensure you have the following installed:

* Python 3.8+: Download from python.org.
* uv: A fast Python package installer and resolver. Install it via pip:

    ```bash
    pip install uv
    ```

* Ollama: If you plan to use local LLMs like qwen3:8B or qwen3:14B.
  * Download Ollama from ollama.com.
  * After installation, pull the required models:
        ```bash
        ollama pull qwen3:8b
        ollama pull qwen3:14b
        ```

---

## 📦 Installation

Follow these steps to set up the project locally:

1. Clone the repository:

    ```bash
    git clone https://github.com/Sudharshan-3904/LocalAgent.git
    cd LocalAgent
    ```

2. Create a virtual environment using uv (recommended):

    ```bash
    uv venv
    ```

3. Activate the virtual environment:
    * Windows:

        ```bash
        .\venv\Scripts\activate
        ```

    * macOS/Linux:

        ```bash
        source venv/bin/activate
        ```

4. Install dependencies using uv:

    ```bash
    uv pip install -r requirements.txt
    ```

    (You'll need to create a requirements.txt file if you don't have one. It should contain: streamlit, langchain, langgraph, imap-tools, python-dotenv, ollama)

---

## ⚙️ Configuration

A new .env file in root directory is expeceted for the execution of the project. The following list a few keys to be entered in the env file for the listed modeules.

* All the models in genral require the following keys:

  ```env
  OLLAMA_MODEL_NAME="loaded_local_model"
  OLLAMA_EMBEDDING_MODEL="local_embedding_model"
  ```

* The Email Agent requires your IMAP server details:

  ```env
  IMAP_HOST="your.imap.server.com"
  IMAP_USER="your_email@example.com"
  IMAP_PASS="your_email_password"
  ```

* The Blog Agent requires your blogging platform API key and username:

  ```env
  BLOGGER_USERNAME="you_blogger_username"
  BLOGGER_API_KEY="aoi_key_for _you_account"
  ```

Important: Never share your .env file or commit it to version control.

---

## 🏃‍♀️ Usage

To run the Streamlit application:

1. Activate your virtual environment (if not already active):
    * Windows: `.\venv\Scripts\activate`
    * macOS/Linux: `source venv/bin/activate`

2. Start the Streamlit app:

    ```bash
    streamlit run main.py
    ```

    (Based on your folder structure, main.py appears to be your primary Streamlit UI file.)

    This will open the application in your web browser, usually at <http://localhost:8501>.

### Interacting with the Agents

* Code Agent: In the Streamlit UI, you can type prompts like:
  * "Write a Python script to calculate the factorial of a number and save it as factorial.py."
  * "Analyze the following code and suggest efficiency improvements: [Paste your code here]"
  * Generated code will be saved in the Outputs/ directory.

* Email Agent: In the Streamlit UI, you can type prompts like:
  * "List unread emails."
  * "Summarize email with UID 12345."

* RAG Agent: In the Streamlit UI, you can type prompts like:
  * "What are the key points in the uploaded document."
  * "Summarize the second section of this document clearly and consice."

* Blog Agent: In the Streamlit UI, you can type prompts like:
  * "write a blog about LangChain Framework. Ensure it is begginer friendly and detialed."
  * "Add a section about the environment setup steps and make the tone more proessional."

---

## 📂 Project Structure

```file
.
├── .env
├── .gitignore
├── .python-version
├── main.py
├── pyproject.toml
├── uv.lock
├── Agents/
│   ├── blog_agent.py
│   ├── code_agent.py
│   ├── rag_agent.py
│   └── email_agent.py
└── Outputs/
```

---

## 💡 Future Enhancements

* Add more specialized agents (e.g., for data analysis, web scraping).
* Implement persistent chat history for each agent session.
* Support for different LLM providers (e.g., OpenAI, Google Gemini API).
* Containerization (Docker) for easier deployment.
* More robust error handling and user feedback in the UI.

---

## 📄 License

This project is licensed under the MIT License.
