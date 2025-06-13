import os
import json
from typing import TypedDict, Optional

from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END

load_dotenv()

BLOGGER_USERNAME = os.getenv("BLOGGER_USERNAME")
BLOGGER_API_KEY = os.getenv("BLOGGER_API_KEY")

CHAT_MODEL = os.getenv("OLLAMA_MODEL_NAME")
LOGGED_IN = False

def login():
    """Logs in to the platform."""
    if not BLOGGER_USERNAME or not BLOGGER_API_KEY:
        raise ValueError("Blogger credentials (BLOGGER_USERNAME, BLOGGER_API_KEY) must be set in environment variables.")
    LOGGED_IN = True
    return LOGGED_IN


@tool
def create_new_blog(title, instructions):
    """Create a new blog post with the given title and content."""
    if not LOGGED_IN:
        login()
    
    prompt = (
        f"You are a blog writer. Create a new blog post with the title '{title}'. Use the followin instrucitions: \n {instructions} \n\n"
        "The blog post should be well-structured, engaging, and suitable for publication. "
        "Return the content of the blog post as a JSON object with 'title' and 'content' fields that are applicable. "
        "The respose will the passed to the 'json.loads' function, so ensure it is valid JSON.\n\n"
    )

    try:
        response = raw_llm.invoke(prompt)
        blog_post = json.loads(response.content)
        return blog_post
    except json.JSONDecodeError:
        return "Error: The response from the LLM was not valid JSON. Please ensure the output is properly formatted."
    except Exception as e:
        return f"Error during blog creation: {e}"

@tool
def post_new_blog(blog_post):
    """Post a new blog to the blogging platform."""
    if not LOGGED_IN:
        login()
    
    try:
        with open('blog_post.json', 'w') as f:
            json.dump(blog_post, f)
            return f"Blog post saved successfully with title: {blog_post['title']}"
    except Exception as e:
        return f"Error saving blog post: {e}"

@tool
def get_last_n_blogs(n=3):
    """Retrieves the last n blog posts. Returns last 3 by default."""
    if not LOGGED_IN:
        login()
    
    try:
        blogs = []
        for root, _, files in os.walk('.\\Outputs\\blogs'):
            for file in files:
                if file.endswith('.json') and len(blogs) < n:
                    blogs.append(os.path.join(root, file))
        return blogs
    except Exception as e:
        return f"Error retrieving blog posts: {e}"

class ChatState(TypedDict):
    messages: list
    latest_blog: Optional[dict]
    last_n_blogs: Optional[list]

llm = init_chat_model(CHAT_MODEL, model_provider='ollama')
tool_node = ToolNode([create_new_blog, post_new_blog, get_last_n_blogs])

raw_llm = init_chat_model(CHAT_MODEL, model_provider='ollama')

def llm_node(state):
    """Invokes the LLM with the current message history."""
    system_message = SystemMessage(content="""You are an AI assistant specialized in blog writing.
                                   You can create new blog posts, post them to the blogging platform, and retrieve the last n blog posts.
                                   Any generated blog post should be returned as a JSON object with 'title' and 'content' fields.
                                   The content should be well-structured, professional and suitable for publication.""")
    messages_for_llm = [system_message] + state['messages']
    response = llm.invoke(messages_for_llm)
    return {'messages': state['messages'] + [response]}

def router(state):
    """Determines the next step in the graph based on the LLM's response."""
    last_message = state['messages'][-1]
    if isinstance(last_message, AIMessage) and getattr(last_message, 'tool_calls', None):
        return 'tools'
    elif isinstance(last_message, ToolMessage):
        return 'llm'
    else:
        return 'end'

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


def process_blog_request(user_message: str) -> str:
    """
    Processes a user request related to blog writing through the agent graph.
    This function acts as the entry point for a backend system.

    Args:
        user_message (str): The message from the user (e.g., "Create a new blog post", "Post the latest blog").

    Returns:
        str: The response from the agent, which could be the content of a new blog post, confirmation of posting, or a list of recent blogs.
    """
    initial_state = {'messages': [HumanMessage(content=user_message)]}

    final_graph_output = None
    for s in graph.stream(initial_state):
        if 'llm' in s:
            final_graph_output = s['llm']
        elif 'tools' in s:
            final_graph_output = s['tools']

    if final_graph_output and 'messages' in final_graph_output and final_graph_output['messages']:
        last_message = final_graph_output['messages'][-1]
        if isinstance(last_message, AIMessage):
            return last_message.content
        if isinstance(last_message, AIMessage):
            return last_message.content
        elif isinstance(last_message, ToolMessage):
            return last_message.content
        else:
            return f"Agent Response: {last_message}"
    else:
        return "No response from Blog agent."
    