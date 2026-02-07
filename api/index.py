from flask import Flask, render_template, request, flash, redirect, url_for
import os
import sys

# Ensure ogctz_frontend is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ogctz_frontend'))

# Create the Flask app with proper paths pointing to ogctz_frontend
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'ogctz_frontend', 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'ogctz_frontend', 'static'),
    static_url_path='/static'
)

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
