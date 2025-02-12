from flask import Flask, request, jsonify
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
import requests


app = Flask(__name__)
OLLAMA_API_URL = 'http://localhost:11434/api/generate'

# Enable CORS (Cross-Origin Resource Sharing)


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    return response


@app.route('/api/ollama', methods=['POST'])
def proxy_ollama():
    model = "deepseek-r1:1.5b"

    llm = ChatOllama(
        model=model,
        temperature=0,
    )

    payload = request.json
    prompt = payload.get('prompt')
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    messages = [
        (
            "system",
            "You are a helpful assistant that translates English to French. Translate the user sentence.",
        ),
        ("human", prompt),
    ]
    ai_msg = llm.invoke(messages)
    return jsonify(ai_msg.content)

    # try:
    #     # Send request to Ollama
    #     ollama_response = requests.post(
    #         OLLAMA_API_URL,
    #         json={
    #             'prompt': prompt,
    #             'model': model,
    #             'stream': False  # Adding this to ensure we get a complete response
    #         }
    #     )
    #     ollama_response.raise_for_status()  # Raise an error for bad responses
    #     return jsonify(ollama_response.json())
    # except requests.exceptions.RequestException as e:
    #     print(f"Error: {e}")
    #     return jsonify({"error": "Ollama API error"}), 500


if __name__ == '__main__':
    app.run(port=3000)
