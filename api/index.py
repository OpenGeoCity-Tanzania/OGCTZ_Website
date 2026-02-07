import sys
import os
from pathlib import Path

# Get absolute paths
project_root = Path(__file__).parent.parent
frontend_dir = project_root / "ogctz_frontend"

# Add frontend to path
sys.path.insert(0, str(frontend_dir))

# Important: Set Flask's template and static folders to point to ogctz_frontend
os.environ['FLASK_ENV'] = 'production'

# Import after path is set
from flask import Flask, render_template, request, flash, redirect, url_for

# Create Flask app with explicit template folder
app = Flask(__name__, 
            template_folder=str(frontend_dir / 'templates'),
            static_folder=str(frontend_dir / 'static'))

app.secret_key = "secret_key_for_session"

@app.context_processor
def inject_global_vars():
    return {
        "site_name": "OpenGeoCity Tanzania",
        "email": "info@ogctz.org",
        "phone": "+255 700 000 000"
    }

@app.route('/')
def home():
    return render_template('index.html', title="Home")

@app.route('/projects')
def projects():
    return render_template('projects.html', title="Our Projects")

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    flash(f"Thanks for subscribing! ({email})", "success")
    return redirect(url_for('home'))

# For Vercel serverless
if __name__ != "__main__":
    # Running on Vercel
    pass
