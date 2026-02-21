# Load environment variables from .env file (for local development)
from dotenv import load_dotenv
load_dotenv()

## ...existing code...
from flask import Flask, render_template, request, flash, redirect, url_for, Response
import os
from authlib.integrations.flask_client import OAuth

# Absolute path of current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(current_dir, "templates"),
    static_folder=os.path.join(current_dir, "static"),
    static_url_path="/static"
)

# OAuth setup
oauth = OAuth(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')
app.config['GITHUB_CLIENT_ID'] = os.environ.get('GITHUB_CLIENT_ID', 'your-github-client-id')
app.config['GITHUB_CLIENT_SECRET'] = os.environ.get('GITHUB_CLIENT_SECRET', 'your-github-client-secret')

# OAuth setup - only register if credentials are available
if app.config['GOOGLE_CLIENT_ID'] and app.config['GOOGLE_CLIENT_SECRET']:
    google = oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
        client_kwargs={'scope': 'openid email profile'},
    )
else:
    google = None

if app.config['GITHUB_CLIENT_ID'] and app.config['GITHUB_CLIENT_SECRET']:
    github = oauth.register(
        name='github',
        client_id=app.config['GITHUB_CLIENT_ID'],
        client_secret=app.config['GITHUB_CLIENT_SECRET'],
        access_token_url='https://github.com/login/oauth/access_token',
        access_token_params=None,
        authorize_url='https://github.com/login/oauth/authorize',
        authorize_params=None,
        api_base_url='https://api.github.com/',
        userinfo_endpoint='https://api.github.com/user',
        client_kwargs={'scope': 'user:email'},
    )
else:
    github = None

# Secret key (use env variable on Vercel)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# Global variables for templates
@app.context_processor
def inject_global_vars():
    return {
        "site_name": "OpenGeoCity Tanzania",
        "email": "info@ogctz.org",
        "phone": "+255 700 000 000",
        "location": "Dodoma, Tanzania",
        "founded": "2021",
        # SEO defaults — can be overridden per-page by providing `page_description` or `page_keywords`
        "site_url": os.environ.get("SITE_URL", "https://opengeocity.org"),
        "default_description": "OpenGeoCity Tanzania — geospatial innovation, urban data and mapping for resilient cities.",
        "default_keywords": "OpenGeoCity, geospatial, GIS, mapping, Tanzania, urban planning, data",
        "twitter_handle": os.environ.get("TWITTER_HANDLE", "@OpenGeoCityTZ")
    }   

# Main Pages
@app.route("/")
def home():
    return render_template("index.html", page_title="Home")

@app.route("/about")
def about():
    return render_template("about.html", page_title="About Us")

@app.route("/services")
def services():
    return render_template("services.html", page_title="Our Services")

@app.route("/projects")
def projects():
    return render_template("projects.html", page_title="Our Projects")

@app.route("/team")
def team():
    return render_template("team.html", page_title="Our Team")

@app.route("/contact")
def contact():
    return render_template("contact.html", page_title="Contact Us")

@app.route("/resources")
def resources():
    return render_template("resources.html", page_title="Resources")

def gis_course():
    return render_template("gis_course/gis_course.html", page_title="GIS Fundamentals Guide")

# GIS Course Registration

# GIS Course Landing with OAuth
@app.route("/gis-course", methods=["GET"])
def gis_course():
    return render_template("gis_course/gis_course.html", page_title="GIS Fundamentals Guide")

@app.route("/gis-course/module-1", methods=["GET"])
def module_one():
    return render_template("gis_course/module_one.html", page_title="Module 1: GIS Fundamentals")

@app.route('/login/google')
def login_google():
    if not google:
        flash("Google OAuth is not configured.", "error")
        return redirect(url_for("home"))
    redirect_uri = url_for('authorize_google', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/login/github')
def login_github():
    if not github:
        flash("GitHub OAuth is not configured.", "error")
        return redirect(url_for("home"))
    redirect_uri = url_for('authorize_github', _external=True)
    return oauth.github.authorize_redirect(redirect_uri)

@app.route('/authorize/google')
def authorize_google():
    if not google:
        flash("Google OAuth is not configured.", "error")
        return redirect(url_for("home"))
    try:
        token = oauth.google.authorize_access_token()
        user = oauth.google.parse_id_token(token)
        # user contains: sub, name, email, picture, etc.
        # Here you would store user info and send email if needed
        return render_template("gis_course/register_success.html", page_title="Registration Successful", user=user)
    except Exception as e:
        print(f"Google OAuth error: {str(e)}")
        flash(f"Authentication failed: {str(e)}", "error")
        return redirect(url_for("gis_course"))

@app.route('/authorize/github')
def authorize_github():
    if not github:
        flash("GitHub OAuth is not configured.", "error")
        return redirect(url_for("home"))
    try:
        token = oauth.github.authorize_access_token()
        resp = oauth.github.get('user', token=token)
        user = resp.json()
        # user contains: login, id, name, email, etc.
        # Here you would store user info and send email if needed
        return render_template("gis_course/register_success.html", page_title="Registration Successful", user=user)
    except Exception as e:
        print(f"GitHub OAuth error: {str(e)}")
        flash(f"Authentication failed: {str(e)}", "error")
        return redirect(url_for("gis_course"))


# Sitemap and robots
@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    # list of site paths to include in sitemap
    paths = [
        '/',
        '/about',
        '/services',
        '/projects',
        '/team',
        '/contact',
        '/resources',
        '/gis-course'
    ]
    site_url = os.environ.get("SITE_URL", "https://ogctz.org")
    return render_template('sitemap.xml', paths=paths, site_url=site_url), 200, {'Content-Type': 'application/xml'}


@app.route('/robots.txt')
def robots_txt():
    site_url = os.environ.get("SITE_URL", "https://ogctz.org")
    txt = f"""User-agent: *
Disallow:

Sitemap: {site_url}/sitemap.xml
"""
    return Response(txt, mimetype='text/plain')

# API Routes
@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email")
    if email:
        flash(f"Thanks for subscribing with {email}!", "success")
    else:
        flash("Please enter a valid email address.", "error")
    return redirect(request.referrer or url_for("home"))

@app.route("/contact-submit", methods=["POST"])
def contact_submit():
    name = request.form.get("name")
    email = request.form.get("email")
    subject = request.form.get("subject")
    message = request.form.get("message")
    
    if name and email and message:
        flash(f"Thanks {name}! We received your message and will get back to you soon.", "success")
    else:
        flash("Please fill in all required fields.", "error")
    return redirect(url_for("contact"))

# WSGI entry point for Vercel serverless deployment
# This makes `app` available to Vercel's Python runtime without explicit export
if __name__ == "__main__":
    # For local development only
    app.run()