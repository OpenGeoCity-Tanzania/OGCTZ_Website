from datetime import datetime
import os
import re
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()


# ── User loader ─────────────────────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))


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


class Category(db.Model):
    __tablename__ = "blog_categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Category {self.slug}>"


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
    view_count = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey("blog_categories.id"), nullable=True)
    category = db.relationship("Category", backref="posts")
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


class Comment(db.Model):
    __tablename__ = "blog_comments"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"), nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    post = db.relationship("BlogPost", backref="comments")

    def __repr__(self):
        return f"<Comment {self.id} on post {self.post_id}>"


class Subscriber(db.Model):
    __tablename__ = "blog_subscribers"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Subscriber {self.email}>"


class CMSImage(db.Model):
    __tablename__ = "cms_images"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    original_filename = db.Column(db.String(300), nullable=False)
    alt_text = db.Column(db.String(300), nullable=True)
    folder = db.Column(db.String(100), default="general")
    file_size = db.Column(db.Integer, nullable=True)
    minio_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def url(self):
        return self.minio_url or f"/static/uploads/{self.folder}/{self.filename}"

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
