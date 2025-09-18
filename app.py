from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "MED.AI Flask Backend Running 🚀"

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    # Simple chatbot logic
    if "fever" in user_message.lower():
        reply = "It seems you have fever 🤒. Please take rest and drink plenty of fluids."
    elif "headache" in user_message.lower():
        reply = "For headache, stay hydrated and take proper rest."
    elif "hello" in user_message.lower():
        reply = "Hello 👋, I am MED.AI. How can I help you today?"
    else:
        reply = f"You said: {user_message}. MED.AI will soon analyze this with AI 🧠."

    return jsonify({"reply": reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)