"""
MED.AI - Single-file Flask app for GitHub (app.py)

Files included (single file contains everything needed to run locally):
- app.py (this file)

Quick start:
1. Create a new GitHub repo and add this file as app.py
2. Create a Python 3.10+ virtualenv
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\Scripts\activate    # Windows
3. Install requirements:
   pip install -r requirements.txt
   (or: pip install flask sqlalchemy python-dotenv markdown)
4. Create DB and seed sample data:
   FLASK_APP=app.py flask init-db
5. Run locally:
   flask run

Notes about deploying on GitHub:
- GitHub Pages only serves static sites. To host this Flask app, use a platform like Render, Railway, Heroku, or a VM. You can keep the repo on GitHub and deploy with CI/CD.

This single-file app contains:
- lightweight article/resource model (SQLite + SQLAlchemy)
- simple browsing, search and JSON API
- admin route protected by ADMIN_TOKEN environment variable to add articles
- templates embedded with Flask's render_template_string for easy single-file distribution

"""

from flask import Flask, render_template_string, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime
import os
import markdown

# ---------------------- Configuration ----------------------
APP_NAME = "MED.AI"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.environ.get('MEDAI_DB', os.path.join(BASE_DIR, 'medai.db'))
ADMIN_TOKEN = os.environ.get('MEDAI_ADMIN_TOKEN', 'CHANGE_ME')  # set a secure token for production

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret')

db = SQLAlchemy(app)

# ---------------------- Models ----------------------
class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    slug = db.Column(db.String(300), unique=True, nullable=False)
    summary = db.Column(db.String(600), nullable=True)
    content_md = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(300), nullable=True)  # comma separated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'summary': self.summary,
            'tags': [t.strip() for t in (self.tags or '').split(',') if t.strip()],
            'created_at': self.created_at.isoformat()
        }

# ---------------------- Templates (single-file) ----------------------
base_template = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{{ title }} - {{ app_name }}</title>
  <style>
    body{font-family:Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; margin:0; padding:0; background:#f7fafc; color:#111}
    header{background:linear-gradient(90deg,#0066cc,#00aaff); color:white; padding:20px}
    .container{max-width:920px; margin:28px auto; padding:0 16px}
    .card{background:white; border-radius:12px; padding:18px; box-shadow:0 6px 18px rgba(29,31,33,0.06); margin-bottom:18px}
    a{color:#0666c6; text-decoration:none}
    .meta{color:#6b7280; font-size:14px}
    .search{display:flex; gap:8px}
    input[type=text]{flex:1; padding:8px 12px; border-radius:8px; border:1px solid #e5e7eb}
    button{padding:8px 12px; border-radius:8px; border:none; background:#0066cc; color:white}
    .tags{font-size:13px; color:#475569}
    footer{padding:18px; text-align:center; color:#6b7280}
    pre code{white-space:pre-wrap}
  </style>
</head>
<body>
  <header>
    <div class="container">
      <h1 style="margin:0">{{ app_name }}</h1>
      <div class="meta">Resources, articles and lightweight tools for medical researchers & healthcare professionals</div>
    </div>
  </header>
  <main class="container">
    {% block content %}{% endblock %}
  </main>
  <footer>
    <small>&copy; {{ year }} {{ app_name }} &middot; Built with ❤️ for research</small>
  </footer>
</body>
</html>
"""

index_template = """
{% extends 'base' %}
{% block content %}
  <div class="card">
    <form method="get" action="{{ url_for('index') }}" class="search">
      <input type="text" name="q" placeholder="Search articles, tags, or keywords" value="{{ q or '' }}">
      <button type="submit">Search</button>
    </form>
  </div>

  <div class="card">
    <h2>Featured articles</h2>
    {% for a in articles %}
      <div style="margin-bottom:12px">
        <a href="{{ url_for('article_detail', slug=a.slug) }}"><strong>{{ a.title }}</strong></a>
        <div class="meta">{{ a.created_at.strftime('%b %d, %Y') }} &middot; <span class="tags">{{ a.tags }}</span></div>
        <p>{{ a.summary }}</p>
      </div>
    {% else %}
      <p>No articles found.</p>
    {% endfor %}
  </div>

  <div class="card">
    <h3>Tools & Resources</h3>
    <ul>
      <li><a href="{{ url_for('api_articles') }}">API: /api/articles (JSON)</a> &mdash; machine-friendly list of articles</li>
      <li><a href="https://doi.org" target="_blank">DOI resolver</a> (external)</li>
      <li>Markdown-based article format for quick authoring</li>
    </ul>
  </div>
{% endblock %}
"""

article_template = """
{% extends 'base' %}
{% block content %}
  <div class="card">
    <h2>{{ article.title }}</h2>
    <div class="meta">Published {{ article.created_at.strftime('%b %d, %Y') }} &middot; Tags: {{ article.tags or '—' }}</div>
    <hr />
    <div>{{ content_html | safe }}</div>
  </div>

  <div class="card">
    <a href="{{ url_for('index') }}">&larr; Back to articles</a>
  </div>
{% endblock %}
"""

# ---------------------- Template registration ----------------------
# We register the base template in Flask's template loader via a small trick
from jinja2 import DictLoader
app.jinja_loader = DictLoader({'base': base_template, 'index.html': index_template, 'article.html': article_template})

# ---------------------- Utility functions ----------------------
def make_slug(title: str):
    slug = ''.join(c.lower() if c.isalnum() else '-' for c in title).strip('-')
    # collapse multiple dashes
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug[:250]

# ---------------------- CLI command to init DB ----------------------
@app.cli.command('init-db')
def init_db():
    """Initialize the database and seed sample articles."""
    db.create_all()
    if Article.query.count() == 0:
        sample_md = (
            '# Welcome to MED.AI\n\n'
            'This sample article shows how to write research-focused content using Markdown.\n\n'
            '## Summary\n\n'
            'Short summary for busy clinicians and researchers.\n\n'
            '## References\n\n'
            '- Example: Smith J et al., *Journal of Examples*, 2024.'
        )
        a1 = Article(title='Introducing MED.AI — resources for researchers', slug=make_slug('Introducing MED.AI — resources for researchers'), summary='Overview of MED.AI and how researchers can contribute.', content_md=sample_md, tags='platform,announcement')
        a2 = Article(title='How to write a reproducible methods section', slug=make_slug('How to write a reproducible methods section'), summary='Practical steps to improve reproducibility in clinical research.', content_md='# Reproducible methods\n\nDetailed guidance...', tags='research,methods')
        db.session.add_all([a1, a2])
        db.session.commit()
        print('Seeded database with sample articles.')
    print('Database initialized at', DB_PATH)

# ---------------------- Routes ----------------------
@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    articles = Article.query.order_by(Article.created_at.desc())
    if q:
        # simple full-text-ish search on title, summary, content_md and tags
        like = f"%{q}%"
        articles = articles.filter(
            (Article.title.ilike(like)) | (Article.summary.ilike(like)) | (Article.content_md.ilike(like)) | (Article.tags.ilike(like))
        )
    articles = articles.limit(20).all()
    return render_template_string(index_template, title='Home', app_name=APP_NAME, articles=articles, q=q, year=datetime.utcnow().year)

@app.route('/articles/<slug>')
def article_detail(slug):
    article = Article.query.filter_by(slug=slug).first_or_404()
    content_html = markdown.markdown(article.content_md, extensions=['fenced_code', 'tables', 'toc'])
    return render_template_string(article_template, title=article.title, app_name=APP_NAME, article=article, content_html=content_html, year=datetime.utcnow().year)

# Simple JSON API
@app.route('/api/articles')
def api_articles():
    tag = request.args.get('tag')
    query = Article.query.order_by(Article.created_at.desc())
    if tag:
        like = f"%{tag}%"
        query = query.filter(Article.tags.ilike(like))
    items = [a.to_dict() for a in query.limit(200).all()]
    return jsonify({'count': len(items), 'items': items})

# Admin: add article via POST (protected by ADMIN_TOKEN)
@app.route('/admin/add', methods=['GET','POST'])
def admin_add():
    token = request.args.get('token') or request.headers.get('X-Admin-Token')
    if token != ADMIN_TOKEN:
        abort(401, 'Unauthorized')
    if request.method == 'GET':
        return jsonify({'message': 'POST title, content_md, summary (optional), tags (comma separated) as JSON or form-data'})
    data = request.get_json() or request.form
    title = data.get('title')
    content_md = data.get('content_md')
    if not title or not content_md:
        abort(400, 'missing title or content_md')
    slug = make_slug(title)
    # ensure unique slug
    base = slug
    i = 1
    while Article.query.filter_by(slug=slug).first():
        slug = f"{base}-{i}"
        i += 1
    article = Article(title=title, slug=slug, content_md=content_md, summary=data.get('summary'), tags=data.get('tags'))
    db.session.add(article)
    db.session.commit()
    return jsonify({'message': 'created', 'article': article.to_dict()}), 201

# Healthcheck
@app.route('/.well-known/health')
def health():
    return jsonify({'status': 'ok', 'app': APP_NAME})

# ---------------------- Error handlers ----------------------
@app.errorhandler(401)
def unauthorized(e):
    return jsonify({'error': 'unauthorized', 'message': str(e)}), 401

@app.errorhandler(404)
def not_found(e):
    return render_template_string("""
    {% extends 'base' %}
    {% block content %}
      <div class='card'><h3>Not found</h3><p>The requested resource was not found.</p><a href='{{ url_for('index') }}'>Home</a></div>
    {% endblock %}
    """, title='Not Found', app_name=APP_NAME, year=datetime.utcnow().year), 404

# ---------------------- Run ----------------------
if __name__ == '__main__':
    # quick dev run
    # ensure DB exists
    if not os.path.exists(DB_PATH):
        with app.app_context():
            db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
