# Load environment variables from .env file (for local development)
from dotenv import load_dotenv
load_dotenv()

## ...existing code...
from flask import Flask, render_template, request, flash, redirect, url_for, Response, session
import os
import time
import urllib.request
import json
from authlib.integrations.flask_client import OAuth
import random

# ── YouTube live feed helpers ─────────────────────────────────────────────────
_yt_cache = {"videos": [], "fetched_at": 0}
YT_CACHE_TTL = 1800  # 30 minutes

def fetch_youtube_videos(max_results=12):
    """Fetch latest videos from the channel using YouTube Data API v3."""
    global _yt_cache
    now = time.time()
    if _yt_cache["videos"] and (now - _yt_cache["fetched_at"]) < YT_CACHE_TTL:
        return _yt_cache["videos"]

    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    channel_id = os.environ.get("YOUTUBE_CHANNEL_ID", "")
    if not api_key or not channel_id:
        return []

    try:
        url = (
            f"https://www.googleapis.com/youtube/v3/search"
            f"?key={api_key}&channelId={channel_id}"
            f"&part=snippet&order=date&type=video&maxResults={max_results}"
        )
        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json.loads(resp.read().decode())

        videos = []
        for item in data.get("items", []):
            vid_id = item["id"].get("videoId", "")
            snip = item["snippet"]
            videos.append({
                "id": vid_id,
                "title": snip.get("title", ""),
                "description": snip.get("description", ""),
                "thumbnail": snip.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "published": snip.get("publishedAt", "")[:10],
                "url": f"https://www.youtube.com/watch?v={vid_id}",
            })

        _yt_cache["videos"] = videos
        _yt_cache["fetched_at"] = now
        return videos
    except Exception:
        return _yt_cache["videos"] or []

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
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
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

# Quiz Questions Database
MODULE_ONE_QUESTIONS = [
    {
        'id': 'q1',
        'text': 'What is a datum in geodesy?',
        'options': [
            {'label': 'A smooth mathematical surface that approximates the geoid', 'value': 'a'},
            {'label': 'A specific version of an ellipsoid anchored to Earth for regional accuracy', 'value': 'b'},
            {'label': 'The geographic coordinate system for Earth', 'value': 'c'},
            {'label': 'A method of simplifying map data', 'value': 'd'},
        ],
        'correct': 'b'
    },
    {
        'id': 'q2',
        'text': 'WGS84 is used globally because:',
        'options': [
            {'label': 'Its center is anchored at a local point for maximum accuracy', 'value': 'a'},
            {'label': 'Its center is Earth\'s center of mass, making it good for the whole planet and used by GPS', 'value': 'b'},
            {'label': 'It\'s the oldest datum still in use', 'value': 'c'},
            {'label': 'It eliminates the need for coordinate transformations', 'value': 'd'},
        ],
        'correct': 'b'
    },
    {
        'id': 'q3',
        'text': 'What is the main difference between Geographic Coordinate Systems (GCS) and Projected Coordinate Systems (PCS)?',
        'options': [
            {'label': 'GCS uses degrees, PCS uses meters; GCS is spherical, PCS is planar', 'value': 'a'},
            {'label': 'GCS is more accurate than PCS', 'value': 'b'},
            {'label': 'PCS is only used for local mapping', 'value': 'c'},
            {'label': 'GCS cannot be used with GPS data', 'value': 'd'},
        ],
        'correct': 'a'
    },
    {
        'id': 'q4',
        'text': 'Tanzania spans which two UTM zones?',
        'options': [
            {'label': 'UTM Zone 35S and 36S', 'value': 'a'},
            {'label': 'UTM Zone 36S and 37S', 'value': 'b'},
            {'label': 'UTM Zone 37S and 38S', 'value': 'c'},
            {'label': 'Tanzania only uses one UTM zone', 'value': 'd'},
        ],
        'correct': 'b'
    },
    {
        'id': 'q5',
        'text': 'Which data model is best for representing continuous phenomena like elevation or temperature?',
        'options': [
            {'label': 'Vector (points, lines, polygons)', 'value': 'a'},
            {'label': 'Raster (grid of pixels)', 'value': 'b'},
            {'label': 'Only attribute tables', 'value': 'c'},
            {'label': 'Topological networks', 'value': 'd'},
        ],
        'correct': 'b'
    },
    {
        'id': 'q6',
        'text': 'In vector data, which geometry type would you use to represent a forest?',
        'options': [
            {'label': 'Point', 'value': 'a'},
            {'label': 'Line', 'value': 'b'},
            {'label': 'Polygon', 'value': 'c'},
            {'label': 'All of the above depending on scale', 'value': 'd'},
        ],
        'correct': 'c'
    },
    {
        'id': 'q7',
        'text': 'What is the relationship between spatial data and attribute data in GIS?',
        'options': [
            {'label': 'They are the same thing', 'value': 'a'},
            {'label': 'Spatial shows location; attribute shows properties. A unique ID links them via a table', 'value': 'b'},
            {'label': 'Only spatial data is used in professional GIS', 'value': 'c'},
            {'label': 'Attribute data is unnecessary for GIS analysis', 'value': 'd'},
        ],
        'correct': 'b'
    },
    {
        'id': 'q8',
        'text': 'What is map generalization?',
        'options': [
            {'label': 'The process of creating maps that work for all purposes', 'value': 'a'},
            {'label': 'Simplifying data for display at smaller scales (selection, simplification, aggregation)', 'value': 'b'},
            {'label': 'Adding more detail to maps', 'value': 'c'},
            {'label': 'A method of error correction', 'value': 'd'},
        ],
        'correct': 'b'
    },
    {
        'id': 'q9',
        'text': 'Why would you use a projected coordinate system (like UTM) instead of a geographic coordinate system (lat/lon) for measuring distances?',
        'options': [
            {'label': 'Projected systems use meters, allowing accurate distance measurements on a flat map', 'value': 'a'},
            {'label': 'Geographic systems cannot measure distances', 'value': 'b'},
            {'label': 'Projected systems are always more accurate', 'value': 'c'},
            {'label': 'They give the same results; the choice doesn\'t matter', 'value': 'd'},
        ],
        'correct': 'a'
    },
    {
        'id': 'q10',
        'text': 'A large-scale map (e.g., 1:1,000) shows _____, while a small-scale map (e.g., 1:1,000,000) shows _____:',
        'options': [
            {'label': 'A small area with great detail; a large area with minimal detail', 'value': 'a'},
            {'label': 'A large area with great detail; a small area with minimal detail', 'value': 'b'},
            {'label': 'The same area but different projections', 'value': 'c'},
            {'label': 'Different datums for the same area', 'value': 'd'},
        ],
        'correct': 'a'
    },
]

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
    youtube_videos = fetch_youtube_videos()
    return render_template("resources.html", page_title="Resources", youtube_videos=youtube_videos)

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

@app.route("/gis-course/module-1/quiz", methods=["GET"])
def module_one_quiz():
    # Randomize questions for this session
    shuffled_questions = MODULE_ONE_QUESTIONS.copy()
    random.shuffle(shuffled_questions)
    
    # Store shuffled questions in session
    session['quiz_questions'] = shuffled_questions
    
    return render_template("gis_course/module_one_quiz.html", page_title="Module 1 Quiz", questions=shuffled_questions)

@app.route("/gis-course/module-1/quiz/submit", methods=["POST"])
def module_one_quiz_submit():
    try:
        # Create answer key from original questions
        answer_key = {q['id']: q['correct'] for q in MODULE_ONE_QUESTIONS}
        
        # Score the quiz
        score = 0
        results = {}
        
        for question in MODULE_ONE_QUESTIONS:
            q_id = question['id']
            user_answer = request.form.get(q_id)
            correct_answer = answer_key[q_id]
            is_correct = user_answer == correct_answer
            
            results[q_id] = {
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'question_text': question['text']
            }
            
            if is_correct:
                score += 1
        
        percentage = (score / len(MODULE_ONE_QUESTIONS)) * 100
        passed = percentage >= 70
        
        print(f"Quiz submitted - Score: {score}/{len(MODULE_ONE_QUESTIONS)}, Percentage: {percentage}%, Passed: {passed}")
        
        # Clear quiz questions from session
        session.pop('quiz_questions', None)
        
        return render_template(
            "gis_course/module_one_quiz_results.html",
            page_title="Quiz Results",
            score=score,
            total=len(MODULE_ONE_QUESTIONS),
            percentage=percentage,
            passed=passed,
            results=results
        )
    except Exception as e:
        print(f"Quiz submission error: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Error submitting quiz: {str(e)}", "error")
        return redirect(url_for("module_one_quiz"))

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
        # In OpenID Connect flow, user info is in the token's id_token
        user = token.get('userinfo')
        if not user:
            # Fallback: fetch from userinfo endpoint
            resp = oauth.google.get('userinfo', token=token)
            user = resp.json()
        
        # Store user info in session
        session['user'] = {
            'name': user.get('name', 'User'),
            'email': user.get('email'),
            'picture': user.get('picture')
        }
        
        print(f"Google OAuth successful for user: {user.get('email')}")
        # user contains: sub, name, email, picture, etc.
        # Here you would store user info and send email if needed
        success_page = render_template("gis_course/register_success.html", page_title="Registration Successful", user=user)
        print(f"Rendered register_success.html successfully")
        return success_page
    except Exception as e:
        print(f"Google OAuth error: {str(e)}")
        import traceback
        traceback.print_exc()
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
        
        # Store user info in session
        session['user'] = {
            'name': user.get('name') or user.get('login', 'User'),
            'email': user.get('email'),
            'picture': user.get('avatar_url')
        }
        
        # user contains: login, id, name, email, avatar_url, etc.
        # Here you would store user info and send email if needed
        return render_template("gis_course/register_success.html", page_title="Registration Successful", user=user)
    except Exception as e:
        print(f"GitHub OAuth error: {str(e)}")
        flash(f"Authentication failed: {str(e)}", "error")
        return redirect(url_for("gis_course"))


# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('gis_course'))


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