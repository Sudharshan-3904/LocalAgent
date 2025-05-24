import os
import io
from typing import TypedDict, Optional, List
from PyPDF2 import PdfReader
from docx import Document

from langchain.chat_models import init_chat_model
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END

CHAT_MODEL = 'qwen3:8B'
EMBEDDING_MODEL = 'nomic-embed-text'
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RETRIEVAL = 4

class ChatState(TypedDict):
    """
    Represents the state of the RAG agent's conversation.
    """
    messages: list

def _load_pdf(file_content: io.BytesIO) -> str:
    """Loads text from a PDF file."""
    reader = PdfReader(file_content)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def _load_docx(file_content: io.BytesIO) -> str:
    """Loads text from a DOCX file."""
    document = Document(file_content)
    text = "\n".join([paragraph.text for paragraph in document.paragraphs])
    return text

def _load_txt(file_content: io.BytesIO) -> str:
    """Loads text from a TXT file."""
    return file_content.read().decode('utf-8')

def load_and_process_document(file_bytes: bytes, file_type: str) -> List[dict]:
    """
    Loads a document, splits it into chunks, and generates embeddings for each chunk.

    Args:
        file_bytes (bytes): The raw bytes content of the uploaded file.
        file_type (str): The type of the file (e.g., 'pdf', 'docx', 'txt').

    Returns:
        List[dict]: A list of dictionaries, where each dict contains 'text' and 'embedding'.
    """
    file_content = io.BytesIO(file_bytes)
    raw_text = ""

    if file_type == 'pdf':
        raw_text = _load_pdf(file_content)
    elif file_type == 'docx':
        raw_text = _load_docx(file_content)
    elif file_type == 'txt':
        raw_text = _load_txt(file_content)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    if not raw_text:
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.create_documents([raw_text])

    embeddings_model = OllamaEmbeddings(model=EMBEDDING_MODEL)

    processed_chunks = []
    for i, chunk in enumerate(chunks):
        embedding = embeddings_model.embed_query(chunk.page_content)
        processed_chunks.append({
            'text': chunk.page_content,
            'embedding': embedding,
            'chunk_id': i
        })
    return processed_chunks

@tool
def retrieve_context(question: str, document_chunks: List[dict]) -> str:
    """
    Retrieves the most relevant document chunks based on the question.

    Args:
        question (str): The user's question.
        document_chunks (List[dict]): A list of dictionaries, each containing 'text' and 'embedding'.

    Returns:
        str: A concatenated string of the most relevant text chunks.
    """
    if not document_chunks:
        return "No document loaded or processed to retrieve context from."

    embeddings_model = OllamaEmbeddings(model=EMBEDDING_MODEL)
    question_embedding = embeddings_model.embed_query(question)

    similarities = []
    for chunk in document_chunks:
        if isinstance(chunk['embedding'], list) and all(isinstance(x, (int, float)) for x in chunk['embedding']):
            similarity = sum(q_i * c_i for q_i, c_i in zip(question_embedding, chunk['embedding']))
            similarities.append((similarity, chunk['text']))
        else:
            print(f"Warning: Invalid embedding format for chunk: {chunk['embedding']}")

    similarities.sort(key=lambda x: x[0], reverse=True)
    top_k_chunks = [text for _, text in similarities[:TOP_K_RETRIEVAL]]

    context = "\n\n".join(top_k_chunks)
    return context if context else "No relevant context found."

@tool
def answer_question(question: str, context: str) -> str:
    """
    Generates an answer to the question based on the provided context.

    Args:
        question (str): The user's question.
        context (str): The retrieved context from the document.

    Returns:
        str: The generated answer.
    """
    llm = init_chat_model(CHAT_MODEL, model_provider='ollama')

    prompt = (
        f"You are an AI assistant specialized in answering questions based on provided document context. "
        f"Answer the following question truthfully and concisely, using ONLY the information from the context below. "
        f"If the answer cannot be found in the context, state that you don't have enough information.\n\n"
        f"Question: {question}\n\n"
        f"Context:\n{context}\n\n"
        f"Answer:"
    )
    response = llm.invoke(prompt).content
    return response

llm_with_tools = init_chat_model(CHAT_MODEL, model_provider='ollama')
llm_with_tools = llm_with_tools.bind_tools([retrieve_context, answer_question])

def llm_node(state: ChatState) -> dict:
    """
    Invokes the LLM with the current message history.
    """
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {'messages': messages + [response]}

def router(state: ChatState) -> str:
    """
    Determines the next step in the graph based on the LLM's response.
    """
    last_message = state['messages'][-1]
    if getattr(last_message, 'tool_calls', None):
        return "tools"
    return "end"

tool_node = ToolNode([retrieve_context, answer_question])

def tools_node(state: ChatState) -> dict:
    """
    Executes the tool called by the LLM.
    """
    
    last_message = state['messages'][-1]
    if getattr(last_message, 'tool_calls', None):
        for tool_call in last_message.tool_calls:
            if tool_call.get('function', {}).get('name') == 'retrieve_context':
                pass

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

# --- Main Entry Point for RAG Agent (Question Answering) ---
def process_rag_request(user_question: str, document_chunks: Optional[List[dict]] = None) -> str:
    """
    Processes a user question using the RAG agent graph.

    Args:
        user_question (str): The question from the user.
        document_chunks (Optional[List[dict]]): The pre-processed document chunks with embeddings.
                                                 This is crucial for the retrieve_context tool.

    Returns:
        str: The agent's final answer.
    """
    
    if document_chunks:
        initial_instruction = (
            f"The user has asked: '{user_question}'. "
            f"You have access to a document. First, use the 'retrieve_context' tool with the question to get relevant information from the document. "
            f"Then, use the 'answer_question' tool with the original question and the retrieved context to formulate a final answer."
        )
        initial_state = {
            'messages': [HumanMessage(content=user_question)],
            'document_chunks': document_chunks
        }
    else:
        return "Error: No document processed. Please upload and process a document first."

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
    return "No response from RAG agent."

