from dataclasses import dataclass
from typing import List, TypedDict
from flask import Flask, request, jsonify
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables import RunnableConfig
import requests


chats_by_session_id = {}


app = Flask(__name__)
OLLAMA_API_URL = 'http://localhost:11434/api/generate'

# Enable CORS (Cross-Origin Resource Sharing)


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    return response


model = "deepseek-r1:1.5b"

llm = ChatOllama(
    model=model,
    temperature=0,
)


def call_model(state: MessagesState, config: RunnableConfig) -> MessagesState:
    # Make sure that config is populated with the session id
    print(f"Config: {config}")
    if "configurable" not in config or "session_id" not in config["configurable"]:
        raise ValueError(
            "Make sure that the config includes the following information: {'configurable': {'session_id': 'some_value'}}"
        )

    # Fetch the history of messages and append to it any new messages.
    chat_history = get_chat_history(config["configurable"]["session_id"])
    # llm = config["configurable"]

    messages = list(chat_history.messages) + state["messages"]
    response = llm.invoke(messages)
    print(f"\nAI Response: {response}")

    main_response = response.content

    # Create a new message with the response content
    ai_message = type(response)(content=main_response)

    # Update the chat message history to include
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


def initialize_state_graph():
    # Define a new graph
    builder = StateGraph(state_schema=MessagesState)

    # Define the two nodes we will cycle between
    builder.add_edge(START, "model")
    builder.add_node("model", call_model)

    # Compile the graph
    graph = builder.compile()

    return graph


@app.route('/api/ollama', methods=['POST'])
def proxy_ollama():

    payload = request.json
    prompt = payload.get('prompt')
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    session_id = "1234"

    config = {
        "configurable": {
            "session_id": session_id,
        }
    }

    messages = MessagesState(
        messages=[
            (
                "system",
                "You are a helpful assistant that translates English to French. Translate the user sentence.",
            ),
            ("human", prompt),
        ]
    )

    call_model_graph = initialize_state_graph()

    # Stream the messages through the graph
    for event in call_model_graph.stream(messages, config, stream_mode="values"):
        print(f"Stream Event: {event}")

        latest_message = event["messages"][-1]

        # Only process AI messages
        if isinstance(latest_message, AIMessage):
            # Display AI message content
            print(latest_message.content)
            # console.print(Markdown(latest_message.content))

    return jsonify(latest_message.content)


if __name__ == '__main__':
    app.run(port=3000)
