from flask import Flask, render_template, request, flash, redirect, url_for
import os

# Absolute path of current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(current_dir, "templates"),
    static_folder=os.path.join(current_dir, "static"),
    static_url_path="/static"
)

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
        "founded": "2021"
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

if __name__ == "__main__":
    app.run()