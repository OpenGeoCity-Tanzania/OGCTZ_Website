from flask import Flask, render_template, request, flash, redirect, url_for
import os

# Get the directory where this app.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Create Flask app with explicit template and static folder paths
app = Flask(
    __name__,
    template_folder=os.path.join(current_dir, 'templates'),
    static_folder=os.path.join(current_dir, 'static'),
    static_url_path='/static'
)

app.secret_key = "secret_key_for_session"  # Required for flash messages

# Context processor to make variables available in all templates
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

# Mock route for Newsletter form
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    # Logic to save email would go here
    flash(f"Thanks for subscribing! ({email})", "success")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)