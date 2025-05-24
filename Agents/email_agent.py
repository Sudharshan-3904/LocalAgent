import os
import json
from typing import TypedDict, Optional

from dotenv import load_dotenv
from imap_tools import MailBox, AND
from imap_tools.errors import MailboxLoginError


from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END

load_dotenv()

IMAP_HOST = os.getenv("IMAP_HOST")
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")
IMAP_FOLDER = 'INBOX'

CHAT_MODEL = 'qwen3:14B'


class ChatState(TypedDict):
    messages: list

app_state = {'messages': []}


def connect():
    """Establishes a connection to the IMAP mailbox."""
    if not all([IMAP_HOST, IMAP_USER, IMAP_PASS]):
        raise ValueError("IMAP credentials (IMAP_HOST, IMAP_USER, IMAP_PASS) must be set in environment variables.")
    try:
        mailbox = MailBox(IMAP_HOST)
        mailbox.login(IMAP_USER, IMAP_PASS, initial_folder=IMAP_FOLDER)
        return mailbox
    except MailboxLoginError:
        raise ConnectionError("Failed to log in to the IMAP mailbox. Check credentials.")
    except Exception as e:
        raise ConnectionError(f"An unexpected error occurred during IMAP connection: {e}")


@tool
def list_unread_emails():
    """Return a bullet list of all unread message's subject, UID, date, and sender."""
    try:
        with connect() as mb:
            unread = mb.fetch(criteria=AND(seen=False), headers_only=True, mark_seen=False)

            if not unread:
                return 'You have no unread messages.'

            response = json.dumps([
                {
                    'uid': mail.uid,
                    'date': mail.date.astimezone().strftime('%Y-%m-%d %H:%M'),
                    'subject': mail.subject,
                    'from': mail.from_,
                } for mail in unread
            ])
            return response
    except ConnectionError as e:
        return f"Error connecting to email server: {e}"
    except Exception as e:
        return f"An unexpected error occurred while listing unread emails: {e}"

@tool
def summarize_email(uid: str):
    """Summarize a single email given its IMAP UID. Return a short summary of the email content/body in plain text."""
    try:
        with connect() as mb:
            mail = next(mb.fetch(criteria=AND(uid=uid), mark_seen=False), None)

            if not mail:
                return f'Could not find email with uid {uid}.'

            prompt = (
                "Summarize this email concisely:\n\n"
                f"Subject: {mail.subject}\n"
                f"Sender: {mail.from_}\n"
                f"Date: {mail.date}\n"
                f"{mail.text or mail.html}"
            )

            return raw_llm.invoke(prompt).content
    except ConnectionError as e:
        return f"Error connecting to email server: {e}"
    except Exception as e:
        return f"An unexpected error occurred while summarizing email: {e}"


llm = init_chat_model(CHAT_MODEL, model_provider='ollama')
llm = llm.bind_tools([list_unread_emails, summarize_email])

raw_llm = init_chat_model(CHAT_MODEL, model_provider='ollama')


def llm_node(state):
    """Invokes the LLM with the current message history."""
    system_message = SystemMessage(content="""You are an AI assistant specialized in email management.
You can list unread emails and summarize specific emails.
When asked to list unread emails, use the 'list_unread_emails' tool.
When asked to summarize an email and provided with a UID, use the 'summarize_email' tool.
Always be concise and helpful.
""")
    messages_for_llm = [system_message] + state['messages']
    response = llm.invoke(messages_for_llm)
    return {'messages': state['messages'] + [response]}


def router(state):
    """Determines the next step in the graph based on the LLM's response."""
    last_message = state['messages'][-1]
    return 'tools' if getattr(last_message, 'tool_calls', None) else 'end'

tool_node = ToolNode([list_unread_emails, summarize_email])

def tools_node(state):
    """Executes the tool called by the LLM."""
    result = tool_node.invoke(state)
    tool_output_messages = result.get('messages', [])
    return {'messages': state['messages'] + tool_output_messages}

builder = StateGraph(ChatState)
builder.add_node('llm', llm_node)
builder.add_node('tools', tools_node)
builder.add_edge(START, 'llm')
builder.add_edge('tools', 'llm')
builder.add_conditional_edges('llm', router, {'tools': 'tools', 'end': END})

graph = builder.compile()


def process_email_request(user_message: str) -> str:
    """
    Processes a user request related to email management through the agent graph.
    This function acts as the entry point for a backend system.

    Args:
        user_message (str): The message from the user (e.g., "list unread emails", "summarize email 123").

    Returns:
        str: The agent's final response or tool output.
    """
    global app_state

    app_state['messages'] = []

    app_state['messages'].append(HumanMessage(content=user_message))

    final_graph_output = None
    for s in graph.stream(app_state):
        if 'llm' in s:
            final_graph_output = s['llm']
        elif 'tools' in s:
            final_graph_output = s['tools']

        if final_graph_output and 'messages' in final_graph_output:
            app_state['messages'] = final_graph_output['messages']

    if 'messages' in app_state and app_state['messages']:
        last_message = app_state['messages'][-1]
        if isinstance(last_message, AIMessage):
            if last_message.content:
                return last_message.content
            elif last_message.tool_calls:
                return f"AI requested tool call: {last_message.tool_calls}. Processing..."
            else:
                return "AI finished processing without explicit content."
        elif isinstance(last_message, ToolMessage):
            return last_message.content
        else:
            return f"Agent Response: {last_message}"
    else:
        return "No response from email agent."


if __name__ == '__main__':
    print("Backend Email Agent Script - Simulating Requests")
    print("------------------------------------------------")
    print("This script now acts as a backend. You can simulate requests.")
    print("Ensure IMAP_HOST, IMAP_USER, IMAP_PASS are set as environment variables.")
    print("Type 'quit' to exit.")

    while True:
        simulated_user_input = input("\nSimulate user request (e.g., 'list unread emails', 'summarize email 123', or 'quit'): ")

        if simulated_user_input.lower() == 'quit':
            break

        response = process_email_request(simulated_user_input)
        print(f"\nAgent Response: {response}")