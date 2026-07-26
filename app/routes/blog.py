from flask import Blueprint, render_template, request, abort

from app import db
from app.models import BlogPost
from app.utils.helpers import render_markdown

blog = Blueprint('blog', __name__)

VALID_CATEGORIES = {
    'thoughts', 'books', 'music', 'movies', 'technology', 'markets', 'life'
}


@blog.route('/blog')
def blog_list():
    """List all published blog posts, optionally filtered by category."""
    category = request.args.get('category', '').strip().lower()

    query = BlogPost.query.filter_by(is_published=True)

    if category and category in VALID_CATEGORIES:
        query = query.filter(BlogPost.category == category)

    posts = query.order_by(BlogPost.published_at.desc(), BlogPost.created_at.desc()).all()

    return render_template(
        'public/blog.html',
        posts=posts,
        categories=sorted(VALID_CATEGORIES),
        current_category=category,
    )


@blog.route('/blog/<slug>')
def blog_detail(slug):
    """Display a single published blog post, rendering its content from markdown."""
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()

    content_html = render_markdown(post.content)

    return render_template(
        'public/blog_detail.html',
        post=post,
        content_html=content_html,
    )
