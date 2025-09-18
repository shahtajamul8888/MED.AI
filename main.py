from flask import Flask, request, jsonify
import os
import time

app = Flask(__name__)

# ✅ Home route
@app.route('/')
def home():
    return jsonify({
        "message": "Flask app is running on Render 🚀",
        "status": "healthy",
        "timestamp": time.time()
    })

# ✅ Test route
@app.route('/api/hello')
def hello():
    name = request.args.get('name', 'Guest')
    return jsonify({
        "message": f"Hello, {name}!",
        "note": "This is a test API endpoint running on Render"
    })

# ✅ Example AI route (dummy for now)
@app.route('/api/ask', methods=['POST'])
def ask_ai():
    data = request.get_json()
    question = data.get("question", "")

    if not question:
        return jsonify({"error": "Question required"}), 400

    # ⚡ Yahan apna AI / OpenAI API call ka code add karna hoga
    answer = f"AI response for: {question}"

    return jsonify({"question": question, "answer": answer})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)