from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
OLLAMA_API_URL = 'http://localhost:11434/api/generate'  # adjust as needed


@app.route('/api/ollama', methods=['GET'])
def proxy_ollama():
    payload = {
        "model": "deepseek-r1:1.5b",
        "prompt": "What color is the sky at different times of the day?",
        "stream": False
    }
    # payload = request.get_json()
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        return jsonify(response.json())
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Ollama API error"}), 500


if __name__ == '__main__':
    app.run(port=3000)
