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
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
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

The Email Agent requires your IMAP server details. Create a .env file in the root directory of your project and add the following:

```env
IMAP_HOST="your.imap.server.com"
IMAP_USER="your_email@example.com"
IMAP_PASS="your_email_password"
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

#### Interacting with the Agents

* Code Agent: In the Streamlit UI, you can type prompts like:
  * "Write a Python script to calculate the factorial of a number and save it as factorial.py."
  * "Analyze the following code and suggest efficiency improvements: [Paste your code here]"
  * Generated code will be saved in the Outputs/ directory.

* Email Agent: In the Streamlit UI, you can type prompts like:
  * "List unread emails."
  * "Summarize email with UID 12345."

---

## 📂 Project Structure

```file
.
├── .env                # Environment variables for sensitive information
├── .gitignore          # Files/directories to ignore in Git
├── .python-version     # (Optional) Specifies Python version for tools like pyenv
├── main.py             # Main Streamlit user interface
├── pyproject.toml      # Project configuration (e.g., for poetry, pip-tools)
├── uv.lock             # Lock file for uv (if used for dependency management)
├── Agents/             # Directory containing agent scripts
│   ├── code_agent.py   # Backend script for the Code Agent
│   └── email_agent.py  # Backend script for the Email Agent
└── Outputs/            # Directory where generated/edited code files are saved
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
