import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app, origins=["https://bitcoiners.africa"])

# In-memory session storage
session_threads = {}

@app.route('/', methods=['GET'])
def health_check():
    return "Bitcoin Sidekick API - Operational"

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    try:
        data = request.get_json()
        user_message = data.get('message')
        user_id = data.get('user_id')

        if not user_message or not user_id:
            return jsonify({"error": "Message and user_id required"}), 400

        # Get or create thread
        thread_id = session_threads.get(user_id)
        if not thread_id:
            thread = openai.beta.threads.create()
            thread_id = thread.id
            session_threads[user_id] = thread_id

        # Add message to thread
        openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        # Process with Assistant
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id="asst_wXH9h4xeSZ3nmPZgjWqvRVfL"
        )

        # Poll for completion
        while True:
            status = openai.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if status.status == "completed":
                break
            if status.status in ["failed", "cancelled"]:
                return jsonify({"error": "Processing failed"}), 500

        # Get response
        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        bot_reply = next(
            (msg.content[0].text.value 
             for msg in messages.data 
             if msg.role == "assistant"), 
            "Could not generate response"
        )

        return jsonify({"reply": bot_reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
