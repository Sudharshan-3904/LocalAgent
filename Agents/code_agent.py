from typing import TypedDict, Optional

from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END

CHAT_MODEL = 'qwen3:8B'


class ChatState(TypedDict):
    messages: list
    uploaded_file_content: Optional[str]
    uploaded_file_extension: Optional[str] # New: to store original extension for context


@tool
def analyze_and_edit_file(file_content: str, instructions: str, original_extension: Optional[str] = None) -> str:
    """Analyzes the provided file content and edits it based on the given instructions.
    Returns the modified content. Use this when the user provides any file content for analysis or editing.
    The original_extension can be provided for context if the modification needs to respect the file type's syntax.
    """
    if not file_content:
        return "Error: No file content provided for analysis or editing."

    # Adjust prompt to be generic for any file type, but mention original_extension if available
    prompt = (
        f"You are an expert file analyzer and editor. "
        f"Analyze and modify the following file content according to these instructions: '{instructions}'.\n\n"
    )
    if original_extension:
        prompt += f"The original file had a '.{original_extension}' extension. Please consider its syntax if applicable.\n\n"

    prompt += f"File content:\n```\n{file_content}\n```\n\n"
    prompt += f"Provide ONLY the modified or generated content. Do not include explanations or markdown other than the content block if applicable."

    try:
        modified_content = raw_llm.invoke(prompt).content
        # We will not strip specific markdown like ```python, as it can be any type
        # The agent should ideally output raw content or a fenced code block with appropriate language tag
        return modified_content
    except Exception as e:
        return f"Error during file analysis and editing: {e}"


llm = init_chat_model(CHAT_MODEL, model_provider='ollama')
llm = llm.bind_tools([analyze_and_edit_file])

raw_llm = init_chat_model(CHAT_MODEL, model_provider='ollama')


def llm_node(state):
    """Invokes the LLM with the current message history and uploaded file content."""
    # Generalize system message for any file type
    system_message_content = "You are an AI assistant specialized in file content generation, analysis, and editing for various formats."

    if state.get('uploaded_file_content'):
        original_ext_info = f" (originally a '.{state['uploaded_file_extension']}' file)" if state.get('uploaded_file_extension') else ""
        system_message_content += (
            "\n\nThe user has provided the following file content for context or direct action"
            f"{original_ext_info}:\n"
            f"```\n{state['uploaded_file_content']}\n```\n\n"
            "If the user asks to analyze or edit this content, use the 'analyze_and_edit_file' tool, "
            "passing the provided file content, the user's specific instructions, and the original file extension (if known) to the tool. "
            "When responding with generated or modified content, provide it in a raw text block or fenced code block with the appropriate language tag."
        )
    system_message_content += "\nAlways respond concisely and provide content in markdown format (e.g., fenced code block with language tag like ```json or ```xml) if applicable, or raw text if not."

    messages_for_llm = [SystemMessage(content=system_message_content)] + state['messages']
    response = llm.invoke(messages_for_llm)
    return {'messages': state['messages'] + [response]}


def router(state):
    """Determines the next step in the graph based on the LLM's response."""
    last_message = state['messages'][-1]
    if getattr(last_message, 'tool_calls', None):
        first_call = last_message.tool_calls[0]
        function_name = first_call.get('function', {}).get('name', '')
        if function_name == "analyze_and_edit_file":
            return "tools"
    return 'end'


tool_node = ToolNode([analyze_and_edit_file])

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


def process_agent_request(user_instruction: str, uploaded_content: Optional[str] = None, uploaded_file_extension: Optional[str] = None) -> str:
    """
    Processes a user request for the Code Agent.
    This function acts as the entry point for a backend system.

    Args:
        user_instruction (str): The user's instruction or query.
        uploaded_content (Optional[str]): The content of a file provided by the user (e.g., for analysis/editing).
        uploaded_file_extension (Optional[str]): The extension of the uploaded file, for context.

    Returns:
        str: The agent's final response or tool output.
    """
    initial_state = {'messages': [HumanMessage(content=user_instruction)],
                     'uploaded_file_content': uploaded_content,
                     'uploaded_file_extension': uploaded_file_extension} # Pass the extension

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
        elif isinstance(last_message, ToolMessage):
            return last_message.content
        else:
            return "Agent response: " + str(last_message)
    return "No response from code agent."