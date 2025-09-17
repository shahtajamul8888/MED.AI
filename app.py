from flask import Flask, request, jsonify
import os
import time

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Flask app is running on Render 🚀",
        "status": "healthy",
        "timestamp": time.time()
    })

@app.route('/api/hello')
def hello():
    name = request.args.get('name', 'Guest')
    return jsonify({
        "message": f"Hello, {name}!",
        "note": "This is a test API endpoint running on Render"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)