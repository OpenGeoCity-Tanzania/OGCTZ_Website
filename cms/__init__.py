from .models import db, login_manager, AdminUser, BlogPost, Category, Comment, Subscriber, CMSImage, SiteContent
from .utils import (
    save_uploaded_file, make_unique_slug, slugify, allowed_file, get_or_create_content,
    get_content, published_posts_query, create_admin_user, parse_scheduled_datetime,
    extract_headings, add_heading_ids, seed_content_blocks, _ensure_superadmin
)
from .routes.admin import admin_bp
from .routes.blog import blog_bp


def init_cms(app):
    """Bind CMS extensions to the Flask app and create tables."""
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "admin.admin_login"
    login_manager.login_message = "Please log in to access the admin panel."
    login_manager.login_message_category = "warning"

    app.register_blueprint(admin_bp)
    app.register_blueprint(blog_bp)

    with app.app_context():
        db.create_all()
        # Ensure common editable content blocks exist
        seed_content_blocks()
        # Backfill roles and ensure one superadmin exists
        _ensure_superadmin()
