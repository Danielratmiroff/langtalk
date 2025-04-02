from dataclasses import dataclass
from typing import List, TypedDict, Dict, Optional, Any
from flask import Flask, Response, request, jsonify, stream_with_context
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, AIMessageChunk, SystemMessage
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.outputs import ChatResult
import requests
import os


chats_by_session_id = {}


app = Flask(__name__)
OLLAMA_API_URL = 'http://localhost:11434/api/generate'

# Enable CORS (Cross-Origin Resource Sharing)


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET')
    return response


model = "deepseek-r1:1.5b"

llm = ChatOllama(
    model=model,
    temperature=0,
    stream=True,
)


def validate_messages(messages: List[Dict[str, str]]) -> None:
    """Validate that messages are properly formatted."""
    if not isinstance(messages, list):
        raise ValueError("Messages must be a list")
    for message in messages:
        if not isinstance(message, dict) or "role" not in message or "content" not in message:
            raise ValueError(
                "Each message must be a dict with 'role' and 'content' keys")


class GeminiClient:
    """A client for interacting with Google's Gemini model via LangChain."""

    def __init__(
        self,
        model: str = "gemini-pro",
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        max_output_tokens: int = 8000,
        callback_manager: Optional[Any] = None,
        stream: bool = True,
    ):
        """
        Initialize the Gemini client.

        Args:
            model: The name of the Gemini model to use
            temperature: Controls randomness in responses
            top_p: Nucleus sampling parameter
            top_k: Number of tokens to consider for sampling
            max_output_tokens: Maximum number of tokens to generate
            callback_manager: Optional callback manager for logging and monitoring
            stream: Whether to stream the response
        """
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key must be provided through the GOOGLE_API_KEY environment variable"
            )

        self.llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=self.api_key,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_output_tokens,
            callback_manager=callback_manager,
            streaming=stream,
        )

    def get_chat_completion(
        self,
        messages: List[BaseMessage],
        **kwargs: Any,
    ) -> Any:
        """
        Chat method.

        Args:
            messages: The messages to send to the model
            **kwargs: Additional keyword arguments to pass to the model

        Returns:
            Model's response
        """
        try:
            response = self.llm.invoke(
                messages,
                **kwargs,
            )
            return response
        except Exception as e:
            raise Exception(f"Error while communicating with Gemini: {str(e)}")


def call_model(state: MessagesState, config: RunnableConfig) -> MessagesState:
    # Make sure that config is populated with the session id
    # print(f"Config: {config}")
    if "configurable" not in config or "session_id" not in config["configurable"]:
        raise ValueError(
            "Make sure that the config includes the following information: {'configurable': {'session_id': 'some_value'}}"
        )

    # Fetch the history of messages and append to it any new messages.
    chat_history = get_chat_history(config["configurable"]["session_id"])
    # llm = config["configurable"]

    messages = list(chat_history.messages) + state["messages"]
    response = llm.invoke(messages)
    # print(f"\nAI Response: {response}")
    print(f"log: {response}")

    main_response = response.content

    # Create a new message with the response content
    ai_message = type(response)(content=main_response)

    # Update the chat message history to include
    chat_history.add_messages(state["messages"] + [ai_message])

    return {
        "messages": [ai_message],
    }


def call_gemini_model(state: MessagesState, config: RunnableConfig) -> MessagesState:
    if "configurable" not in config or "session_id" not in config["configurable"]:
        raise ValueError(
            "Make sure that the config includes the following information: {'configurable': {'session_id': 'some_value'}}"
        )

    # Fetch the history of messages and append to it any new messages.
    chat_history = get_chat_history(config["configurable"]["session_id"])
    gemini_client = config["configurable"].get("gemini_client")

    if not gemini_client:
        raise ValueError("gemini_client must be provided in the config")

    messages = list(chat_history.messages) + state["messages"]
    response = gemini_client.get_chat_completion(messages)
    print(f"log: {response}")

    main_response = response.content

    # Create a new message with the response content
    ai_message = type(response)(content=main_response)

    # Update the chat message history
    chat_history.add_messages(state["messages"] + [ai_message])

    return {
        "messages": [ai_message],
    }


def get_chat_history(session_id: str) -> InMemoryChatMessageHistory:
    chat_history = chats_by_session_id.get(session_id)
    if chat_history is None:
        chat_history = InMemoryChatMessageHistory()
        chats_by_session_id[session_id] = chat_history
    return chat_history


def initialize_state_graph(model_function):
    # Define a new graph
    builder = StateGraph(state_schema=MessagesState)

    # Define the two nodes we will cycle between
    builder.add_edge(START, "model")
    builder.add_node("model", model_function)

    # Compile the graph
    graph = builder.compile()

    return graph


@app.route('/api/ollama', methods=['GET'])
def proxy_ollama():

    prompt = request.args.get('prompt')
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    session_id = "1234"

    def generate():
        config = {
            "configurable": {
                "session_id": session_id,
            }
        }

        messages = MessagesState(
            messages=[
                (
                    "system",
                    "You are a helpful chat assistant.",
                ),
                ("human", prompt),
            ]
        )

        call_model_graph = initialize_state_graph(call_model)

        for event in call_model_graph.stream(messages, config, stream_mode="messages"):
            # print(f"chunk: {event}")
            if isinstance(event, tuple) and isinstance(event[0], AIMessageChunk):
                chunk = event[0].content
                print(f"yow chunck: {chunk}")
                yield f"data: {chunk}\n\n"

        # Signal the end of the stream
        yield f"data: [DONE]\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')
    # return jsonify(latest_message.content)


@app.route('/api/gemini', methods=['GET'])
def proxy_gemini():
    prompt = request.args.get('prompt')
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    session_id = "gemini_1234"

    def generate():
        # Initialize Gemini client with streaming enabled
        gemini_client = GeminiClient(
            model="gemini-pro",
            temperature=0.7,
            stream=True
        )

        config = {
            "configurable": {
                "session_id": session_id,
                "gemini_client": gemini_client
            }
        }

        messages = MessagesState(
            messages=[
                (
                    "system",
                    "You are a helpful chat assistant powered by Google's Gemini model.",
                ),
                ("human", prompt),
            ]
        )

        call_model_graph = initialize_state_graph(call_gemini_model)

        for event in call_model_graph.stream(messages, config, stream_mode="messages"):
            if isinstance(event, tuple) and isinstance(event[0], AIMessageChunk):
                chunk = event[0].content
                print(f"gemini chunk: {chunk}")
                yield f"data: {chunk}\n\n"

        # Signal the end of the stream
        yield f"data: [DONE]\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(port=3000)
