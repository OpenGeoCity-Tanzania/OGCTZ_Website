import sys
import os

# Set up paths for Vercel serverless
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
frontend_dir = os.path.join(project_root, 'ogctz_frontend')

# Add to Python path
if frontend_dir not in sys.path:
    sys.path.insert(0, frontend_dir)

# Configure Flask
from flask import Flask, render_template, request, flash, redirect, url_for

# Create Flask app with correct paths
app = Flask(
    __name__,
    template_folder=os.path.join(frontend_dir, 'templates'),
    static_folder=os.path.join(frontend_dir, 'static'),
    static_url_path='/static'
)

app.config['JSON_SORT_KEYS'] = False
app.secret_key = "secret_key_for_session"

# Context processor
@app.context_processor
def inject_global_vars():
    return {
        "site_name": "OpenGeoCity Tanzania",
        "email": "info@ogctz.org",
        "phone": "+255 700 000 000"
    }

# Routes
@app.route('/', methods=['GET'])
def home():
    try:
        return render_template('index.html', title="Home")
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/projects', methods=['GET'])
def projects():
    try:
        return render_template('projects.html', title="Our Projects")
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/subscribe', methods=['POST'])
def subscribe():
    try:
        email = request.form.get('email')
        flash(f"Thanks for subscribing! ({email})", "success")
        return redirect(url_for('home'))
    except Exception as e:
        return f"Error: {str(e)}", 500

# Health check route
@app.route('/api/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

