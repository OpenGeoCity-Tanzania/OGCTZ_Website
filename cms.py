# Content Management System (CMS) for OpenGeoCity Tanzania
# Provides: admin auth, blog posts, image uploads, and editable page blocks

from datetime import datetime
import os
import re
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from flask import current_app

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

# ── Models ────────────────────────────────────────────────────────────────────

class AdminUser(UserMixin, db.Model):
    __tablename__ = "admin_users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="editor", nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ROLES = ["superadmin", "admin", "editor"]

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_superadmin(self):
        return self.role == "superadmin" and self.is_active

    def is_admin(self):
        return self.role in ("superadmin", "admin") and self.is_active

    def can_manage_users(self):
        return self.is_superadmin()

    def can_manage_content(self):
        return self.role in ("superadmin", "admin", "editor") and self.is_active


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    excerpt = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    featured_image = db.Column(db.String(300), nullable=True)
    author = db.Column(db.String(100), nullable=True)
    tags = db.Column(db.String(300), nullable=True)  # comma-separated tags
    meta_title = db.Column(db.String(200), nullable=True)
    meta_description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="draft")  # draft, published, scheduled
    published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)
    scheduled_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<BlogPost {self.slug}>"

    @property
    def read_time(self):
        """Estimate reading time in minutes (200 words/min)."""
        words = len(re.findall(r"\w+", self.content or ""))
        return max(1, round(words / 200))

    @property
    def tag_list(self):
        """Return list of normalized tags."""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def is_visible(self):
        """A post is publicly visible when published and (not scheduled or schedule reached)."""
        if not self.published or self.status != "published":
            return False
        if self.scheduled_at and self.scheduled_at > datetime.utcnow():
            return False
        return True


class CMSImage(db.Model):
    __tablename__ = "cms_images"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    original_filename = db.Column(db.String(300), nullable=False)
    alt_text = db.Column(db.String(300), nullable=True)
    folder = db.Column(db.String(100), default="general")
    file_size = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def url(self):
        return f"/static/uploads/{self.folder}/{self.filename}"

    @property
    def filepath(self):
        return os.path.join("static", "uploads", self.folder, self.filename)


class SiteContent(db.Model):
    """Editable text blocks referenced by a unique key and page."""
    __tablename__ = "site_content"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False)
    page = db.Column(db.String(50), nullable=False, default="global")
    label = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False, default="")
    content_type = db.Column(db.String(20), default="text")  # text, html, markdown
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("key", "page", name="uix_content_key_page"),)

    def __repr__(self):
        return f"<SiteContent {self.page}.{self.key}>"


# ── User loader ─────────────────────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))


# ── Helpers ───────────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}


def parse_scheduled_datetime(value):
    """Parse a datetime-local string (YYYY-MM-DDTHH:MM) to datetime or None."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def slugify(value, max_length=200):
    value = re.sub(r"[^\w\s-]", "", value.lower()).strip()
    value = re.sub(r"[\s-]+", "-", value)
    return value[:max_length]


def make_unique_slug(title, existing_id=None):
    base = slugify(title)
    slug = base
    counter = 1
    while True:
        query = BlogPost.query.filter_by(slug=slug)
        if existing_id:
            query = query.filter(BlogPost.id != existing_id)
        if not query.first():
            return slug
        slug = f"{base}-{counter}"
        counter += 1


def unique_filename(original):
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else "jpg"
    return f"{uuid.uuid4().hex[:12]}.{ext}"


def save_uploaded_file(file, folder="general"):
    """Save an uploaded file to static/uploads/<folder> and return filename."""
    if not file or not allowed_file(file.filename):
        return None

    filename = secure_filename(file.filename)
    new_filename = unique_filename(filename)
    upload_dir = os.path.join(current_app.root_path, "static", "uploads", folder)
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, new_filename)
    file.save(filepath)
    return new_filename


def get_or_create_content(key, page="global", default="", label=None, content_type="text"):
    """Get a SiteContent block; create it if missing."""
    item = SiteContent.query.filter_by(key=key, page=page).first()
    if item is None:
        item = SiteContent(key=key, page=page, content=default, label=label or key, content_type=content_type)
        db.session.add(item)
        db.session.commit()
    return item


def get_content(key, page="global", default=""):
    """Get content value for a given key/page."""
    item = SiteContent.query.filter_by(key=key, page=page).first()
    return item.content if item else default


def create_admin_user(username, password, email=None, role="editor"):
    """Create an admin user. Defaults to editor; first setup should be superadmin."""
    if AdminUser.query.filter_by(username=username).first():
        return False
    role = role if role in AdminUser.ROLES else "editor"
    user = AdminUser(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return True


def init_cms(app):
    """Bind CMS extensions to the Flask app and create tables."""
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "admin_login"
    login_manager.login_message = "Please log in to access the admin panel."
    login_manager.login_message_category = "warning"

    with app.app_context():
        db.create_all()
        # Ensure common editable content blocks exist
        seed_content_blocks()
        # Backfill roles and ensure one superadmin exists
        _ensure_superadmin()


def _ensure_superadmin():
    """Backfill missing roles and promote the first user to superadmin if none exists."""
    users = AdminUser.query.all()
    if not users:
        return
    # Backfill any NULL roles to editor
    for user in users:
        if not user.role or user.role not in AdminUser.ROLES:
            user.role = "editor"
    if not any(u.role == "superadmin" for u in users):
        first = min(users, key=lambda u: u.created_at or datetime.utcnow())
        first.role = "superadmin"
    db.session.commit()


def seed_content_blocks():
    """Create default editable content blocks so the admin has something to edit."""
    defaults = [
        # Home page
        ("home_hero_title", "home", "Home", "Geospatial Innovation for Tanzania", "text"),
        ("home_hero_subtitle", "home", "Home", "Maps, data, and tools shaping resilient cities.", "text"),
        ("home_about_text", "home", "About Intro", "At OpenGeoCity Tanzania, we firmly believe that maps are the intelligence that shapes a better world.", "text"),
        ("home_cta_text", "home", "CTA Text", "Whether you are a student, researcher, organization, or government — join us as we plot the present, plan the future, and prospect sustainable opportunities for Tanzania.", "text"),
        # About page
        ("about_intro", "about", "About Intro", "", "html"),
        # Resources page
        ("resources_video_intro", "resources", "Video Section Intro", "Watch our tutorials, project demos, and geospatial walkthroughs on YouTube.", "text"),
        # Global / Footer
        ("footer_about", "global", "Footer About Text", "OpenGeoCity Tanzania is a premier NGO specializing in geospatial innovation and data-driven urban strategy in Dodoma.", "text"),
        ("site_contact_email", "global", "Contact Email", "info@ogctz.org", "text"),
        ("site_contact_phone", "global", "Contact Phone", "+255 700 000 000", "text"),
    ]
    for key, page, label, default, ctype in defaults:
        get_or_create_content(key, page, default, label, ctype)


def published_posts_query(limit=None, featured_first=True):
    q = BlogPost.query.filter_by(published=True)
    if featured_first:
        q = q.order_by(BlogPost.is_featured.desc(), BlogPost.published_at.desc(), BlogPost.created_at.desc())
    else:
        q = q.order_by(BlogPost.published_at.desc(), BlogPost.created_at.desc())
    if limit:
        q = q.limit(limit)
    return q
