from datetime import datetime
import os
import re
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from .models import db, AdminUser, BlogPost, SiteContent

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}


def minio_configured():
    """Return True when all required MinIO environment variables are set."""
    return all(
        os.environ.get(k)
        for k in ("MINIO_ENDPOINT", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY", "MINIO_BUCKET")
    )


def get_minio_client():
    """Return a configured MinIO client, or None if not configured."""
    if not minio_configured():
        return None
    try:
        from minio import Minio
    except ImportError:
        return None

    endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.environ.get("MINIO_ACCESS_KEY")
    secret_key = os.environ.get("MINIO_SECRET_KEY")
    secure = os.environ.get("MINIO_SECURE", "true").lower() in ("true", "1", "yes")
    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


def minio_public_url(object_name, bucket=None):
    """Build a public URL for a MinIO object using the configured bucket."""
    bucket = bucket or os.environ.get("MINIO_BUCKET", "ogctz")
    endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    secure = os.environ.get("MINIO_SECURE", "true").lower() in ("true", "1", "yes")
    scheme = "https" if secure else "http"
    # MinIO public URLs typically look like: https://endpoint/bucket/object-name
    return f"{scheme}://{endpoint}/{bucket}/{object_name}"


def upload_to_minio(file, folder="general", filename=None):
    """Upload a file to MinIO and return its public URL. Returns None on failure."""
    if not file or not allowed_file(file.filename):
        return None

    client = get_minio_client()
    if not client:
        return None

    bucket = os.environ.get("MINIO_BUCKET", "ogctz")
    original = secure_filename(file.filename)
    new_filename = filename or unique_filename(original)
    object_name = f"{folder}/{new_filename}" if folder else new_filename

    try:
        # Ensure bucket exists
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
        # Upload file content
        file_length = os.fstat(file.fileno()).st_size
        file.seek(0)
        client.put_object(bucket, object_name, file, file_length, content_type=file.content_type or "application/octet-stream")
        return minio_public_url(object_name, bucket)
    except Exception as e:
        current_app.logger.error(f"MinIO upload failed: {e}")
        return None


def delete_from_minio(object_name, bucket=None):
    """Delete an object from MinIO. Returns True on success."""
    client = get_minio_client()
    if not client:
        return False
    bucket = bucket or os.environ.get("MINIO_BUCKET", "ogctz")
    try:
        client.remove_object(bucket, object_name)
        return True
    except Exception as e:
        current_app.logger.error(f"MinIO delete failed: {e}")
        return False


def minio_object_name_from_url(url):
    """Extract bucket/object-name from a MinIO public URL."""
    if not url:
        return None, None
    bucket = os.environ.get("MINIO_BUCKET", "ogctz")
    endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    prefix = f"{endpoint}/{bucket}/"
    if prefix in url:
        return bucket, url.split(prefix, 1)[-1]
    return None, None


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


def extract_headings(html_content):
    """Extract h2/h3 headings from HTML for a table of contents.
    Returns list of dicts with id, level, text.
    """
    if not html_content:
        return []
    headings = []
    pattern = re.compile(r"<h([23])[^>]*>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)
    for match in pattern.finditer(html_content):
        level = int(match.group(1))
        text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        if text:
            anchor = slugify(text)
            headings.append({"level": level, "text": text, "anchor": anchor})
    return headings


def add_heading_ids(html_content):
    """Add id attributes to h2/h3 headings so TOC can link to them."""
    if not html_content:
        return html_content
    seen = set()

    def replace_heading(match):
        level = match.group(1)
        attrs = match.group(2)
        inner = match.group(3)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        anchor = slugify(text)
        # Ensure uniqueness
        original = anchor
        counter = 1
        while anchor in seen:
            anchor = f"{original}-{counter}"
            counter += 1
        seen.add(anchor)
        # Inject id into existing attributes or add new
        if 'id="' in attrs or "id='" in attrs:
            attrs = re.sub(r'id=["\'][^"\']*["\']', f'id="{anchor}"', attrs)
        else:
            attrs = f'{attrs} id="{anchor}"'.strip()
        return f"<h{level} {attrs}>{inner}</h{level}>"

    pattern = re.compile(r"<h([23])([^>]*)>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)
    return pattern.sub(replace_heading, html_content)


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


def published_posts_query(limit=None, featured_first=True):
    q = BlogPost.query.filter_by(published=True)
    if featured_first:
        q = q.order_by(BlogPost.is_featured.desc(), BlogPost.published_at.desc(), BlogPost.created_at.desc())
    else:
        q = q.order_by(BlogPost.published_at.desc(), BlogPost.created_at.desc())
    if limit:
        q = q.limit(limit)
    return q


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
