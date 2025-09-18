

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


---

📌 Procfile

web: gunicorn main:app


---

📌 requirements.txt

flask
gunicorn


---

⚡ Bas itna rakhna hai. Deploy kar → Render pe test kar:

/ pe → "Flask app is running on Render 🚀"

/api/hello?name=Tajamul pe → "Hello, Tajamul!"



---

👉 Ab tu bata: iske baad tu sirf test app chalana chahta hai ya apna bada wala AI project bhi isi main.py me dalna hai?

