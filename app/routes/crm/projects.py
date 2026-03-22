import os
import uuid

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    current_app,
)
from flask_login import login_required
from werkzeug.utils import secure_filename
from PIL import Image

from app import db
from app.models import Project
from app.utils.helpers import slugify

crm_projects = Blueprint(
    "crm_projects",
    __name__,
    url_prefix="/admin/projects",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
IMAGE_MAX_WIDTH = 800
UPLOAD_SUBDIR = os.path.join("uploads", "projects")

CATEGORY_CHOICES = [
    ("financial_engineering", "Financial Engineering"),
    ("machine_learning", "Machine Learning"),
    ("trading_quant", "Trading / Quant"),
    ("statistical_analysis", "Statistical Analysis"),
    ("research", "Research"),
    ("personal", "Personal"),
]

SOURCE_CHOICES = [
    ("upwork", "Upwork"),
    ("quant_hedge", "Quant / Hedge"),
    ("personal", "Personal"),
    ("academic", "Academic"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def _save_cover_image(file_obj) -> str | None:
    """Validate, resize (max 800 px wide), save and return the relative URL."""
    if file_obj is None or file_obj.filename == "":
        return None

    if not _allowed_file(file_obj.filename):
        flash("Invalid image type. Allowed: png, jpg, jpeg, gif, webp.", "danger")
        return None

    ext = file_obj.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
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


def _populate_project(project: Project, form: dict) -> None:
    """Copy form values onto a Project instance."""
    project.title = form.get("title", "").strip()
    project.slug = form.get("slug", "").strip() or slugify(project.title)
    project.category = form.get("category", "")
    project.source = form.get("source", "")
    project.short_description = form.get("short_description", "").strip()
    project.full_description = form.get("full_description", "").strip()
    project.tools_used = form.get("tools_used", "").strip()
    project.github_url = form.get("github_url", "").strip() or None
    project.colab_url = form.get("colab_url", "").strip() or None
    project.substack_url = form.get("substack_url", "").strip() or None
    project.paper_url = form.get("paper_url", "").strip() or None
    project.upwork_url = form.get("upwork_url", "").strip() or None

    raw_rating = form.get("upwork_rating", "").strip()
    project.upwork_rating = float(raw_rating) if raw_rating else None

    project.is_featured = "is_featured" in form
    project.is_visible = "is_visible" in form

    raw_order = form.get("sort_order", "").strip()
    project.sort_order = int(raw_order) if raw_order.isdigit() else 0


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@crm_projects.route("/")
@login_required
def list_projects():
    """List all projects with optional category filter and title search."""
    category = request.args.get("category", "").strip()
    search = request.args.get("search", "").strip()

    query = Project.query

    if category:
        query = query.filter(Project.category == category)

    if search:
        query = query.filter(Project.title.ilike(f"%{search}%"))

    projects = query.order_by(Project.sort_order.asc(), Project.id.desc()).all()

    return render_template(
        "admin/projects_list.html",
        projects=projects,
        category_choices=CATEGORY_CHOICES,
        current_category=category,
        current_search=search,
    )


@crm_projects.route("/new", methods=["GET", "POST"])
@login_required
def new_project():
    """Create a new project."""
    if request.method == "POST":
        project = Project()
        _populate_project(project, request.form)

        cover_file = request.files.get("cover_image")
        saved_url = _save_cover_image(cover_file)
        if saved_url:
            project.cover_image_url = saved_url

        db.session.add(project)
        db.session.commit()
        flash(f'Project "{project.title}" created successfully.', "success")
        return redirect(url_for("crm_projects.list_projects"))

    # Pre-populate slug via JS on the frontend; pass an empty dict as form data.
    return render_template(
        "admin/project_form.html",
        project=None,
        category_choices=CATEGORY_CHOICES,
        source_choices=SOURCE_CHOICES,
        form_action=url_for("crm_projects.new_project"),
    )


@crm_projects.route("/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def edit_project(project_id: int):
    """Edit an existing project."""
    project = Project.query.get_or_404(project_id)

    if request.method == "POST":
        _populate_project(project, request.form)

        cover_file = request.files.get("cover_image")
        saved_url = _save_cover_image(cover_file)
        if saved_url:
            project.cover_image_url = saved_url

        db.session.commit()
        flash(f'Project "{project.title}" updated successfully.', "success")
        return redirect(url_for("crm_projects.list_projects"))

    return render_template(
        "admin/project_form.html",
        project=project,
        category_choices=CATEGORY_CHOICES,
        source_choices=SOURCE_CHOICES,
        form_action=url_for("crm_projects.edit_project", project_id=project_id),
    )


@crm_projects.route("/<int:project_id>/delete", methods=["POST"])
@login_required
def delete_project(project_id: int):
    """Delete a project."""
    project = Project.query.get_or_404(project_id)
    title = project.title
    db.session.delete(project)
    db.session.commit()
    flash(f'Project "{title}" deleted.', "warning")
    return redirect(url_for("crm_projects.list_projects"))


@crm_projects.route("/<int:project_id>/toggle-featured", methods=["POST"])
@login_required
def toggle_featured(project_id: int):
    """Toggle the is_featured flag via AJAX. Returns JSON."""
    project = Project.query.get_or_404(project_id)
    project.is_featured = not project.is_featured
    db.session.commit()
    return jsonify(
        {
            "success": True,
            "is_featured": project.is_featured,
            "project_id": project_id,
        }
    )


@crm_projects.route("/<int:project_id>/toggle-visible", methods=["POST"])
@login_required
def toggle_visible(project_id: int):
    """Toggle the is_visible flag via AJAX. Returns JSON."""
    project = Project.query.get_or_404(project_id)
    project.is_visible = not project.is_visible
    db.session.commit()
    return jsonify(
        {
            "success": True,
            "is_visible": project.is_visible,
            "project_id": project_id,
        }
    )
