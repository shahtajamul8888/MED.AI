from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import openai
import requests
import time
from functools import wraps
import logging
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# API keys from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Root route (important for Render)
@app.route('/')
def home():
    return jsonify({
        "message": "Medical AI Flask app running on Render 🚀",
        "status": "healthy",
        "timestamp": time.time()
    })

# Rate limiting decorator
def rate_limit(max_calls=60, period=60):
    calls = {}
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            now = time.time()
            key = request.remote_addr
            if key in calls:
                calls[key] = [call for call in calls[key] if call > now - period]
                if len(calls[key]) >= max_calls:
                    return jsonify({'error': 'Rate limit exceeded'}), 429
            else:
                calls[key] = []
            calls[key].append(now)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Query enhancer
def enhance_medical_query(query):
    return f"medical research healthcare {query}"

# ChatGPT API
def call_chatgpt(query):
    if not OPENAI_API_KEY:
        return None
    try:
        openai.api_key = OPENAI_API_KEY
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert medical research assistant."},
                {"role": "user", "content": enhance_medical_query(query)}
            ],
            max_tokens=800,
            temperature=0.3
        )
        return response.choices[0].message['content']
    except Exception as e:
        logger.error(f"ChatGPT API error: {e}")
        return None

# Perplexity API
def call_perplexity(query):
    if not PERPLEXITY_API_KEY:
        return None
    try:
        headers = {"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [
                {"role": "system", "content": "You are a medical research expert."},
                {"role": "user", "content": enhance_medical_query(query)}
            ],
            "max_tokens": 600,
            "temperature": 0.2,
            "top_p": 0.9,
        }
        response = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Perplexity API error: {e}")
        return None

# Google Search
def call_google_search(query):
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return None
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {'key': GOOGLE_API_KEY, 'cx': GOOGLE_CSE_ID, 'q': enhance_medical_query(query), 'num': 3}
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'items' in data:
                snippets = [item['snippet'] for item in data['items'][:2]]
                return ' '.join(snippets)[:400]
    except Exception as e:
        logger.error(f"Google Search API error: {e}")
        return None

# Combine responses
def aggregate_responses(chatgpt_response, perplexity_response, google_response):
    responses = []
    sources = []
    if chatgpt_response:
        responses.append(f"**AI Analysis:** {chatgpt_response}")
        sources.append("ChatGPT")
    if perplexity_response:
        responses.append(f"**Research Findings:** {perplexity_response}")
        sources.append("Perplexity AI")
    if google_response:
        responses.append(f"**Additional Context:** {google_response}")
        sources.append("Google Search")
    if not responses:
        return "Unable to retrieve medical information.", ""
    combined = "\n\n".join(responses)
    combined += "\n\n⚠️ Disclaimer: For educational purposes only. Consult professionals."
    return combined, f"Sources: {', '.join(sources)}"

# API endpoint
@app.route('/api/instant_answer')
@rate_limit(max_calls=30, period=60)
def instant_answer():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'answer': "Please provide a question.", 'source': ""})
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        chatgpt_result = executor.submit(call_chatgpt, query).result(timeout=8)
        perplexity_result = executor.submit(call_perplexity, query).result(timeout=8)
        google_result = executor.submit(call_google_search, query).result(timeout=5)
    answer, source = aggregate_responses(chatgpt_result, perplexity_result, google_result)
    return jsonify({'answer': answer, 'source': source, 'timestamp': time.time()})

# Health check
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': time.time(), 'version': '2.0.0'})

# Error handlers
@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({'error': 'Too many requests.'}), 429

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)