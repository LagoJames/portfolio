import os
import uuid
from datetime import datetime, timezone

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_required
from werkzeug.utils import secure_filename
from PIL import Image

from app import db
from app.models import BlogPost
from app.utils.helpers import slugify

crm_blog = Blueprint('crm_blog', __name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
IMAGE_MAX_WIDTH = 800
UPLOAD_SUBDIR = os.path.join('uploads', 'blog')

CATEGORY_CHOICES = [
    ('thoughts', 'Thoughts'),
    ('books', 'Books'),
    ('music', 'Music'),
    ('movies', 'Movies'),
    ('technology', 'Technology'),
    ('markets', 'Markets'),
    ('life', 'Life'),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _allowed_file(filename: str) -> bool:
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def _save_cover_image(file_obj) -> str | None:
    """Validate, resize (max 800 px wide), save and return the relative URL."""
    if file_obj is None or file_obj.filename == '':
        return None

    if not _allowed_file(file_obj.filename):
        flash('Invalid image type. Allowed: png, jpg, jpeg, gif, webp.', 'danger')
        return None

    ext = file_obj.filename.rsplit('.', 1)[1].lower()
    unique_name = f'{uuid.uuid4().hex}.{ext}'
    safe_name = secure_filename(unique_name)

    upload_dir = os.path.join(current_app.static_folder, UPLOAD_SUBDIR)
    os.makedirs(upload_dir, exist_ok=True)

    dest_path = os.path.join(upload_dir, safe_name)

    img = Image.open(file_obj)
    if img.width > IMAGE_MAX_WIDTH:
        ratio = IMAGE_MAX_WIDTH / img.width
        new_size = (IMAGE_MAX_WIDTH, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    img.save(dest_path)

    # Return a URL-friendly path relative to /static/
    return f"{UPLOAD_SUBDIR.replace(os.sep, '/')}/{safe_name}"


def _populate_post(post: BlogPost, form: dict) -> None:
    """Copy form values onto a BlogPost instance."""
    post.title = form.get('title', '').strip()

    # Use the submitted slug if provided; otherwise auto-generate from title.
    submitted_slug = form.get('slug', '').strip()
    post.slug = submitted_slug if submitted_slug else slugify(post.title)

    post.excerpt = form.get('excerpt', '').strip() or None
    post.content = form.get('content', '').strip()
    post.category = form.get('category', 'thoughts')
    post.tags = form.get('tags', '').strip() or None
    post.is_featured = 'is_featured' in form
    post.is_published = 'is_published' in form


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@crm_blog.route('/')
@login_required
def list_posts():
    """List all blog posts (published and drafts)."""
    posts = BlogPost.query.order_by(
        BlogPost.created_at.desc()
    ).all()

    return render_template(
        'admin/blog_list.html',
        posts=posts,
        category_choices=CATEGORY_CHOICES,
    )


@crm_blog.route('/new', methods=['GET', 'POST'])
@login_required
def new_post():
    """Create a new blog post."""
    if request.method == 'POST':
        post = BlogPost()
        _populate_post(post, request.form)

        # Handle cover image upload
        cover_file = request.files.get('cover_image')
        saved_url = _save_cover_image(cover_file)
        if saved_url:
            post.cover_image_url = saved_url

        # Set published_at timestamp when publishing for the first time
        if post.is_published and post.published_at is None:
            post.published_at = datetime.now(timezone.utc)

        db.session.add(post)
        db.session.commit()
        flash(f'Blog post "{post.title}" created successfully.', 'success')
        return redirect(url_for('crm_blog.list_posts'))

    return render_template(
        'admin/blog_form.html',
        post=None,
        category_choices=CATEGORY_CHOICES,
        form_action=url_for('crm_blog.new_post'),
    )


@crm_blog.route('/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id: int):
    """Edit an existing blog post."""
    post = BlogPost.query.get_or_404(post_id)

    if request.method == 'POST':
        was_published = post.is_published
        _populate_post(post, request.form)

        # Handle cover image upload
        cover_file = request.files.get('cover_image')
        saved_url = _save_cover_image(cover_file)
        if saved_url:
            post.cover_image_url = saved_url

        # Set published_at only when transitioning from draft to published
        if post.is_published and not was_published and post.published_at is None:
            post.published_at = datetime.now(timezone.utc)

        db.session.commit()
        flash(f'Blog post "{post.title}" updated successfully.', 'success')
        return redirect(url_for('crm_blog.list_posts'))

    return render_template(
        'admin/blog_form.html',
        post=post,
        category_choices=CATEGORY_CHOICES,
        form_action=url_for('crm_blog.edit_post', post_id=post_id),
    )


@crm_blog.route('/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id: int):
    """Permanently delete a blog post."""
    post = BlogPost.query.get_or_404(post_id)
    title = post.title
    db.session.delete(post)
    db.session.commit()
    flash(f'Blog post "{title}" deleted.', 'warning')
    return redirect(url_for('crm_blog.list_posts'))


@crm_blog.route('/<int:post_id>/publish', methods=['POST'])
@login_required
def toggle_publish(post_id: int):
    """Toggle the published state of a blog post.

    When publishing (draft -> published): sets is_published=True and stamps
    published_at with the current UTC time if it has not already been set.
    When unpublishing: sets is_published=False (published_at is preserved so
    re-publishing keeps the original date unless it is cleared manually).
    """
    post = BlogPost.query.get_or_404(post_id)

    if post.is_published:
        # Unpublish
        post.is_published = False
        flash(f'"{post.title}" unpublished (moved to drafts).', 'info')
    else:
        # Publish
        post.is_published = True
        if post.published_at is None:
            post.published_at = datetime.now(timezone.utc)
        flash(f'"{post.title}" published successfully.', 'success')

    db.session.commit()
    return redirect(url_for('crm_blog.list_posts'))
