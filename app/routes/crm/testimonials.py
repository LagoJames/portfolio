from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from flask_login import login_required

from app import db
from app.models import Project, Testimonial

crm_testimonials = Blueprint(
    "crm_testimonials",
    __name__,
    url_prefix="/admin/testimonials",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SOURCE_CHOICES = [
    ("upwork", "Upwork"),
    ("direct", "Direct"),
    ("spectra_markets", "Spectra Markets"),
    ("other", "Other"),
]

RATING_CHOICES = [1, 2, 3, 4, 5]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _populate_testimonial(testimonial: Testimonial, form: dict) -> None:
    """Copy form values onto a Testimonial instance."""
    testimonial.client_name = form.get("client_name", "").strip()
    testimonial.job_title = form.get("job_title", "").strip() or None
    testimonial.review_text = form.get("review_text", "").strip()
    testimonial.source = form.get("source", "")

    raw_rating = form.get("rating", "").strip()
    testimonial.rating = int(raw_rating) if raw_rating.isdigit() else None

    raw_project = form.get("project_id", "").strip()
    testimonial.project_id = int(raw_project) if raw_project.isdigit() else None

    testimonial.is_visible = "is_visible" in form

    raw_order = form.get("sort_order", "").strip()
    testimonial.sort_order = int(raw_order) if raw_order.isdigit() else 0


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@crm_testimonials.route("/")
@login_required
def list_testimonials():
    """List all testimonials ordered by sort_order then id."""
    testimonials = (
        Testimonial.query
        .order_by(Testimonial.sort_order.asc(), Testimonial.id.desc())
        .all()
    )
    return render_template(
        "admin/testimonials_list.html",
        testimonials=testimonials,
        source_choices=SOURCE_CHOICES,
    )


@crm_testimonials.route("/new", methods=["GET", "POST"])
@login_required
def new_testimonial():
    """Create a new testimonial."""
    if request.method == "POST":
        testimonial = Testimonial()
        _populate_testimonial(testimonial, request.form)
        db.session.add(testimonial)
        db.session.commit()
        flash(
            f'Testimonial from "{testimonial.client_name}" created successfully.',
            "success",
        )
        return redirect(url_for("crm_testimonials.list_testimonials"))

    projects = (
        Project.query
        .filter_by(is_visible=True)
        .order_by(Project.sort_order.asc(), Project.title.asc())
        .all()
    )
    return render_template(
        "admin/testimonial_form.html",
        testimonial=None,
        source_choices=SOURCE_CHOICES,
        rating_choices=RATING_CHOICES,
        projects=projects,
        form_action=url_for("crm_testimonials.new_testimonial"),
    )


@crm_testimonials.route("/<int:testimonial_id>/edit", methods=["GET", "POST"])
@login_required
def edit_testimonial(testimonial_id: int):
    """Edit an existing testimonial."""
    testimonial = Testimonial.query.get_or_404(testimonial_id)

    if request.method == "POST":
        _populate_testimonial(testimonial, request.form)
        db.session.commit()
        flash(
            f'Testimonial from "{testimonial.client_name}" updated successfully.',
            "success",
        )
        return redirect(url_for("crm_testimonials.list_testimonials"))

    projects = (
        Project.query
        .filter_by(is_visible=True)
        .order_by(Project.sort_order.asc(), Project.title.asc())
        .all()
    )
    return render_template(
        "admin/testimonial_form.html",
        testimonial=testimonial,
        source_choices=SOURCE_CHOICES,
        rating_choices=RATING_CHOICES,
        projects=projects,
        form_action=url_for(
            "crm_testimonials.edit_testimonial",
            testimonial_id=testimonial_id,
        ),
    )


@crm_testimonials.route("/<int:testimonial_id>/delete", methods=["POST"])
@login_required
def delete_testimonial(testimonial_id: int):
    """Delete a testimonial."""
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    client_name = testimonial.client_name
    db.session.delete(testimonial)
    db.session.commit()
    flash(f'Testimonial from "{client_name}" deleted.', "warning")
    return redirect(url_for("crm_testimonials.list_testimonials"))
