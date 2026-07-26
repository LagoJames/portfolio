from flask import Blueprint, render_template
from flask_login import login_required
from app import db
from app.models import (
    AdminUser, Project, Testimonial, Notebook,
    ContactSubmission, HireRequest, ActiveProject, Setting
)

crm_dashboard = Blueprint('crm_dashboard', __name__, template_folder='../../../templates')


@crm_dashboard.route('/')
@login_required
def dashboard():
    # Projects stats
    total_projects = db.session.query(Project).count()
    visible_projects = db.session.query(Project).filter_by(is_visible=True).count()
    hidden_projects = db.session.query(Project).filter_by(is_visible=False).count()

    # Testimonials count
    total_testimonials = db.session.query(Testimonial).count()

    # Notebooks count
    total_notebooks = db.session.query(Notebook).count()

    # Unread contacts count
    unread_contacts = db.session.query(ContactSubmission).filter_by(is_read=False).count()

    # Recent 5 contact submissions (newest first)
    recent_contacts = (
        db.session.query(ContactSubmission)
        .order_by(ContactSubmission.created_at.desc())
        .limit(5)
        .all()
    )

    # Pending hire requests count
    pending_hire_requests = db.session.query(HireRequest).filter_by(status='pending').count()

    # Active projects currently in progress
    active_projects = (
        db.session.query(ActiveProject)
        .filter_by(status='in_progress')
        .order_by(ActiveProject.created_at.desc())
        .all()
    )

    from app.models import ClientReview
    pending_reviews = db.session.query(ClientReview).filter_by(is_approved=False).count()
    active_count = len(active_projects)

    stats = {
        'total_projects': total_projects,
        'visible_projects': visible_projects,
        'hidden_projects': hidden_projects,
        'total_testimonials': total_testimonials,
        'total_notebooks': total_notebooks,
        'unread_contacts': unread_contacts,
        'pending_hire_requests': pending_hire_requests,
        'active_projects': active_count,
        'pending_reviews': pending_reviews,
    }

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_contacts=recent_contacts,
        active_projects=active_projects,
    )
