from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import openai
import requests
import json
import time
from functools import wraps
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Configure CORS properly for production

# API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
SERPER_API_KEY = os.getenv('SERPER_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

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

def enhance_medical_query(query):
    """Enhance the query for better medical search results"""
    medical_terms = [
        "evidence-based", "clinical guidelines", "medical research",
        "peer-reviewed", "healthcare", "treatment", "diagnosis"
    ]
    
    # Add medical context to improve search relevance
    enhanced_query = f"medical research healthcare {query}"
    return enhanced_query

def call_chatgpt(query):
    """Call OpenAI GPT for medical information"""
    if not OPENAI_API_KEY:
        return None
    
    try:
        openai.api_key = OPENAI_API_KEY
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": """You are an expert medical research assistant. Provide accurate, evidence-based medical information. Always include disclaimers about consulting healthcare professionals. Focus on peer-reviewed research and established medical guidelines."""
                },
                {"role": "user", "content": enhance_medical_query(query)}
            ],
            max_tokens=800,
            temperature=0.3  # Lower temperature for more factual responses
        )
        return response.choices[0].message['content']
    except Exception as e:
        logger.error(f"ChatGPT API error: {e}")
        return None

def call_perplexity(query):
    """Call Perplexity API for research-based answers"""
    if not PERPLEXITY_API_KEY:
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a medical research expert. Provide evidence-based answers with citations."
                },
                {
                    "role": "user", 
                    "content": enhance_medical_query(query)
                }
            ],
            "max_tokens": 600,
            "temperature": 0.2,
            "top_p": 0.9,
            "search_domain_filter": ["pubmed.ncbi.nlm.nih.gov", "who.int", "cdc.gov", "nih.gov"]
        }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        
    except Exception as e:
        logger.error(f"Perplexity API error: {e}")
        return None

def call_google_search(query):
    """Call Google Custom Search for medical information"""
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return None
    
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_CSE_ID,
            'q': enhance_medical_query(query),
            'num': 3,
            'safe': 'high'
        }
        
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'items' in data:
                snippets = [item['snippet'] for item in data['items'][:2]]
                return ' '.join(snippets)[:400]
                
    except Exception as e:
        logger.error(f"Google Search API error: {e}")
        return None

def aggregate_responses(chatgpt_response, perplexity_response, google_response):
    """Intelligently combine responses from multiple sources"""
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
        sources.append("Google Scholar")
    
    if not responses:
        return "Unable to retrieve medical information at this time. Please try again later.", ""
    
    # Combine responses intelligently
    combined = "\n\n".join(responses)
    combined += "\n\n**⚠️ Medical Disclaimer:** This information is for educational purposes only. Always consult qualified healthcare professionals for medical advice, diagnosis, or treatment."
    
    source_text = f"Sources: {', '.join(sources)}"
    
    return combined, source_text

@app.route('/api/instant_answer')
@rate_limit(max_calls=30, period=60)
def instant_answer():
    """Enhanced instant answer endpoint with multiple AI sources"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'answer': "Please provide a medical question.", 'source': ""})
    
    if len(query) < 3:
        return jsonify({'answer': "Please provide a more detailed question.", 'source': ""})
    
    # Call multiple AI services in parallel using threading for better performance
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        chatgpt_future = executor.submit(call_chatgpt, query)
        perplexity_future = executor.submit(call_perplexity, query)
        google_future = executor.submit(call_google_search, query)
        
        # Get results with timeout
        try:
            chatgpt_result = chatgpt_future.result(timeout=8)
            perplexity_result = perplexity_future.result(timeout=8)
            google_result = google_future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            chatgpt_result = None
            perplexity_result = None
            google_result = None
    
    answer, source = aggregate_responses(chatgpt_result, perplexity_result, google_result)
    
    return jsonify({
        'answer': answer,
        'source': source,
        'timestamp': time.time()
    })

@app.route('/api/generate_image')
@rate_limit(max_calls=10, period=60)
def generate_image():
    """Generate medical illustrations using DALL-E"""
    query = request.args.get('q', '').strip()
    if not query or not OPENAI_API_KEY:
        return jsonify({'image_url': ""})
    
    try:
        # Enhanced prompt for medical illustrations
        medical_prompt = f"Professional medical illustration of {query}, anatomically accurate, educational style, clean background, detailed diagram, medical textbook quality"
        
        response = openai.Image.create(
            prompt=medical_prompt,
            n=1,
            size="512x512",
            quality="standard",
            style="natural"
        )
        
        image_url = response['data'][0]['url']
        return jsonify({'image_url': image_url})
        
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        return jsonify({'image_url': ""})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '2.0.0'
    })

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({'error': 'Too many requests. Please try again later.'}), 429

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Production-ready configuration
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
