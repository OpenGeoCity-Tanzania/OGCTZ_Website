from datetime import datetime
import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, Response, current_app
from flask_login import current_user
from ..models import db, BlogPost, Category, Comment, Subscriber
from ..utils import extract_headings, comment_requires_moderation

blog_bp = Blueprint("blog", __name__, template_folder="../templates")


def _visible_posts_query():
    """Query posts that are publicly visible (published and schedule reached)."""
    now = datetime.utcnow()
    return BlogPost.query.filter(
        BlogPost.published == True,
        BlogPost.status == "published",
        db.or_(
            BlogPost.scheduled_at == None,
            BlogPost.scheduled_at <= now
        )
    )


@blog_bp.route("/blog")
def blog_index():
    page = request.args.get("page", 1, type=int)
    per_page = 9
    posts = _visible_posts_query()\
        .order_by(BlogPost.is_featured.desc(), BlogPost.published_at.desc(), BlogPost.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    all_categories = Category.query.order_by(Category.name).all()
    return render_template("blog/index.html", page_title="Blog", posts=posts, all_categories=all_categories)


@blog_bp.route("/blog/<slug>")
def blog_post(slug):
    post = BlogPost.query.filter_by(slug=slug).first_or_404()
    if not post.is_visible() and not (current_user.is_authenticated and current_user.can_manage_content()):
        return render_template("404.html"), 404

    # Increment view count (only for public visitors)
    if not current_user.is_authenticated:
        post.view_count = (post.view_count or 0) + 1
        db.session.commit()

    related = _visible_posts_query().filter(BlogPost.id != post.id)\
        .order_by(BlogPost.published_at.desc()).limit(3).all()
    approved_comments = Comment.query.filter_by(post_id=post.id, is_approved=True).order_by(Comment.created_at.desc()).all()
    headings = extract_headings(post.content)
    page_description = post.meta_description or post.excerpt or ""
    site_url = current_app.config.get("SITE_URL", os.environ.get("SITE_URL", "https://ogctz.org"))

    # Previous / next post navigation (by publication date)
    post_date = post.published_at or post.created_at
    prev_query = _visible_posts_query().filter(BlogPost.id != post.id)
    next_query = _visible_posts_query().filter(BlogPost.id != post.id)
    if post.published_at:
        prev_query = prev_query.filter(BlogPost.published_at < post.published_at)
        next_query = next_query.filter(BlogPost.published_at > post.published_at)
    else:
        prev_query = prev_query.filter(BlogPost.created_at < post.created_at)
        next_query = next_query.filter(BlogPost.created_at > post.created_at)
    prev_post = prev_query.order_by(BlogPost.published_at.desc(), BlogPost.created_at.desc()).first()
    next_post = next_query.order_by(BlogPost.published_at.asc(), BlogPost.created_at.asc()).first()

    return render_template(
        "blog/post.html",
        page_title=post.meta_title or post.title,
        page_description=page_description,
        post=post,
        related=related,
        comments=approved_comments,
        headings=headings,
        prev_post=prev_post,
        next_post=next_post,
        canonical_url=site_url + url_for("blog.blog_post", slug=post.slug)
    )


@blog_bp.route("/blog/tag/<tag>")
def blog_tag(tag):
    """Filter posts by tag."""
    page = request.args.get("page", 1, type=int)
    per_page = 9
    posts = _visible_posts_query().filter(BlogPost.tags.contains(tag))\
        .order_by(BlogPost.published_at.desc(), BlogPost.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    all_categories = Category.query.order_by(Category.name).all()
    return render_template("blog/index.html", page_title=f'Posts tagged "{tag}"', posts=posts, tag=tag, all_categories=all_categories)


@blog_bp.route("/blog/rss.xml")
def blog_rss():
    """RSS feed of published posts."""
    site_url = current_app.config.get("SITE_URL", os.environ.get("SITE_URL", "https://ogctz.org"))
    posts = _visible_posts_query().order_by(BlogPost.published_at.desc()).limit(20).all()
    rss = render_template("blog/rss.xml", posts=posts, site_url=site_url, now=datetime.utcnow())
    return Response(rss, mimetype="application/rss+xml")


@blog_bp.route("/blog/category/<slug>")
def blog_category(slug):
    """Filter posts by category."""
    category = Category.query.filter_by(slug=slug).first_or_404()
    page = request.args.get("page", 1, type=int)
    per_page = 9
    posts = _visible_posts_query().filter(BlogPost.category_id == category.id)\
        .order_by(BlogPost.published_at.desc(), BlogPost.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    all_categories = Category.query.order_by(Category.name).all()
    return render_template("blog/index.html", page_title=f"Category: {category.name}", posts=posts, category=category, all_categories=all_categories)


@blog_bp.route("/blog/archive/<int:year>/<int:month>")
def blog_archive(year, month):
    """Monthly archive of posts."""
    start = datetime(year, month, 1)
    end = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
    posts = _visible_posts_query().filter(
        BlogPost.published_at >= start,
        BlogPost.published_at < end
    ).order_by(BlogPost.published_at.desc()).paginate(page=1, per_page=50, error_out=False)
    return render_template("blog/archive.html", page_title=f"Archive {month:02d}/{year}", posts=posts, year=year, month=month)


@blog_bp.route("/blog/search")
def blog_search():
    """Search posts by title, excerpt, or content."""
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 9
    if q:
        like = f"%{q}%"
        posts = _visible_posts_query().filter(
            db.or_(
                BlogPost.title.ilike(like),
                BlogPost.excerpt.ilike(like),
                BlogPost.content.ilike(like)
            )
        ).order_by(BlogPost.published_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    else:
        posts = None
    return render_template("blog/search.html", page_title=f"Search: {q}" if q else "Search", posts=posts, q=q)


@blog_bp.route("/blog/<slug>/comment", methods=["POST"])
def blog_comment(slug):
    """Submit a comment on a post. Auto-approve unless flagged by moderation words."""
    post = BlogPost.query.filter_by(slug=slug).first_or_404()
    if not post.is_visible():
        return render_template("404.html"), 404
    name = request.form.get("name", "").strip().title()
    email = request.form.get("email", "").strip().lower()
    content = request.form.get("content", "").strip()
    if not name or not email or not content:
        flash("Please fill in all comment fields.", "error")
        return redirect(url_for("blog.blog_post", slug=post.slug) + "#comments")
    flagged = comment_requires_moderation(content)
    comment = Comment(
        post_id=post.id,
        author_name=name,
        email=email,
        content=content,
        is_approved=not flagged,
    )
    db.session.add(comment)
    db.session.commit()
    if flagged:
        flash("Your comment has been flagged for review and will appear after approval.", "warning")
    else:
        flash("Your comment has been published.", "success")
    return redirect(url_for("blog.blog_post", slug=post.slug) + "#comments")


@blog_bp.route("/blog/subscribe", methods=["POST"])
def blog_subscribe():
    """Subscribe to the blog newsletter."""
    email = request.form.get("email", "").strip()
    name = request.form.get("name", "").strip()
    if not email or "@" not in email:
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("blog.blog_index") + "#subscribe")
    existing = Subscriber.query.filter_by(email=email).first()
    if existing:
        flash("You are already subscribed.", "success")
    else:
        subscriber = Subscriber(email=email, name=name or None)
        db.session.add(subscriber)
        db.session.commit()
        flash("Thank you for subscribing!", "success")
    return redirect(url_for("blog.blog_index") + "#subscribe")
