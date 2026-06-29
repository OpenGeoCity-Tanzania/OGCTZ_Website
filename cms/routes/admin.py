import os
import uuid
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, login_user, logout_user, current_user
from ..models import db, AdminUser, BlogPost, Category, Comment, Subscriber, CMSImage, SiteContent
from ..utils import (
    save_uploaded_file, make_unique_slug, slugify, get_or_create_content, create_admin_user,
    parse_scheduled_datetime, seed_content_blocks, _ensure_superadmin, minio_configured,
    upload_to_minio, delete_from_minio, minio_object_name_from_url
)

admin_bp = Blueprint("admin", __name__, template_folder="../templates")


# ── Role-based Access Helpers ────────────────────────────────────────────────

def superadmin_required(f):
    """Decorator restricting a route to superadmin users."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_superadmin():
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for("admin.admin_dashboard"))
        return f(*args, **kwargs)
    return decorated_function


# ── Admin Authentication ─────────────────────────────────────────────────────

@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("admin.admin_dashboard"))
        flash("Invalid username or password.", "error")

    return render_template("admin/login.html", page_title="Admin Login")


@admin_bp.route("/admin/logout")
@login_required
def admin_logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("admin.admin_login"))


# ── Admin Dashboard ────────────────────────────────────────────────────────────

@admin_bp.route("/admin")
@admin_bp.route("/admin/dashboard")
@login_required
def admin_dashboard():
    stats = {
        "posts": BlogPost.query.count(),
        "published": BlogPost.query.filter_by(published=True).count(),
        "images": CMSImage.query.count(),
        "content": SiteContent.query.count(),
    }
    recent_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html", page_title="Admin Dashboard", stats=stats, recent_posts=recent_posts)


# ── Admin Blog Posts CRUD ─────────────────────────────────────────────────────

def _apply_post_form(post, form, is_new=False):
    """Populate a BlogPost from form data and return a tuple (success, error_message)."""
    title = form.get("title", "").strip()
    content = form.get("content", "").strip()
    slug = form.get("slug", "").strip()
    excerpt = form.get("excerpt", "").strip()
    author = form.get("author", "").strip()
    tags = form.get("tags", "").strip()
    meta_title = form.get("meta_title", "").strip()
    meta_description = form.get("meta_description", "").strip()
    status = form.get("status", "draft")
    featured = bool(form.get("featured"))
    scheduled_at = parse_scheduled_datetime(form.get("scheduled_at", "").strip())
    category_id = form.get("category_id", "").strip()

    if not title or not content:
        return False, "Title and content are required."
    if status not in ("draft", "published", "scheduled"):
        status = "draft"

    # Determine slug
    if not slug:
        slug = make_unique_slug(title, existing_id=None if is_new else post.id)
    else:
        slug = slugify(slug)
        if is_new:
            slug = make_unique_slug(slug)
        else:
            existing = BlogPost.query.filter(BlogPost.slug == slug, BlogPost.id != post.id).first()
            if existing:
                slug = make_unique_slug(slug, existing_id=post.id)

    post.title = title
    post.slug = slug
    post.content = content
    post.excerpt = excerpt or None
    post.author = author or None
    post.tags = tags or None
    post.meta_title = meta_title or None
    post.meta_description = meta_description or None
    post.is_featured = featured
    post.scheduled_at = scheduled_at
    if category_id:
        cat = Category.query.get(int(category_id))
        post.category_id = cat.id if cat else None
    else:
        post.category_id = None

    # Handle status transitions
    was_published = post.published
    post.status = status
    if status == "published":
        post.published = True
        if not was_published or not post.published_at:
            post.published_at = datetime.utcnow()
    elif status == "scheduled":
        post.published = True
        if not post.published_at:
            post.published_at = datetime.utcnow()
    else:  # draft
        post.published = False

    # Featured image upload
    if "featured_image" in request.files:
        file = request.files["featured_image"]
        if file and file.filename:
            if minio_configured():
                minio_url = upload_to_minio(file, folder="blog")
                if minio_url:
                    post.featured_image = minio_url
                else:
                    flash("Featured image upload to MinIO failed. Please check MinIO settings.", "error")
                    return False, "MinIO upload failed"
            else:
                filename = save_uploaded_file(file, folder="blog")
                if filename:
                    post.featured_image = f"/static/uploads/blog/{filename}"

    return True, None


@admin_bp.route("/admin/posts")
@login_required
def admin_posts():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template("admin/posts.html", page_title="Manage Posts", posts=posts)


@admin_bp.route("/admin/posts/new", methods=["GET", "POST"])
@login_required
def admin_post_new():
    if request.method == "POST":
        post = BlogPost()
        ok, err = _apply_post_form(post, request.form, is_new=True)
        if not ok:
            flash(err, "error")
            categories = Category.query.order_by(Category.name).all()
            return render_template("admin/post_form.html", page_title="New Post", post=None, categories=categories)
        db.session.add(post)
        db.session.commit()
        flash("Post created successfully.", "success")
        return redirect(url_for("admin.admin_posts"))

    categories = Category.query.order_by(Category.name).all()
    return render_template("admin/post_form.html", page_title="New Post", post=None, categories=categories)


@admin_bp.route("/admin/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def admin_post_edit(post_id):
    post = BlogPost.query.get_or_404(post_id)
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        ok, err = _apply_post_form(post, request.form, is_new=False)
        if not ok:
            flash(err, "error")
            return render_template("admin/post_form.html", page_title="Edit Post", post=post, categories=categories)
        db.session.commit()
        flash("Post updated successfully.", "success")
        return redirect(url_for("admin.admin_posts"))

    return render_template("admin/post_form.html", page_title="Edit Post", post=post, categories=categories)


@admin_bp.route("/admin/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def admin_post_delete(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "success")
    return redirect(url_for("admin.admin_posts"))


# ── Admin Image Manager ───────────────────────────────────────────────────────

@admin_bp.route("/admin/images")
@login_required
def admin_images():
    folder = request.args.get("folder", "general")
    images = CMSImage.query.order_by(CMSImage.created_at.desc()).all()
    return render_template("admin/images.html", page_title="Image Library", images=images, folder=folder)


@admin_bp.route("/admin/images/upload", methods=["POST"])
@login_required
def admin_image_upload():
    folder = request.form.get("folder", "general").strip()
    if "file" not in request.files:
        flash("No file selected.", "error")
        return redirect(url_for("admin.admin_images", folder=folder))
    file = request.files["file"]
    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("admin.admin_images", folder=folder))

    original = secure_filename(file.filename)
    if minio_configured():
        # Capture size before upload consumes the file stream
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        minio_url = upload_to_minio(file, folder=folder)
        if minio_url:
            new_filename = original.rsplit(".", 1)[0].lower().replace(" ", "-") if "." in original else "image"
            ext = original.rsplit(".", 1)[-1].lower() if "." in original else "jpg"
            new_filename = f"{new_filename[:60]}-{uuid.uuid4().hex[:8]}.{ext}"
            image = CMSImage(
                filename=new_filename,
                original_filename=original,
                alt_text=request.form.get("alt_text", "").strip() or None,
                folder=folder,
                minio_url=minio_url,
                file_size=file_size
            )
            db.session.add(image)
            db.session.commit()
            flash("Image uploaded to MinIO successfully.", "success")
        else:
            flash("MinIO upload failed. Please check your MinIO settings.", "error")
    else:
        filename = save_uploaded_file(file, folder=folder)
        if filename:
            image = CMSImage(
                filename=filename,
                original_filename=original,
                alt_text=request.form.get("alt_text", "").strip() or None,
                folder=folder,
                file_size=os.path.getsize(os.path.join(current_app.root_path, "static", "uploads", folder, filename))
            )
            db.session.add(image)
            db.session.commit()
            flash("Image uploaded successfully.", "success")
        else:
            flash("Invalid file. Allowed types: PNG, JPG, GIF, WEBP, SVG.", "error")
    return redirect(url_for("admin.admin_images", folder=folder))


@admin_bp.route("/admin/images/<int:image_id>/delete", methods=["POST"])
@login_required
def admin_image_delete(image_id):
    image = CMSImage.query.get_or_404(image_id)
    if image.minio_url:
        bucket, object_name = minio_object_name_from_url(image.minio_url)
        if object_name:
            delete_from_minio(object_name, bucket)
    else:
        full_path = os.path.join(current_app.root_path, image.filepath)
        if os.path.exists(full_path):
            os.remove(full_path)
    db.session.delete(image)
    db.session.commit()
    flash("Image deleted.", "success")
    return redirect(url_for("admin.admin_images"))


# ── Admin Editable Content Blocks ─────────────────────────────────────────────

@admin_bp.route("/admin/content")
@login_required
def admin_content():
    page_filter = request.args.get("page", "all")
    if page_filter == "all":
        items = SiteContent.query.order_by(SiteContent.page, SiteContent.key).all()
    else:
        items = SiteContent.query.filter_by(page=page_filter).order_by(SiteContent.key).all()
    pages = [r[0] for r in db.session.query(SiteContent.page).distinct().order_by(SiteContent.page)]
    return render_template("admin/content.html", page_title="Manage Content", items=items, pages=pages, page_filter=page_filter)


@admin_bp.route("/admin/content/<int:content_id>/edit", methods=["GET", "POST"])
@login_required
def admin_content_edit(content_id):
    item = SiteContent.query.get_or_404(content_id)
    if request.method == "POST":
        item.content = request.form.get("content", "")
        item.content_type = request.form.get("content_type", "text")
        db.session.commit()
        flash("Content block updated.", "success")
        return redirect(url_for("admin.admin_content", page=item.page))
    return render_template("admin/content_form.html", page_title="Edit Content", item=item)


# ── User Management (superadmin only) ───────────────────────────────────────────

@admin_bp.route("/admin/users")
@superadmin_required
def admin_users():
    users = AdminUser.query.order_by(AdminUser.created_at.desc()).all()
    return render_template("admin/users.html", page_title="Manage Users", users=users)


@admin_bp.route("/admin/users/new", methods=["GET", "POST"])
@superadmin_required
def admin_user_new():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip() or None
        role = request.form.get("role", "editor")
        if not username or not password or len(password) < 6:
            flash("Username and password (min 6 chars) required.", "error")
            return render_template("admin/user_form.html", page_title="New User", user=None)
        if role not in AdminUser.ROLES:
            role = "editor"
        if create_admin_user(username, password, email, role=role):
            flash(f"User '{username}' created with role {role}.", "success")
            return redirect(url_for("admin.admin_users"))
        flash("Username or email already exists.", "error")
    return render_template("admin/user_form.html", page_title="New User", user=None)


@admin_bp.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@superadmin_required
def admin_user_edit(user_id):
    user = AdminUser.query.get_or_404(user_id)
    # Prevent editing/deleting the last superadmin
    if user.is_superadmin() and AdminUser.query.filter_by(role="superadmin").count() <= 1:
        is_last_superadmin = True
    else:
        is_last_superadmin = False

    if request.method == "POST":
        email = request.form.get("email", "").strip() or None
        role = request.form.get("role", user.role)
        is_active = request.form.get("is_active") == "on"
        new_password = request.form.get("password", "")

        if role not in AdminUser.ROLES:
            role = user.role
        if is_last_superadmin and role != "superadmin":
            flash("Cannot demote the last superadmin.", "error")
            return render_template("admin/user_form.html", page_title="Edit User", user=user)
        if is_last_superadmin and not is_active:
            flash("Cannot deactivate the last superadmin.", "error")
            return render_template("admin/user_form.html", page_title="Edit User", user=user)

        user.email = email
        user.role = role
        user.is_active = is_active
        if new_password:
            if len(new_password) < 6:
                flash("Password must be at least 6 characters.", "error")
                return render_template("admin/user_form.html", page_title="Edit User", user=user)
            user.set_password(new_password)
        db.session.commit()
        flash("User updated.", "success")
        return redirect(url_for("admin.admin_users"))

    return render_template("admin/user_form.html", page_title="Edit User", user=user)


@admin_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@superadmin_required
def admin_user_delete(user_id):
    user = AdminUser.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "error")
        return redirect(url_for("admin.admin_users"))
    if user.is_superadmin() and AdminUser.query.filter_by(role="superadmin").count() <= 1:
        flash("Cannot delete the last superadmin.", "error")
        return redirect(url_for("admin.admin_users"))
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "success")
    return redirect(url_for("admin.admin_users"))


# ── Admin Categories ──────────────────────────────────────────────────────────

@admin_bp.route("/admin/categories")
@login_required
def admin_categories():
    categories = Category.query.order_by(Category.name).all()
    return render_template("admin/categories.html", page_title="Categories", categories=categories)


@admin_bp.route("/admin/categories/new", methods=["POST"])
@login_required
def admin_category_new():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    if not name:
        flash("Category name is required.", "error")
        return redirect(url_for("admin.admin_categories"))
    slug = make_unique_slug(name)
    if Category.query.filter_by(slug=slug).first():
        flash("Category already exists.", "error")
        return redirect(url_for("admin.admin_categories"))
    cat = Category(name=name, slug=slug, description=description or None)
    db.session.add(cat)
    db.session.commit()
    flash("Category created.", "success")
    return redirect(url_for("admin.admin_categories"))


@admin_bp.route("/admin/categories/<int:cat_id>/delete", methods=["POST"])
@login_required
def admin_category_delete(cat_id):
    cat = Category.query.get_or_404(cat_id)
    BlogPost.query.filter_by(category_id=cat.id).update({"category_id": None})
    db.session.delete(cat)
    db.session.commit()
    flash("Category deleted.", "success")
    return redirect(url_for("admin.admin_categories"))


# ── Admin Comments ─────────────────────────────────────────────────────────────

@admin_bp.route("/admin/comments")
@login_required
def admin_comments():
    status = request.args.get("status", "pending")
    if status == "approved":
        comments = Comment.query.filter_by(is_approved=True).order_by(Comment.created_at.desc()).all()
    elif status == "pending":
        comments = Comment.query.filter_by(is_approved=False).order_by(Comment.created_at.desc()).all()
    else:
        comments = Comment.query.order_by(Comment.created_at.desc()).all()
    return render_template("admin/comments.html", page_title="Comments", comments=comments, status=status)


@admin_bp.route("/admin/comments/<int:comment_id>/approve", methods=["POST"])
@login_required
def admin_comment_approve(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.is_approved = True
    db.session.commit()
    flash("Comment approved.", "success")
    return redirect(url_for("admin.admin_comments", status="pending"))


@admin_bp.route("/admin/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def admin_comment_delete(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted.", "success")
    return redirect(url_for("admin.admin_comments"))


# ── Admin Subscribers ──────────────────────────────────────────────────────────

@admin_bp.route("/admin/subscribers")
@login_required
def admin_subscribers():
    subscribers = Subscriber.query.order_by(Subscriber.created_at.desc()).all()
    return render_template("admin/subscribers.html", page_title="Subscribers", subscribers=subscribers)


@admin_bp.route("/admin/subscribers/<int:sub_id>/delete", methods=["POST"])
@login_required
def admin_subscriber_delete(sub_id):
    sub = Subscriber.query.get_or_404(sub_id)
    db.session.delete(sub)
    db.session.commit()
    flash("Subscriber removed.", "success")
    return redirect(url_for("admin.admin_subscribers"))


# ── Admin Setup (one-time) ───────────────────────────────────────────────────

@admin_bp.route("/admin/setup", methods=["GET", "POST"])
def admin_setup():
    if AdminUser.query.first():
        flash("Admin user already exists. Please log in.", "warning")
        return redirect(url_for("admin.admin_login"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip() or None
        if not username or not password or len(password) < 6:
            flash("Username and password (min 6 chars) required.", "error")
            return render_template("admin/setup.html", page_title="Admin Setup")
        if create_admin_user(username, password, email, role="superadmin"):
            flash("Superadmin account created. Please log in.", "success")
            return redirect(url_for("admin.admin_login"))
        flash("Could not create admin user.", "error")

    return render_template("admin/setup.html", page_title="Admin Setup")
