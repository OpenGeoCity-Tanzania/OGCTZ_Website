# CMS Setup Guide

The OpenGeoCity Tanzania website now includes a built-in Content Management System (CMS) for managing blog posts, images, and editable page content without changing code.

## Environment Variables

Add these to your `.env` file if they are not already present:

```env
SECRET_KEY=your-very-long-random-secret-key
DATABASE_URL=sqlite:///data/opengeocity.db
# Or use any PostgreSQL/MySQL URI supported by SQLAlchemy
```

`SECRET_KEY` is required for secure sessions and login.

## First-Time Admin Setup

1. Start the application.
2. Visit `/admin/setup` in your browser.
3. Create the first admin account.
4. The setup page will be disabled automatically once an admin exists.

## Admin Dashboard

After setup, sign in at `/admin/login` to access the dashboard.

Available sections:

- **Blog Posts** — Create, edit, publish, unpublish, and delete articles.
- **Images** — Upload images and copy their URLs for use in posts or pages.
- **Site Content** — Edit text/HTML content blocks for specific pages.
- **Manage Users** *(superadmin only)* — Create, edit, and delete other admin users.

## Roles

There are three built-in roles:

- **Superadmin** — Full access; can manage users, content, posts, and images.
- **Admin** — Can manage blog posts, images, and site content.
- **Editor** — Can manage blog posts, images, and site content.

The first account created via `/admin/setup` becomes a **superadmin**. Only superadmins can add or remove other admin users.

## Public Blog

Published blog posts are visible at `/blog`. The navigation menu and footer both link to the blog automatically.

Blog features inspired by leading platforms:

- **Rich text editor** — TinyMCE-based WYSIWYG editor for formatting, links, lists, images, and code.
- **Editable URL slug** — Control the post URL (`/blog/your-slug`). Auto-generated from the title if left blank.
- **SEO meta fields** — Set custom `<meta name="description">`, OpenGraph title, and description per post; canonical URLs.
- **Categories** — WordPress-style taxonomy for broad topic organization. Public category pages at `/blog/category/<slug>`.
- **Tags** — Assign comma-separated tags to posts. Public tag pages at `/blog/tag/<tag>`.
- **Featured posts** — Mark posts as featured to highlight them at the top of the listing.
- **Publishing status** — Draft, Published, or Scheduled. Scheduled posts go live automatically at the chosen UTC time.
- **RSS feed** — `/blog/rss.xml` syndicates the latest 20 published posts.
- **Social sharing** — Twitter and LinkedIn share buttons on every post.
- **Related posts** — Automatically shows related published posts at the bottom of an article.
- **Search** — `/blog/search?q=...` searches titles, excerpts, and content.
- **Monthly archive** — `/blog/archive/<year>/<month>` lists posts published in that month.
- **Comments** — WordPress-style moderated comments. Readers submit; admins approve before display.
- **Newsletter subscriptions** — `/blog/subscribe` collects subscriber emails; managed in the admin panel.
- **Table of contents** — Auto-generated from `h2`/`h3` headings in the post body.
- **Reading progress bar** — Visual progress indicator as readers scroll.
- **View counter** — Tracks public post views (excludes logged-in admins).
- **Author profile** — Author name and avatar displayed at the end of each post.

## Page Content Blocks

The following content keys are available by default in the admin panel:

- `home_hero_title` / `home_hero_subtitle` — Home page hero text
- `about_intro` — About page introduction
- `services_intro` — Services page introduction
- `contact_intro` — Contact page introduction
- `footer_about` — Footer about paragraph

Templates use the `get_content()` helper through the `cms_content()` context processor. Example:

```html
{{ cms_content('home', 'hero_title') }}
```

## Image Uploads

Uploaded images are stored in `static/uploads/<folder>/`. In Docker deployments, the `static/uploads` folder is mounted as a volume so uploads persist between restarts.

## Deployment Notes

- The SQLite database is stored in `data/opengeocity.db` by default.
- In Docker Compose, `data/` and `static/uploads/` are mounted as persistent volumes.
- The `.gitignore` file excludes `data/` and uploaded files, but tracks the upload folder structure via `.gitkeep`.

## Database Migrations

The CMS tables are created automatically on startup. If you need to reset, delete the database file and restart the application.
