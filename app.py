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
        "phone": "+255 700 000 000"
    }

@app.route("/")
def home():
    return render_template("index.html", title="Home")

@app.route("/projects")
def projects():
    return render_template("projects.html", title="Our Projects")

@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email")
    flash(f"Thanks for subscribing! ({email})", "success")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run()